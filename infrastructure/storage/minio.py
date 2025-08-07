from io import BytesIO

from minio import Minio
from minio.credentials.providers import Provider
from minio.deleteobjects import DeleteObject
import urllib3

from services import RawStorage


class MinIORawStorage(RawStorage):
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

    def save(self, file_bytes: bytes, path: str) -> None:
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=path.lstrip("/"),
            data=BytesIO(file_bytes),
            length=len(file_bytes),
        )

    def get(self, path: str) -> bytes:
        response = self.client.get_object(
            bucket_name=self.bucket_name,
            object_name=path.lstrip("/"),
        )
        try:
            return response.read()
        finally:
            if response:
                response.close()
                response.release_conn()

    def delete(self, path: str) -> None:
        path = path.lstrip("/")
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
            self.client.remove_objects(
                bucket_name=self.bucket_name,
                delete_object_list=delete_object_list,
            )
        else:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=path,
            )
