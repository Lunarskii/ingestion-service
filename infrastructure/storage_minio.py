from io import BytesIO

from minio import Minio
from minio.credentials.providers import Provider
from minio.deleteobjects import DeleteObject
from minio.error import S3Error
import urllib3

from services import RawStorage
from utils.file import get_mime_type


class MinIORawStorage(RawStorage):
    """
    Реализация интерфейса :class:`RawStorage` на базе MinIO/S3-совместимого хранилища.
    """

    def __init__(
        self,
        endpoint: str,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        session_token: str | None = None,
        secure: bool = False,
        region: str | None = None,
        http_client: urllib3.PoolManager | None = None,
        credentials: Provider | None = None,
        cert_check: bool = True,
    ):
        """
        Инициализация MinIO-хранилища.

        При инициализации создаёт MinIO-клиент и проверяет существование указанного
        бакета; при отсутствии — пытается создать его.

        :param endpoint: URL/хост MinIO-сервера (может включать порт), например ``localhost:9000``.
        :type endpoint: str
        :param bucket_name: Имя бакета, где будут храниться объекты.
        :type bucket_name: str
        :param access_key: Access key для аутентификации (логин).
        :type access_key: str
        :param secret_key: Secret key для аутентификации (пароль).
        :type secret_key: str
        :param session_token: Session token для временных учётных данных.
        :type session_token: str | None
        :param secure: Использовать HTTPS при соединении (True) или HTTP (False).
        :type secure: bool
        :param region: Регион бакета.
        :type region: str | None
        :param http_client: Кастомный urllib3.PoolManager для клиента.
        :type http_client: urllib3.PoolManager | None
        :param credentials: Поставщик учётных данных (Provider).
        :type credentials: Provider | None
        :param cert_check: Флаг проверки TLS-сертификата сервера.
        :type cert_check: bool
        """

        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token,
            secure=secure,
            region=region,
            http_client=http_client,
            credentials=credentials,
            cert_check=cert_check,
        )

        # TODO поправить проблему создания бакета при запуске в нескольких процессах
        self.bucket_name = bucket_name
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.lstrip("/")

    def save(self, file_bytes: bytes, path: str) -> None:
        """
        Сохраняет бинарные данные в MinIO как объект по указанному пути.

        :param file_bytes: Содержимое файла в виде байтов.
        :type file_bytes: bytes
        :param path: Путь/ключ объекта внутри бакета. Ведущие слэши будут отброшены.
        :type path: str
        """

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=self._normalize_path(path),
            data=BytesIO(file_bytes),
            length=len(file_bytes),
            content_type=get_mime_type(file_bytes),
        )

    def get(self, path: str) -> bytes:
        """
        Получает объект из бакета и возвращает его содержимое в виде байтов.

        :param path: Путь/ключ объекта внутри бакета. Ведущие слэши будут отброшены.
        :type path: str
        :returns: Содержимое объекта в виде ``bytes``.
        :rtype: bytes
        """

        response = self.client.get_object(
            bucket_name=self.bucket_name,
            object_name=self._normalize_path(path),
        )
        try:
            return response.read()
        finally:
            if response:
                response.close()
                response.release_conn()

    def delete(self, path: str) -> None:
        """
        Удаляет объект(ы) из бакета.

        Если ``path`` заканчивается на ``/``, рассматривается как префикс - удаляются все объекты с данным
        префиксом (рекурсивно). Иначе удаляется один объект по указанному пути.

        :param path: Путь или префикс для удаления внутри бакета. Ведущие слэши будут отброшены.
        :type path: str
        """

        path = self._normalize_path(path)
        if path.endswith("/"):
            delete_object_list = list(
                map(
                    lambda x: DeleteObject(x.object_name),
                    self.client.list_objects(
                        bucket_name=self.bucket_name,
                        prefix=path,
                        recursive=True,
                    ),
                )
            )
            errors = self.client.remove_objects(
                bucket_name=self.bucket_name,
                delete_object_list=delete_object_list,
            )
            for _ in errors:
                ...
        else:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=path,
            )

    def exists(self, path: str) -> bool:
        """
        Проверяет существование объекта по пути.

        :param path: Путь к объекту.
        :type path: str
        :return: True, если объект существует, иначе False.
        :rtype: bool
        """

        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=self._normalize_path(path),
            )
            return True
        except S3Error:
            return False
