import streamlit as st


def main() -> None:
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        workspace_form_container = st.container()

        def on_change_workspace_id():
            if not st.session_state["workspace_id"]:
                workspace_form_container.error(
                    "Поле с Workspace ID не может быть пустым"
                )

        workspace_form_container.header("Управление")
        workspace_form_container.text_input(
            "ID рабочего пространства (Workspace)",
            key="workspace_id",
            placeholder="default",
            on_change=on_change_workspace_id,
        )
        st.divider()

    if workspace_id := st.session_state["workspace_id"]:
        st.html(
            f"""
            <center>
                workspace:
                <span style='color: green; background-color: lightgreen; border-radius: 0.25em; padding: 0 0.3em; margin-left: 0.3em;'>
                    {workspace_id}
                </span>
            </center>
            """
        )

    pg = st.navigation(
        [
            st.Page("docs_page.py", title="Документы"),
            st.Page("chat_page.py", title="Чаты"),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
