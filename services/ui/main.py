import streamlit as st

from workspaces_page import get_workspaces


def main() -> None:
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        if workspaces := get_workspaces():
            select_box_workspace_name_index: int | None = st.session_state.get(
                "select_box_workspace_name_index"
            )

            def on_change_workspace_name():
                workspace_name: str | None = st.session_state.get(
                    "select_box_workspace_name"
                )
                if not workspace_name:
                    return

                for i, workspace in enumerate(workspaces):
                    if workspace_name == workspace.get("name"):
                        st.session_state.workspace_name = workspace_name
                        st.session_state.workspace_id = workspace.get("workspace_id")
                        st.session_state.select_box_workspace_name_index = i
                        break

            st.selectbox(
                "Имя рабочего пространства (Workspace)",
                (workspace.get("name") for workspace in workspaces),
                index=select_box_workspace_name_index,
                key="select_box_workspace_name",
                on_change=on_change_workspace_name,
                placeholder="Выбери пространство",
                width=256,
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
