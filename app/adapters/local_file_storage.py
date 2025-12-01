import os
import shutil

from app.interfaces import FileStorage
from app.core import logger


class LocalFileStorage(FileStorage):
    """
    Реализация локального файлового хранилища.
    """

    def __init__(self, directory: str):
        """
        Проверяет, что параметр `directory` является директорией,
        создает её при необходимости.

        :param directory: Базовый путь, куда будут сохраняться директории/файлы.

        :raises ValueError: Если переданный параметр не является директорией.
        """

        if os.path.isfile(directory):
            raise ValueError(
                f"Передаваемый параметр 'directory' должен быть директорией, "
                f"но было получено {directory}",
            )

        self.directory: str = directory
        if not directory.endswith(os.path.sep):
            self.directory += os.path.sep
        os.makedirs(self.directory, exist_ok=True)

        self._logger = logger.bind(base_dir=directory)

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.lstrip("/")

    def _build_full_path(self, path: str) -> str:
        return os.path.join(
            self.directory,
            self._normalize_path(path),
        )

    def save(self, file_bytes: bytes, path: str) -> None:
        """
        Сохраняет бинарные данные файла в сырое хранилище.

        :param file_bytes: Содержимое файла в виде байтов.
        :param path: Логический или файловый путь, по которому нужно сохранить файл.

        :raises FileNotFoundError: Если произошла ошибка во время записи в файл или часть пути не была создана.
                                   Возможно проблема с конкурентностью и путь был удален в процессе.
        :raises Exception: Если произошла неизвестная ошибка при записи в файл.
        """

        full_path: str = self._build_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "wb") as file:
                file.write(file_bytes)
        except FileNotFoundError:
            self._logger.warning(
                "Часть пути не была создана, возможно проблема с конкурентностью и путь был удален в процессе",
                path=full_path,
            )
            raise
        except Exception as e:
            self._logger.error(
                "Неизвестная ошибка при записи в файл",
                path=full_path,
                error_message=str(e),
            )
            raise

    def get(self, path: str) -> bytes:
        """
        Возвращает бинарные данные файла по указанному пути.

        :param path: Логический или файловый путь к файлу.

        :return: Файл в байтах.
        :raises FileNotFoundError: Если переданный путь не является файлом или файл не найден.
        :raises Exception: Если произошла неизвестная ошибка при чтении файла.
        """

        full_path: str = self._build_full_path(path)
        if not os.path.isfile(full_path):
            message: str = "Переданный путь не является файлом"
            self._logger.warning(message, path=full_path)
            raise FileNotFoundError(message)
        try:
            with open(full_path, "rb") as file:
                return file.read()
        except FileNotFoundError:
            self._logger.warning(
                "Файл не найден, возможно проблема с конкурентностью и файл был удален в процессе",
                path=full_path,
            )
            raise
        except Exception as e:
            self._logger.error(
                "Неизвестная ошибка при чтении файла",
                path=full_path,
                error_message=str(e),
            )
            raise

    def delete(self, path: str) -> None:
        """
        Удаляет файл по указанному пути.

        :param path: Путь к удаляемому файлу. Если путь указывает на файл, то будет удален,
                     иначе ничего не произойдет.

        :raises FileNotFoundError: Если переданный путь не является файлом.
        """

        full_path: str = self._build_full_path(path)
        if not os.path.isfile(full_path):
            message: str = "Переданный путь не является файлом"
            self._logger.warning(message, path=full_path)
            raise FileNotFoundError(message)
        os.remove(full_path)

    def delete_dir(self, path: str) -> None:
        """
        Удаляет конечную директорию по указанному пути (+все вложенные файлы),
        т.е., если переданный путь 'dir1/dir2/dir3', то будет удалена только
        директория 'dir3', директории 'dir1' и 'dir2' затронуты не будут.

        :param path: Путь к удаляемой директории. Если путь указывает на директорию,
                     будет рекурсивно удалена вся директория, иначе ничего не произойдет.

        :raises FileNotFoundError: Если переданный путь не является существующей директорией.
        """

        full_path: str = self._build_full_path(path)
        if not os.path.isdir(full_path):
            message: str = "Переданный путь не является существующей директорией"
            self._logger.warning(message, path=full_path)
            raise FileNotFoundError(message)
        shutil.rmtree(full_path)

    def exists(self, path: str) -> bool:
        full_path: str = self._build_full_path(path)
        return os.path.isfile(full_path)
