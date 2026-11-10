"""
Conversation history sidebar and mobile drawer.
Supports searching sessions, starting new chats, switching sessions, and deleting chats.
"""

from typing import Callable, List, Optional
import flet as ft
import database
from theme import get_theme_colors


class HistorySidebar(ft.Container):
    def __init__(
        self,
        current_session_id: str,
        is_dark: bool,
        on_select_session: Callable[[str], None],
        on_new_chat: Callable[[], None],
        on_delete_session: Callable[[str], None],
        on_open_settings: Callable[[], None],
        client_id: Optional[str] = None,
        width: int = 280,
    ):
        super().__init__()
        self.current_session_id = current_session_id
        self.is_dark = is_dark
        self.on_select_session = on_select_session
        self.on_new_chat = on_new_chat
        self.on_delete_session = on_delete_session
        self.on_open_settings = on_open_settings
        self.client_id = client_id
        self.search_query = ""

        self.width = width
        self.padding = ft.Padding(12, 16, 12, 16)
        self.update_colors()

        # UI Elements
        self.search_input = ft.TextField(
            hint_text="Search conversations...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            dense=True,
            content_padding=ft.Padding(10, 8, 10, 8),
            border=ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(1, self.theme["border"]),
            ),
            bgcolor=self.theme["input_bg"],
            color=self.theme["text_primary"],
            hint_style=ft.TextStyle(size=12.5, color=self.theme["text_muted"]),
            on_change=self._on_search_change,
        )

        self.session_list_view = ft.ListView(
            expand=True,
            spacing=6,
            padding=0,
        )

        self._build_layout()
        self.refresh_sessions()

    def update_colors(self):
        self.theme = get_theme_colors(self.is_dark)
        self.bgcolor = self.theme["surface"]
        self.border = ft.Border(
            right=ft.BorderSide(width=1, color=self.theme["border"])
        )

    def set_dark_mode(self, is_dark: bool):
        self.is_dark = is_dark
        self.update_colors()
        self.search_input.border = ft.OutlineInputBorder(
            border_radius=12,
            side=ft.BorderSide(1, self.theme["border"]),
        )
        self.search_input.bgcolor = self.theme["input_bg"]
        self.search_input.color = self.theme["text_primary"]
        self.search_input.hint_style = ft.TextStyle(size=12.5, color=self.theme["text_muted"])
        self.refresh_sessions()

    def _build_layout(self):
        # Header with Logo & Brand
        brand_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=32,
                            height=32,
                            border_radius=16,
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            border=ft.Border.all(1, "#383838" if self.is_dark else "#CCCCCC"),
                            bgcolor="#000000",
                            content=ft.Image(
                                src="/logo.png",
                                width=32,
                                height=32,
                                fit=ft.BoxFit.COVER,
                            ),
                        ),
                        ft.Text(
                            "KESHAV AI",
                            size=17,
                            weight=ft.FontWeight.BOLD,
                            color=self.theme["text_primary"],
                        ),
                    ],
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    icon_size=20,
                    tooltip="Settings",
                    icon_color=self.theme["text_secondary"],
                    on_click=lambda _: self.on_open_settings(),
                ),
            ],
        )

        # ChatGPT-Style "New Chat" Button
        new_chat_btn = ft.Container(
            on_click=lambda _: self.on_new_chat(),
            padding=ft.Padding(12, 9, 12, 9),
            border_radius=10,
            bgcolor=self.theme["surface_variant"],
            border=ft.Border.all(1, self.theme["border"]),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.ADD_ROUNDED, size=16, color=self.theme["text_primary"]),
                            ft.Text("New chat", size=13.5, weight=ft.FontWeight.W_500, color=self.theme["text_primary"]),
                        ],
                    ),
                    ft.Icon(ft.Icons.EDIT_OUTLINED, size=15, color=self.theme["text_muted"]),
                ],
            ),
        )

        # ChatGPT-Style User Profile Bar at bottom
        user_profile_bar = ft.Container(
            padding=ft.Padding(8, 8, 8, 8),
            border_radius=12,
            border=ft.Border(top=ft.BorderSide(1, self.theme["border"])),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        expand=True,
                        url="https://github.com/keshavbatra2003",
                        tooltip="View Keshav Batra on GitHub (github.com/keshavbatra2003)",
                        ink=True,
                        border_radius=8,
                        padding=ft.Padding(4, 4, 4, 4),
                        content=ft.Row(
                            spacing=9,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=32,
                                    height=32,
                                    border_radius=16,
                                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                    border=ft.Border.all(1, "#383838" if self.is_dark else "#CCCCCC"),
                                    bgcolor="#000000",
                                    content=ft.Image(
                                        src="/logo.png",
                                        width=32,
                                        height=32,
                                        fit=ft.BoxFit.COVER,
                                    ),
                                ),
                                ft.Column(
                                    spacing=1,
                                    tight=True,
                                    controls=[
                                        ft.Row(
                                            spacing=4,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Text("Keshav Batra", size=13, weight=ft.FontWeight.W_600, color=self.theme["text_primary"]),
                                                ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, size=11, color=self.theme["text_muted"]),
                                            ],
                                        ),
                                        ft.Text("Developer • GitHub", size=11, color=self.theme["text_muted"]),
                                    ],
                                ),
                            ],
                        ),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,
                        icon_size=18,
                        icon_color=self.theme["text_muted"],
                        tooltip="Settings",
                        on_click=lambda _: self.on_open_settings(),
                    ),
                ],
            ),
        )

        self.content = ft.Column(
            expand=True,
            spacing=12,
            controls=[
                brand_row,
                new_chat_btn,
                self.search_input,
                ft.Text(
                    "CHATS",
                    size=10.5,
                    weight=ft.FontWeight.BOLD,
                    color=self.theme["text_muted"],
                ),
                self.session_list_view,
                user_profile_bar,
            ],
        )

    def _on_search_change(self, e):
        self.search_query = e.control.value.lower().strip()
        self.refresh_sessions()

    def set_current_session(self, session_id: str):
        self.current_session_id = session_id
        self.refresh_sessions()

    def refresh_sessions(self):
        if self.search_query:
            sessions = database.search_sessions(self.search_query, client_id=self.client_id)
        else:
            sessions = database.get_sessions(client_id=self.client_id)
        self.session_list_view.controls.clear()

        if not sessions:
            self.session_list_view.controls.append(
                ft.Container(
                    padding=ft.Padding(0, 24, 0, 0),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        f"No chats matching '{self.search_query}'" if self.search_query else "No past chats yet",
                        size=12,
                        color=self.theme["text_muted"],
                        italic=True,
                    ),
                )
            )
        else:
            for s in sessions:
                is_active = (s["id"] == self.current_session_id)
                msg_count = s.get("message_count", 0)

                # Format time
                updated_at = s.get("updated_at", "")
                date_part = updated_at.split("T")[0] if "T" in updated_at else ""

                item_container = ft.Container(
                    padding=ft.Padding(10, 8, 8, 8),
                    border_radius=10,
                    bgcolor=self.theme["surface_active"] if is_active else "transparent",
                    border=ft.Border.all(
                        width=1,
                        color=self.theme["primary"] if is_active else "transparent",
                    ),
                    on_click=lambda _, sid=s["id"]: self.on_select_session(sid),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED if not is_active else ft.Icons.CHAT_BUBBLE_ROUNDED,
                                        size=16,
                                        color=self.theme["primary"] if is_active else self.theme["text_secondary"],
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(
                                                s["title"],
                                                size=13,
                                                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                                                color=self.theme["text_primary"],
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                            ft.Text(
                                                f"{msg_count} msgs • {date_part}",
                                                size=10.5,
                                                color=self.theme["text_muted"],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                icon_size=16,
                                icon_color=self.theme["text_muted"],
                                tooltip="Delete chat",
                                on_click=lambda _, sid=s["id"]: self._confirm_delete(sid),
                            ),
                        ],
                    ),
                )
                self.session_list_view.controls.append(item_container)

        try:
            self.update()
        except RuntimeError:
            pass

    def _confirm_delete(self, session_id: str):
        self.on_delete_session(session_id)
