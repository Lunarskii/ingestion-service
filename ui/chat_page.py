from typing import Any
import os

import streamlit as st
from requests import (
    Response,
    HTTPError,
)
import requests


BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def ask_question(question: str, workspace_id: str) -> Any:
    try:
        response: Response = requests.post(
            f"{BACKEND_URL}/v1/chat/ask",
            json={"question": question, "workspace_id": workspace_id, "top_k": 3},  # TODO откуда получить top_k?
            timeout=5,
        )
        response.raise_for_status()
    except HTTPError as e:
        response_json = response.json()
        st.error(
            f"Произошла ошибка при обработке вашего запроса: {response_json['msg']}; "
            f"Код ошибки: '{response_json['code']}'"
        )
    else:
        return response.json()


def main() -> None:
    workspace_id = st.session_state["workspace_id"]
    if not workspace_id:
        return

    workspace_messages = f"{workspace_id}_messages"

    if workspace_messages not in st.session_state:
        st.session_state[workspace_messages] = []

    for message in st.session_state[workspace_messages]:
        with st.chat_message(message["role"]):
            st.text(message["content"])
            if "sources" in message:
                with st.expander("Источники"):
                    for source in message["sources"]:
                        st.info(f"**Фрагмент (ID: {source['chunk_id']}):**\n\n{source['snippet']}")

    if prompt := st.chat_input("Спросите что-нибудь"):
        st.chat_message("user").text(prompt)
        st.session_state[workspace_messages].append({"role": "user", "content": prompt})

        with st.spinner("Думаю..."):
            response = ask_question(prompt, workspace_id)

            if response:
                with st.chat_message("assistant"):
                    answer = response.get("answer", "Не удалось получить ответ.")
                    sources = response.get("sources", [])
                    st.text(answer)
                    with st.expander("Источники ответа"):
                        for source in sources:
                            st.info(f"**Chunk (ID: {source['chunk_id']}):**\n\n{source['snippet']}")

                    st.session_state[workspace_messages].append(
                        {"role": "assistant", "content": answer, "sources": sources}
                    )


if __name__ == "__main__":
    main()
