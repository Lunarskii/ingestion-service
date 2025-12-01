from typing import Any
import os

import streamlit as st
from requests import (
    Response,
    HTTPError,
)
import requests


BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise RuntimeError("Переменная окружения BACKEND_URL не установлена")


def get_workspaces() -> Any:
    try:
        response: Response = requests.get(
            url=f"{BACKEND_URL}/v1/workspaces",
        )
        response.raise_for_status()
    except HTTPError:
        st.error("...")
    else:
        return response.json()


def create_workspace(name: str) -> Any:
    try:
        response: Response = requests.post(
            url=f"{BACKEND_URL}/v1/workspaces",
            params={"name": name},
        )
        response.raise_for_status()
    except HTTPError:
        st.error("...")
    else:
        return response.json()


def delete_workspace(workspace_id: str) -> None:
    try:
        response: Response = requests.delete(
            url=f"{BACKEND_URL}/v1/workspaces/{workspace_id}",
        )
        response.raise_for_status()
    except HTTPError:
        st.error("...")


def main() -> None:
    st.header("Пространства документов", divider=True)

    workspaces: list[dict] = get_workspaces()

    refresh_btn, add_btn, remove_btn, _ = st.columns([0.035, 0.035, 0.035, 0.895])
    if refresh_btn.button("", icon=":material/refresh:"):
        st.rerun()
    if add_btn.button("", icon=":material/add:"):

        @st.dialog("Создать рабочее пространство")
        def create_workspace_dialog():
            new_workspace_name: str | None = st.text_input(
                "Имя рабочего пространства (Workspace)",
                placeholder="default",
            )
            if st.button("Создать") and new_workspace_name:
                create_workspace(new_workspace_name)
                st.rerun()

        create_workspace_dialog()
    if remove_btn.button("", icon=":material/remove:"):
        workspace_name: str | None = st.session_state.get("workspace_name")
        workspace_id: str | None = st.session_state.get("workspace_id")

        @st.dialog("Удалить рабочее пространство")
        def delete_workspace_dialog():
            st.text(f"Удалить рабочее пространство '{workspace_name}'?")
            if st.button("Подтвердить удаление"):
                delete_workspace(workspace_id)
                st.session_state.workspace_name = None
                st.session_state.workspace_id = None
                st.session_state.select_box_workspace_name_index = None
                st.rerun()

        if workspace_name and workspace_id:
            delete_workspace_dialog()

    if workspaces:
        st.dataframe(
            workspaces,
            width="stretch",
            hide_index=True,
        )
    else:
        st.text("Пространств пока нет, добавьте одно.")


if __name__ == "__main__":
    main()
