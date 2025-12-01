from typing import (
    Any,
    Iterable,
)
from uuid import uuid4
import os
import urllib.parse
import re

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
    question: str,
    top_k: int,
    workspace_id: str,
    session_id: str | None,
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
            timeout=1800,
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
            render_answer_sources(message["sources"])


def parse_filename_from_content_disposition(cd: str | None) -> str | None:
    if not cd:
        return None

    m = re.search(r"filename\*\s*=\s*([^;]+)", cd, flags=re.I)
    if m:
        val = m.group(1).strip().strip('"').strip("'")
        if "''" in val:
            try:
                _enc, enc_fname = val.split("''", 1)
                return urllib.parse.unquote(enc_fname)
            except Exception:
                return urllib.parse.unquote(val)
        try:
            return urllib.parse.unquote(val)
        except Exception:
            return val

    m2 = re.search(r'filename\s*=\s*"([^"]+)"', cd, flags=re.I)
    if m2:
        return m2.group(1)

    m3 = re.search(r"filename\s*=\s*([^;]+)", cd, flags=re.I)
    if m3:
        return m3.group(1).strip().strip('"').strip("'")

    return None


def render_answer_sources(sources):
    if not sources:
        return

    with st.expander("Источники"):
        for i, source in enumerate(sources, start=1):
            title: str = source.get("title", "Без имени")
            source_id: str = source["source_id"]
            chunks: Any = source.get("chunks", [])

            if not chunks:
                continue

            def merge_page_ranges() -> list[dict[str, int]]:
                ranges: list[tuple[int, int]] = []

                for chunk in chunks:
                    page_start = chunk.get("page_start")
                    page_end = chunk.get("page_end")

                    if not page_start or not page_end:
                        continue

                    page_start = int(page_start)
                    page_end = int(page_end)
                    if page_start > page_end:
                        page_start, page_end = page_end, page_start
                    ranges.append((page_start, page_end))

                if not ranges:
                    return []

                ranges.sort(key=lambda x: (x[0], x[1]))

                merged: list[dict[str, int]] = []
                current_start, current_end = ranges[0]

                for page_start, page_end in ranges[1:]:
                    if page_start <= current_end + 1:
                        if page_end > current_end:
                            current_end = page_end
                    else:
                        merged.append({"page_start": current_start, "page_end": current_end})
                        current_start, current_end = page_start, page_end

                merged.append({"page_start": current_start, "page_end": current_end})
                return merged

            page_value: str = ", ".join(
                [
                    f"{page['page_start']}-{page['page_end']}" if page["page_start"] != page["page_end"] else f"{page['page_start']}"
                    for page in merge_page_ranges()
                ],
            )

            with st.container():
                def download(url):
                    response = requests.get(url)

                    if response.status_code == 200:
                        st.download_button(
                            label="Подтверждение скачивания",
                            data=response.content,
                            file_name=parse_filename_from_content_disposition(response.headers.get("Content-Disposition")),
                            mime=response.headers.get("Content-Type", "application/octet-stream"),
                        )
                    else:
                        st.error(f"Ошибка загрузки: {response.status_code} {response.text}")

                st.text(f"Источник {i}: {title} (стр. {page_value})")
                st.button(
                    "Скачать",
                    key=str(uuid4()),
                    on_click=download,
                    args=[f"{BACKEND_URL}/v1/documents/{source_id}/download"],
                )


def render_llm_chat_input(
    prompt: str,
    top_k: int,
    workspace_id: str,
    session_id: str | None,
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
    if not session_id or session_id not in (
        session.get("session_id") for session in sessions
    ):
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
            for chat in (session.get("session_id") for session in sessions):
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
