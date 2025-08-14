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


def ask_question(
    question: str, top_k: int, workspace_id: str, session_id: str | None
) -> Any:
    try:
        response: Response = requests.post(
            f"{BACKEND_URL}/v1/chat/ask",
            json={
                "question": question,
                "workspace_id": workspace_id,
                "session_id": session_id,
                "top_k": top_k,
            },
            timeout=30,
        )
        response.raise_for_status()
    except HTTPError:
        return {}
    else:
        return response.json()


def get_chat_history(session_id: str) -> Any:
    if not session_id:
        return {}

    try:
        response: Response = requests.get(
            f"{BACKEND_URL}/v1/chat/{session_id}/messages",
            params={"session_id": session_id},
            timeout=5,
        )
    except HTTPError:
        return {}
    else:
        return response.json()


def get_sessions(workspace_id: str) -> Any:
    try:
        response: Response = requests.get(
            f"{BACKEND_URL}/v1/chat",
            params={"workspace_id": workspace_id},
            timeout=5,
        )
    except HTTPError:
        return {}
    else:
        return response.json()


def render_chat_history(chat_history: list[Any]) -> None:
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.text(message["content"])


def render_answer_sources(sources):
    if not sources:
        return

    with st.expander("Источники"):
        for i, source in enumerate(sources, start=1):
            st.markdown(
                f"Источник {i}: [{source['document_name']}]"
                f"({BACKEND_URL}/v1/documents/{source['source_id']}/download) "
                f"(стр. {source['document_page']})"
            )


def render_llm_chat_input(
    prompt: str, top_k: int, workspace_id: str, session_id: str | None
):
    with st.spinner("Думаю...", show_time=True):
        response = ask_question(prompt, top_k, workspace_id, session_id)

        if response:
            session_id: str | None = response.get("session_id")
            if session_id:
                st.session_state.session_id = session_id

            with st.chat_message("assistant"):
                answer = response.get("answer", "Не удалось получить ответ.")
                sources = response.get("sources")

                st.text(answer)
                render_answer_sources(sources)


def main() -> None:
    workspace_id: str | None = st.session_state.get("workspace_id")
    if not workspace_id:
        return

    sessions: list[dict] = get_sessions(workspace_id)

    session_id: str | None = st.session_state.get("session_id")
    if not session_id or session_id not in (session.get("id") for session in sessions):
        st.session_state.session_id = None
        session_id = None

    with st.sidebar:
        with st.container():
            top_k: int = st.number_input(
                "Количество источников",
                value=3,
                min_value=1,
                max_value=10,
                help="Количество источников, на основе которых будет составлен контекст",
            )
            st.session_state.top_k = top_k
            if st.button("Начать новый диалог"):
                st.session_state.session_id = None
                st.rerun()
            st.divider()

        with st.container():
            st.text("Чаты")
            for chat in (session.get("id") for session in sessions):
                if st.button(chat):
                    st.session_state.session_id = chat
                    st.rerun()

    chat_history: list[Any] = get_chat_history(session_id)
    render_chat_history(chat_history)

    if prompt := st.chat_input("Спросите что-нибудь"):
        st.chat_message("user").text(prompt)
        top_k: int | None = st.session_state.get("top_k")
        render_llm_chat_input(prompt, top_k, workspace_id, session_id)


if __name__ == "__main__":
    main()
