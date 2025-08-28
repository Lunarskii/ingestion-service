# import os
# import sqlite3
#
# from tests.conftest import ValueGenerator
# from stubs import SQLiteMetadataRepository
# from domain.document.schemas import Document
#
#
# class TestSQLiteMetadataRepository:
#     def test_init_creates_database_and_table(self, tmp_path):
#         sqlite_url: str = (
#             f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
#         )
#         table_name: str = f"{ValueGenerator.word()}"
#         assert not os.path.exists(sqlite_url)
#
#         _ = SQLiteMetadataRepository(sqlite_url=sqlite_url, table_name=table_name)
#         assert os.path.exists(sqlite_url)
#
#         db_connection = sqlite3.connect(sqlite_url)
#         cursor = db_connection.cursor()
#         cursor.execute(
#             "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
#             (table_name,),
#         )
#         row = cursor.fetchone()
#         db_connection.close()
#
#         assert row is not None and row[0] == table_name
#
#     def test_save_inserts_metadata_correctly(
#         self,
#         tmp_path,
#         document_metadata: Document = ValueGenerator.document_metadata(),
#     ):
#         sqlite_url: str = (
#             f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
#         )
#         table_name: str = f"{ValueGenerator.word()}"
#
#         metadata_repository = SQLiteMetadataRepository(
#             sqlite_url=sqlite_url, table_name=table_name
#         )
#         metadata_repository.save(document_metadata)
#
#         db_connection = sqlite3.connect(sqlite_url)
#         db_connection.row_factory = sqlite3.Row
#         cursor = db_connection.cursor()
#         cursor.execute(
#             f"SELECT * FROM {table_name} WHERE document_id = ?",
#             (document_metadata.document_id,),
#         )
#         row = cursor.fetchone()
#         db_connection.close()
#
#         assert dict(row) == document_metadata.model_dump()
#
#     def test_get_returns_metadata_list(self, tmp_path):
#         sqlite_url: str = (
#             f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
#         )
#         table_name: str = f"{ValueGenerator.word()}"
#         document_metadata: Document = ValueGenerator.document_metadata()
#
#         metadata_repository = SQLiteMetadataRepository(
#             sqlite_url=sqlite_url, table_name=table_name
#         )
#         metadata_repository.save(document_metadata)
#
#         assert metadata_repository.get() == [document_metadata]
#
#     def test_get_returns_empty_metadata_list(self, tmp_path):
#         sqlite_url: str = (
#             f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
#         )
#         table_name: str = f"{ValueGenerator.word()}"
#
#         metadata_repository = SQLiteMetadataRepository(
#             sqlite_url=sqlite_url, table_name=table_name
#         )
#         assert metadata_repository.get() == []
#
#     def test_delete_one_row(self, tmp_path):
#         sqlite_url: str = (
#             f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
#         )
#         table_name: str = f"{ValueGenerator.word()}"
#         document_metadata_list: list[Document] = [
#             ValueGenerator.document_metadata(),
#             ValueGenerator.document_metadata(),
#         ]
#
#         metadata_repository = SQLiteMetadataRepository(
#             sqlite_url=sqlite_url, table_name=table_name
#         )
#         metadata_repository.save(document_metadata_list[0])
#         metadata_repository.save(document_metadata_list[1])
#
#         assert metadata_repository.get() == document_metadata_list
#
#         metadata_repository.delete(document_id=document_metadata_list[1].document_id)
#
#         assert metadata_repository.get() == [document_metadata_list[0]]
#
#     def test_delete_all_rows(self, tmp_path):
#         sqlite_url: str = (
#             f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
#         )
#         table_name: str = f"{ValueGenerator.word()}"
#         document_metadata_list: list[Document] = [
#             ValueGenerator.document_metadata(),
#             ValueGenerator.document_metadata(),
#         ]
#
#         metadata_repository = SQLiteMetadataRepository(
#             sqlite_url=sqlite_url, table_name=table_name
#         )
#         metadata_repository.save(document_metadata_list[0])
#         metadata_repository.save(document_metadata_list[1])
#
#         assert metadata_repository.get() == document_metadata_list
#
#         metadata_repository.delete()
#
#         assert metadata_repository.get() == []
