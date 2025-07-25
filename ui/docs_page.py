from typing import Any

from streamlit.runtime.uploaded_file_manager import UploadedFile
import streamlit as st
from requests import (
    Response,
    HTTPError,
)
import requests


BACKEND_URL = "http://127.0.0.1:8000"  # TODO вынести в переменные окружения, будет приходить из docker-compose


def upload_file(file: UploadedFile, workspace_id: str) -> Any:
    try:
        response: Response = requests.post(
            url=f"{BACKEND_URL}/v1/documents/upload",
            params={"workspace_id": workspace_id},
            files={"file": (file.name, file, file.type)},
            timeout=5,
        )
        response.raise_for_status()
    except HTTPError as e:
        st.error(f"Ошибка загрузки: {e!r}")
    else:
        response_json = response.json()
        st.success(f"Документ успешно принят в обработку! ID документа: {response_json.get('document_id')}")
        return response_json


def get_documents(workspace_id: str) -> Any:
    try:
        response: Response = requests.get(
            url=f"{BACKEND_URL}/v1/documents",
            params={"workspace_id": workspace_id},
            timeout=5,
        )
        response.raise_for_status()
    except HTTPError as e:
        st.error(f"Ошибка при попытке получить список документов: {e!r}")
    else:
        return response.json()


def main():
    workspace_id = st.session_state["workspace_id"]
    if not workspace_id:
        return

    with st.sidebar:
        def on_change_uploaded_file():
            if file := st.session_state['uploaded_file']:
                with st.spinner(f"Добавление документа в очередь на обработку..."):
                    _: Any = upload_file(file, workspace_id)

        st.header("Файлы")
        st.file_uploader(
            "Загрузить документ",
            type=["pdf", "docx"],
            key="uploaded_file",
            on_change=on_change_uploaded_file,
        )

    st.header(f"Документы", divider=True)
    if docs := get_documents(workspace_id):
        st.dataframe(docs, use_container_width=True, hide_index=True, column_config={"workspace_id": None})
    else:
        st.text("В этом пространстве пока нет документов.")
    if st.button("Обновить"):
        st.rerun()


if __name__ == "__main__":
    main()
