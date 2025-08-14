from typing import Any
import os

from streamlit.runtime.uploaded_file_manager import UploadedFile
import streamlit as st
from requests import (
    Response,
    HTTPError,
)
import requests


BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise RuntimeError("Переменная окружения BACKEND_URL не установлена")


def upload_file(file: UploadedFile, workspace_id: str) -> Any:
    try:
        response: Response = requests.post(
            url=f"{BACKEND_URL}/v1/documents/upload",
            params={"workspace_id": workspace_id},
            files={"file": (file.name, file, file.type)},
            timeout=5,
        )
        response.raise_for_status()
    except HTTPError:
        response_json = response.json()
        st.error(response_json["msg"])
    else:
        response_json = response.json()
        st.success(
            f"Документ успешно принят в обработку! ID документа: {response_json.get('document_id')}"
        )
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


def main() -> None:
    workspace_id: str = st.session_state.get("workspace_id")
    if not workspace_id:
        return

    st.header("Документы", divider=True)

    documents: list[dict] = get_documents(workspace_id)

    refresh_btn, add_btn, remove_btn, _ = st.columns([0.035, 0.035, 0.035, 0.895])
    if refresh_btn.button("", icon=":material/refresh:"):
        st.rerun()
    if add_btn.button("", icon=":material/add:"):

        def on_change_uploaded_file():
            if file := st.session_state["uploaded_file"]:
                with st.spinner("Добавление документа в очередь на обработку..."):
                    upload_file(file, workspace_id)

        st.file_uploader(
            "Загрузить документ",
            type=["pdf", "docx"],
            key="uploaded_file",
            on_change=on_change_uploaded_file,
            width=256,
        )
    if remove_btn.button("", icon=":material/remove:"):
        pass

    if documents:
        st.dataframe(
            documents,
            use_container_width=True,
            hide_index=True,
            column_config={"workspace_id": None},
        )
    else:
        st.text("В этом пространстве пока нет документов.")


if __name__ == "__main__":
    main()
