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


def ask_question(question: str, workspace_id: str) -> Any:
    try:
        response: Response = requests.post(
            f"{BACKEND_URL}/v1/chat/ask",
            json={
                "question": question,
                "workspace_id": workspace_id,
                "top_k": 3,
            },  # TODO откуда получить top_k?
            timeout=30,
        )
        response.raise_for_status()
    except HTTPError:
        response_json = response.json()
        if "msg" in response_json and "code" in response_json:
            st.error(
                f"Произошла ошибка при обработке вашего запроса: {response_json['msg']}; "
                f"Код ошибки: '{response_json['code']}'"
            )
        else:
            st.error(f"Произошла неизвестная ошибка: {response_json}")
        return response_json
    else:
        return response.json()


def render_chat_history(chat_history_state: str) -> None:
    for message in st.session_state[chat_history_state]:
        with st.chat_message(message["role"]):
            st.text(message["content"])
            render_answer_sources(message.get("sources"))


def render_answer_sources(sources):
    if not sources:
        return

    with st.expander("Источники"):
        for source in sources:
            st.info(f"**Chunk (ID: {source['chunk_id']}):**" f"\n\n" f"{source['snippet']}")


def render_llm_chat_input(chat_history_state):
    prompt: str = st.session_state.prompt
    workspace_id: str = st.session_state.workspace_id

    with st.spinner("Думаю..."):
        response = ask_question(prompt, workspace_id)

        if response:
            with st.chat_message("assistant"):
                answer = response.get("answer", "Не удалось получить ответ.")
                sources = response.get("sources")

                st.text(answer)
                render_answer_sources(sources)

                st.session_state[chat_history_state].append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )


def main() -> None:
    workspace_id: str = st.session_state["workspace_id"]
    if not workspace_id:
        return

    chat_history_state = f"{workspace_id}_chat_history"

    if chat_history_state not in st.session_state:
        st.session_state[chat_history_state] = []
    if "awaiting_chat_response" not in st.session_state:
        st.session_state.awaiting_chat_response = False

    render_chat_history(chat_history_state)

    if st.session_state.awaiting_chat_response:
        st.chat_input("Спросите что-нибудь", disabled=True)
        render_llm_chat_input(chat_history_state)
        st.session_state.awaiting_chat_response = False
        st.rerun()
    else:
        if prompt := st.chat_input("Спросите что-нибудь"):
            st.session_state.prompt = prompt
            st.chat_message("user").text(prompt)
            st.session_state[chat_history_state].append({"role": "user", "content": prompt})
            st.session_state.awaiting_chat_response = True
            st.rerun()


if __name__ == "__main__":
    main()
