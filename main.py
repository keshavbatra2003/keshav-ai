"""
KESHAV AI Assistant - Cross-Platform (Laptop & Mobile) App.
Built with Flet (Flutter in Python).
"""

import sys
import uuid
import flet as ft
import database
from theme import (
    DESKTOP_HEIGHT,
    DESKTOP_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MOBILE_BREAKPOINT,
    get_theme_colors,
)
from ui.chat_view import ChatView
from ui.history_drawer import HistorySidebar
from ui.settings_dialog import SettingsDialog


def main(page: ft.Page):
    # Initialize storage and create a private client identifier for this connection.
    # Every time a user opens or refreshes the link, they get their own isolated chat session
    # and cannot see conversations created by anyone else.
    database.init_db()
    client_id = str(uuid.uuid4())
    current_session_id = database.get_or_create_initial_session(client_id=client_id)
    settings = database.get_all_settings()
    is_dark = (settings.get("theme_mode", "dark") == "dark")

    # Configure Page and Window
    page.title = "KESHAV AI by Keshav Batra - Smart Cross-Platform Assistant"
    page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    if page.window:
        page.window.width = DESKTOP_WIDTH
        page.window.height = DESKTOP_HEIGHT
        page.window.min_width = MIN_WINDOW_WIDTH
        page.window.min_height = MIN_WINDOW_HEIGHT

    theme = get_theme_colors(is_dark)
    page.bgcolor = theme["bg"]

    # Initial check for mobile viewport (via user agent or window width)
    initial_width = page.width if page.width else DESKTOP_WIDTH
    is_mobile_ua = False
    ua = getattr(page, "client_user_agent", None)
    if ua:
        ua_lower = str(ua).lower()
        if any(x in ua_lower for x in ["mobile", "android", "iphone", "ipad"]):
            is_mobile_ua = True
    is_mobile = is_mobile_ua or (initial_width < MOBILE_BREAKPOINT)

    # --- Callbacks ---

    def on_select_session(session_id: str):
        nonlocal current_session_id
        current_session_id = session_id
        desktop_sidebar.set_current_session(session_id)
        mobile_sidebar.set_current_session(session_id)
        chat_view.load_session(session_id)
        if is_mobile:
            try:
                page.run_task(page.close_drawer)
            except Exception:
                pass

    def on_new_chat():
        nonlocal current_session_id
        new_id = database.create_session(title="New Chat", client_id=client_id)
        current_session_id = new_id
        desktop_sidebar.set_current_session(new_id)
        mobile_sidebar.set_current_session(new_id)
        chat_view.load_session(new_id)
        if is_mobile:
            try:
                page.run_task(page.close_drawer)
            except Exception:
                pass

    def on_delete_session(session_id: str):
        nonlocal current_session_id

        def confirm_delete(_):
            nonlocal current_session_id
            database.delete_session(session_id)
            page.pop_dialog()

            sessions = database.get_sessions(client_id=client_id)
            if not sessions:
                new_id = database.create_session(title="New Chat", client_id=client_id)
                current_session_id = new_id
            elif current_session_id == session_id:
                current_session_id = sessions[0]["id"]

            desktop_sidebar.set_current_session(current_session_id)
            mobile_sidebar.set_current_session(current_session_id)
            chat_view.load_session(current_session_id)

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Conversation?"),
            content=ft.Text("This will permanently delete this conversation and all its messages."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton(
                    "Delete",
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600),
                    on_click=confirm_delete,
                ),
            ],
        )
        page.show_dialog(dialog)

    def on_session_title_changed(session_id: str, new_title: str):
        desktop_sidebar.refresh_sessions()
        mobile_sidebar.refresh_sessions()

    def on_open_settings():
        settings_dialog = SettingsDialog(
            page=page,
            is_dark=is_dark,
            on_settings_saved=on_settings_saved,
        )
        settings_dialog.show()

    def on_settings_saved(new_settings: dict):
        nonlocal is_dark
        is_dark = (new_settings.get("theme_mode", "dark") == "dark")
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        new_theme = get_theme_colors(is_dark)
        page.bgcolor = new_theme["bg"]

        desktop_sidebar.set_dark_mode(is_dark)
        mobile_sidebar.set_dark_mode(is_dark)
        chat_view.set_dark_mode(is_dark)
        chat_view.update_model_badge()
        page.update()

    def on_toggle_drawer():
        try:
            page.run_task(page.show_drawer)
        except Exception as err:
            print("Toggle drawer error:", err)

    # --- UI Components ---

    # Desktop / Laptop persistent sidebar
    desktop_sidebar = HistorySidebar(
        current_session_id=current_session_id,
        is_dark=is_dark,
        on_select_session=on_select_session,
        on_new_chat=on_new_chat,
        on_delete_session=on_delete_session,
        on_open_settings=on_open_settings,
        client_id=client_id,
        width=290,
    )
    desktop_sidebar.visible = not is_mobile

    # Mobile Drawer sidebar
    mobile_sidebar = HistorySidebar(
        current_session_id=current_session_id,
        is_dark=is_dark,
        on_select_session=on_select_session,
        on_new_chat=on_new_chat,
        on_delete_session=on_delete_session,
        on_open_settings=on_open_settings,
        client_id=client_id,
        width=300,
    )

    page.drawer = ft.NavigationDrawer(
        controls=[mobile_sidebar],
    )

    # Main Chat View
    chat_view = ChatView(
        page=page,
        session_id=current_session_id,
        is_dark=is_dark,
        is_mobile=is_mobile,
        on_toggle_drawer=on_toggle_drawer,
        on_session_title_changed=on_session_title_changed,
        on_open_settings=on_open_settings,
        on_new_chat=on_new_chat,
        client_id=client_id,
    )

    # Main Layout Row (Sidebar + Chat Area)
    main_layout = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            desktop_sidebar,
            chat_view,
        ],
    )

    # Responsive Resize Listener
    def handle_resize(e):
        nonlocal is_mobile
        w = page.width if page.width else DESKTOP_WIDTH
        currently_mobile = w < MOBILE_BREAKPOINT

        if currently_mobile != is_mobile:
            is_mobile = currently_mobile
            desktop_sidebar.visible = not is_mobile
            chat_view.set_mobile_mode(is_mobile)
            page.update()

    page.on_resize = handle_resize

    # Global Desktop / Laptop Keyboard Shortcuts
    def handle_keyboard(e: ft.KeyboardEvent):
        cmd = e.ctrl or e.meta
        if cmd and e.key.lower() == "n":
            on_new_chat()
        elif cmd and e.key == ",":
            on_open_settings()
        elif cmd and e.key.lower() == "e":
            chat_view.export_conversation()
        elif cmd and e.key.lower() == "k":
            if desktop_sidebar.visible:
                desktop_sidebar.search_input.focus()

    page.on_keyboard_event = handle_keyboard

    # Add to page
    page.add(main_layout)


if __name__ == "__main__":
    import os
    run_web = "--web" in sys.argv
    if run_web:
        port = int(os.environ.get("PORT", 8550))
        host = os.environ.get("HOST", "127.0.0.1")
        ft.run(main, host=host, port=port, view=ft.AppView.WEB_BROWSER)
    else:
        ft.run(main)
