import streamlit as st


def main() -> None:
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if workspace_name := st.session_state.get("workspace_name"):
        with st.sidebar:
            st.html(
                f"""
                <center>
                    workspace:
                    <span style='color: green; background-color: lightgreen; border-radius: 0.25em; padding: 0 0.3em; margin-left: 0.3em;'>
                        {workspace_name}
                    </span>
                </center>
                """
            )
            st.divider()

    pg = st.navigation(
        [
            st.Page("workspaces_page.py", title="Пространства"),
            st.Page("docs_page.py", title="Документы"),
            st.Page("chat_page.py", title="Чаты"),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
