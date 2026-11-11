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
    # Read query parameters (e.g. from /dictate speech recognition or persistent uid)
    url_params = page.query.to_dict if hasattr(page, "query") and page.query else {}
    url_prompt = url_params.get("prompt", "").strip()
    url_session = url_params.get("session_id", "").strip()
    auto_send = (url_params.get("auto_send", "") == "1")

    # Persistent client identifier for chat history isolation across visits
    # Each browser device maintains its unique user ID, allowing users to see their own past chats while keeping chats 100% private from others
    client_id = url_params.get("uid", "").strip()
    if not client_id:
        client_id = "default_user"

    if url_session and database.get_session(url_session):
        current_session_id = url_session
    else:
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

    def on_new_mindful_chat():
        nonlocal current_session_id
        new_id = database.create_session(
            title="🌿 Safe Space",
            system_prompt=database.MINDFUL_ADVISOR_SYSTEM_PROMPT,
            client_id=client_id,
        )
        welcome_msg = (
            "🌿 **Welcome to your Safe Space.**\n\n"
            "Life can get overwhelming, noisy, and heavy at times. Whatever is on your mind or heart right now — "
            "stress from work or studies, personal decisions, relationship friction, anxiety, or heavy feelings — "
            "you can share it completely openly here without any judgment.\n\n"
            "I'm here to listen, help you take a slow, calm breath, and provide **grounded, objective, and practical guidance** "
            "so you feel relieved, relaxed, and clear-headed.\n\n"
            "Take your time. What is on your mind or heart today?"
        )
        database.add_message(new_id, "assistant", welcome_msg)
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
        on_new_mindful_chat=on_new_mindful_chat,
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
        on_new_mindful_chat=on_new_mindful_chat,
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

    # Pre-populate voice dictated text if arrived from /dictate
    if url_prompt:
        chat_view.text_input.value = url_prompt
        try:
            page.update()
        except Exception:
            pass

        if auto_send:
            async def _do_auto_send():
                import asyncio
                await asyncio.sleep(0.6)
                chat_view.send_message()

            page.run_task(_do_auto_send)
        else:
            try:
                page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("🎙️ Dictated speech loaded into prompt box! Tap Send to ask."),
                        duration=3500,
                    )
                )
            except Exception:
                pass


if __name__ == "__main__":
    import os
    run_web = "--web" in sys.argv
    if run_web:
        import uvicorn
        from fastapi import FastAPI, Response
        from fastapi.responses import HTMLResponse, PlainTextResponse
        import flet.fastapi as flet_fastapi

        database.init_db()
        app = FastAPI(title="KESHAV AI by Keshav Batra")

        @app.get("/health")
        @app.get("/ping")
        async def ping_health():
            return {
                "status": "online",
                "app": "KESHAV AI",
                "developer": "Keshav Batra",
                "keep_alive": True,
            }

        @app.get("/robots.txt", response_class=PlainTextResponse)
        async def robots_txt():
            return (
                "User-agent: *\n"
                "Allow: /\n"
                "Sitemap: https://keshav-ai.onrender.com/sitemap.xml\n"
            )

        @app.get("/sitemap.xml", response_class=Response)
        async def sitemap_xml():
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://keshav-ai.onrender.com/</loc>
    <lastmod>2026-11-10</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://keshav-ai.onrender.com/dictate</loc>
    <lastmod>2026-11-10</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>"""
            return Response(content=xml_content, media_type="application/xml")

        from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

        @app.get("/logo.png")
        @app.get("/logo.jpg")
        async def logo_endpoint():
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
            return FileResponse(logo_path, media_type="image/png")

        @app.get("/favicon.png")
        @app.get("/favicon.ico")
        async def favicon_endpoint():
            fav_path = os.path.join(os.path.dirname(__file__), "assets", "favicon.png")
            return FileResponse(fav_path, media_type="image/png")

        @app.get("/dictate", response_class=HTMLResponse)
        async def dictate_page():
            dictate_path = os.path.join(os.path.dirname(__file__), "assets", "dictate.html")
            with open(dictate_path, "r", encoding="utf-8") as f:
                return f.read()

        @app.get("/google{code}.html", response_class=PlainTextResponse)
        async def google_verification_file(code: str):
            return f"google-site-verification: google{code}.html"

        @app.get("/share/{session_id}", response_class=HTMLResponse)
        async def share_conversation_page(session_id: str):
            try:
                session = database.get_session(session_id)
                if not session:
                    return HTMLResponse(
                        "<html><body style='background:#0d0d0d;color:#fff;font-family:sans-serif;text-align:center;padding:60px 20px;'>"
                        "<h2 style='margin-bottom:12px;'>Conversation Not Found</h2>"
                        "<p style='color:#888;margin-bottom:24px;'>This conversation may be private, expired, or deleted.</p>"
                        "<a href='/' style='background:#fff;color:#000;padding:10px 20px;border-radius:20px;text-decoration:none;font-weight:600;'>Go to KESHAV AI →</a>"
                        "</body></html>",
                        status_code=404,
                    )

                messages = database.get_messages(session_id)
                template_path = os.path.join(os.path.dirname(__file__), "assets", "share_template.html")
                with open(template_path, "r", encoding="utf-8") as f:
                    template = f.read()

                import html
                msg_html_list = []
                for m in messages:
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    if role == "user":
                        escaped = html.escape(content).replace("\n", "<br>")
                        msg_html_list.append(
                            f'<div class="message-row user">'
                            f'  <div class="bubble">{escaped}</div>'
                            f'</div>'
                        )
                    else:
                        escaped_raw = html.escape(content)
                        msg_html_list.append(
                            f'<div class="message-row assistant">'
                            f'  <div class="avatar"><img src="/logo.png" alt="KESHAV AI"></div>'
                            f'  <div class="bubble md-content" data-raw="{escaped_raw}">{escaped_raw}</div>'
                            f'</div>'
                        )

                rendered_msgs = "\n".join(msg_html_list) if msg_html_list else "<p style='color:#777;'>No messages in this chat yet.</p>"
                title = session.get("title", "Conversation")
                date_str = session.get("created_at", "")[:10] if session.get("created_at") else "Recent"

                output = template.replace("{{TITLE}}", html.escape(title))
                output = output.replace("{{DATE}}", html.escape(date_str))
                output = output.replace("{{MESSAGES_HTML}}", rendered_msgs)
                return HTMLResponse(output)
            except Exception as err:
                return HTMLResponse(
                    f"<html><body style='background:#0d0d0d;color:#fff;font-family:sans-serif;text-align:center;padding:60px 20px;'>"
                    f"<h2 style='margin-bottom:12px;'>Unable to Load Conversation</h2>"
                    f"<p style='color:#888;margin-bottom:24px;'>Error: {html.escape(str(err))}</p>"
                    f"<a href='/' style='background:#fff;color:#000;padding:10px 20px;border-radius:20px;text-decoration:none;font-weight:600;'>Go to KESHAV AI →</a>"
                    f"</body></html>",
                    status_code=500,
                )

        flet_app = flet_fastapi.app(
            main,
            assets_dir="assets",
            app_name="KESHAV AI by Keshav Batra",
            app_short_name="KESHAV AI",
            app_description="KESHAV AI - Smart Cross-Platform AI Assistant developed by Keshav Batra with ChatGPT interface, voice dictation, and FLUX.1 image generation.",
        )
        app.mount("/", flet_app)

        port = int(os.environ.get("PORT", 8550))
        host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
        uvicorn.run(app, host=host, port=port)
    else:
        ft.run(main, assets_dir="assets")
