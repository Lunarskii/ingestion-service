from io import BytesIO

from minio import Minio
from minio.credentials.providers import Provider
from minio.deleteobjects import DeleteObject
from minio.error import S3Error
import urllib3

from app.interfaces import FileStorage
from app.utils.file import get_mime_type
from app.core import logger


class MinIOFileStorage(FileStorage):
    """
    Реализация файлового хранилища на базе MinIO/S3-совместимого хранилища.
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
        бакета; при отсутствии - пытается создать его.

        :param endpoint: URL/хост MinIO-сервера (может включать порт), например ``localhost:9000``.
        :param bucket_name: Имя бакета, где будут храниться объекты.
        :param access_key: Access key для аутентификации (логин).
        :param secret_key: Secret key для аутентификации (пароль).
        :param session_token: Session token для временных учётных данных.
        :param secure: Использовать HTTPS при соединении (True) или HTTP (False).
        :param region: Регион бакета.
        :param http_client: Кастомный urllib3.PoolManager для клиента.
        :param credentials: Поставщик учётных данных (Provider).
        :param cert_check: Флаг проверки TLS-сертификата сервера.
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
        self.bucket_name = bucket_name

        self._logger = logger.bind(
            endpoint=endpoint,
            bucket_name=bucket_name,
        )

        if not self.client.bucket_exists(self.bucket_name):
            try:
                self.client.make_bucket(bucket_name)
            except S3Error as e:
                self._logger.warning(
                    f"Произошла ошибка при создании бакета: возможно, бакет '{bucket_name}' уже создан",
                    error_message=str(e),
                )

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.lstrip("/")

    def save(self, file_bytes: bytes, path: str) -> None:
        """
        Сохраняет бинарные данные в MinIO как объект по указанному пути.

        :param file_bytes: Содержимое файла в виде байтов.
        :param path: Путь/ключ объекта внутри бакета. Ведущие слэши будут отброшены.

        :raises S3Error: Если произошла ошибка при сохранении файла.
        """

        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=self._normalize_path(path),
                data=BytesIO(file_bytes),
                length=len(file_bytes),
                content_type=get_mime_type(file_bytes),
            )
        except S3Error as e:
            self._logger.error(
                "Произошла ошибка при сохранении файла",
                error_message=str(e),
            )
            raise

    def get(self, path: str) -> bytes:
        """
        Получает объект из бакета и возвращает его содержимое в виде байтов.

        :param path: Путь/ключ объекта внутри бакета. Ведущие слэши будут отброшены.

        :returns: Содержимое объекта в виде байтов.
        :raises S3Error: Если произошла ошибка при чтении файла.
        """

        response = None
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=self._normalize_path(path),
            )
            return response.read()
        except S3Error as e:
            self._logger.error(
                "Произошла ошибка при чтении файла",
                error_message=str(e),
            )
            raise
        finally:
            if response:
                response.close()
                response.release_conn()

    def delete(self, path: str) -> None:
        """
        Удаляет объект(ы) из бакета.

        :param path: Путь для удаления внутри бакета. Ведущие слэши будут отброшены.

        :raises S3Error: Если произошла ошибка при удалении файла.
        """

        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=self._normalize_path(path),
            )
        except S3Error as e:
            self._logger.error(
                "Произошла ошибка при удалении файла",
                error_message=str(e),
            )
            raise

    def delete_dir(self, path: str) -> None:
        """
        Рекурсивно удаляет объекты из бакета по указанному пути.

        :param path: Путь к директории, из которой будут удалены все объекты.

        :raises S3Error: Если произошла ошибка при чтении списка файлов в бакете.
        """

        path: str = self._normalize_path(path)
        try:
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
        except S3Error as e:
            self._logger.error(
                "Произошла ошибка при чтении списка файлов в бакете",
                prefix=path,
                error_message=str(e),
            )
            raise

        errors = self.client.remove_objects(
            bucket_name=self.bucket_name,
            delete_object_list=delete_object_list,
        )
        for error in errors:
            self._logger.error(
                "Произошла ошибка при удалении файла",
                error_message=error.message,
            )

    def exists(self, path: str) -> bool:
        """
        Проверяет существование объекта в бакете по указанному пути.

        :param path: Путь к объекту.
        :return: True, если объект существует, иначе False.
        """

        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=self._normalize_path(path),
            )
            return True
        except S3Error:
            return False
