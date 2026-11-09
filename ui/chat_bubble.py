"""
Chat message bubble components supporting User (with attachments), Assistant
(Markdown + syntax highlighting + Read Aloud TTS), and real-time streaming state.
"""

from typing import Callable, List, Optional
import flet as ft
from theme import get_theme_colors


class AssistantBubble(ft.Row):
    """Assistant message bubble with in-place streaming updates, TTS narration, and markdown code highlighting."""

    def __init__(
        self,
        content: str,
        timestamp: str,
        is_dark: bool,
        on_copy: Optional[Callable[[str], None]] = None,
        on_speak: Optional[Callable[[str], None]] = None,
        model_name: Optional[str] = None,
    ):
        super().__init__()
        self.content_text = content
        self.timestamp = timestamp
        self.is_dark = is_dark
        self.on_copy = on_copy
        self.on_speak = on_speak
        self.model_name = model_name

        self.alignment = ft.MainAxisAlignment.START
        self.vertical_alignment = ft.CrossAxisAlignment.START

        self.update_colors()
        self._build_bubble()

    def update_colors(self):
        self.theme = get_theme_colors(self.is_dark)

    def _build_bubble(self):
        time_str = self.timestamp.split("T")[-1][:5] if "T" in self.timestamp else self.timestamp

        action_controls = [
            ft.Text(
                time_str,
                size=10.5,
                color=self.theme["text_muted"],
            ),
        ]

        if self.model_name:
            action_controls.insert(
                0,
                ft.Container(
                    padding=ft.Padding(6, 2, 6, 2),
                    border_radius=6,
                    bgcolor=self.theme["badge_bg"],
                    content=ft.Text(
                        self.model_name,
                        size=10,
                        weight=ft.FontWeight.W_600,
                        color=self.theme["badge_text"],
                    ),
                ),
            )

        # Read Aloud (TTS) Button
        if self.on_speak:
            action_controls.append(
                ft.IconButton(
                    icon=ft.Icons.VOLUME_UP_ROUNDED,
                    icon_size=15,
                    tooltip="Read aloud (Voice)",
                    style=ft.ButtonStyle(
                        color=self.theme["text_muted"],
                        padding=2,
                    ),
                    on_click=lambda _: self.on_speak(self.content_text),
                )
            )

        # Copy to Clipboard Button
        if self.on_copy:
            action_controls.append(
                ft.IconButton(
                    icon=ft.Icons.COPY_ROUNDED,
                    icon_size=15,
                    tooltip="Copy message",
                    style=ft.ButtonStyle(
                        color=self.theme["text_muted"],
                        padding=2,
                    ),
                    on_click=lambda _: self.on_copy(self.content_text),
                )
            )

        self.markdown_control = ft.Markdown(
            value=self.content_text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK if self.is_dark else ft.MarkdownCodeTheme.A11Y_LIGHT,
        )

        avatar = ft.Container(
            width=34,
            height=34,
            border_radius=17,
            gradient=ft.LinearGradient(
                colors=[self.theme["primary_gradient_start"], self.theme["primary_gradient_end"]],
            ),
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=18, color="#FFFFFF"),
        )

        bubble_container = ft.Container(
            expand=True,
            padding=ft.Padding(14, 12, 14, 10),
            bgcolor=self.theme["assistant_bubble"],
            border=ft.Border.all(width=1, color=self.theme["border"]),
            border_radius=ft.BorderRadius(
                top_left=4,
                top_right=18,
                bottom_left=18,
                bottom_right=18,
            ),
            content=ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    self.markdown_control,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=action_controls,
                    ),
                ],
            ),
        )

        self.controls = [avatar, bubble_container]

    def set_content(self, new_text: str):
        """Updates the markdown text in real-time during streaming."""
        self.content_text = new_text
        self.markdown_control.value = new_text
        try:
            self.markdown_control.update()
        except RuntimeError:
            pass


def create_user_bubble(
    content: str,
    timestamp: str,
    is_dark: bool,
    attachments: Optional[List[str]] = None,
    message_id: Optional[str] = None,
    on_edit: Optional[Callable[[str, str], None]] = None,
    on_copy: Optional[Callable[[str], None]] = None,
) -> ft.Control:
    theme = get_theme_colors(is_dark)
    time_str = timestamp.split("T")[-1][:5] if "T" in timestamp else timestamp

    column_controls = []

    # If there are attached files, render attachment badges above the message
    if attachments:
        attachment_badges = []
        for att_name in attachments:
            badge = ft.Container(
                padding=ft.Padding(6, 3, 8, 3),
                border_radius=8,
                bgcolor="#312E81",
                border=ft.Border.all(1, "#4338CA"),
                content=ft.Row(
                    tight=True,
                    spacing=4,
                    controls=[
                        ft.Icon(ft.Icons.ATTACH_FILE_ROUNDED, size=13, color="#C7D2FE"),
                        ft.Text(att_name, size=11, color="#E0E7FF", weight=ft.FontWeight.W_500),
                    ],
                ),
            )
            attachment_badges.append(badge)

        column_controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                wrap=True,
                spacing=6,
                controls=attachment_badges,
            )
        )

    footer_controls = [
        ft.Text(
            time_str,
            size=10.5,
            color="#E0E7FF",
        ),
    ]

    if on_edit and message_id:
        footer_controls.append(
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=13,
                tooltip="Edit prompt",
                style=ft.ButtonStyle(
                    color="#E0E7FF",
                    padding=0,
                ),
                on_click=lambda _, mid=message_id, c=content: on_edit(mid, c),
            )
        )

    if on_copy:
        footer_controls.append(
            ft.IconButton(
                icon=ft.Icons.COPY_ROUNDED,
                icon_size=13,
                tooltip="Copy message",
                style=ft.ButtonStyle(
                    color="#E0E7FF",
                    padding=0,
                ),
                on_click=lambda _, c=content: on_copy(c),
            )
        )

    column_controls.extend([
        ft.Text(
            content,
            color=theme["user_text"],
            size=14.5,
            selectable=True,
            weight=ft.FontWeight.W_400,
        ),
        ft.Row(
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
            controls=footer_controls,
        ),
    ])

    user_bubble_container = ft.Container(
        padding=ft.Padding(14, 12, 14, 10),
        gradient=ft.LinearGradient(
            colors=[theme["primary_gradient_start"], theme["primary_gradient_end"]],
            begin=ft.Alignment(-1, 0),
            end=ft.Alignment(1, 0),
        ),
        border_radius=ft.BorderRadius(
            top_left=18,
            top_right=4,
            bottom_left=18,
            bottom_right=18,
        ),
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.END,
            controls=column_controls,
        ),
    )

    avatar = ft.Container(
        width=34,
        height=34,
        border_radius=17,
        bgcolor=theme["surface_variant"],
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.PERSON_ROUNDED, size=18, color=theme["text_primary"]),
    )

    return ft.Row(
        alignment=ft.MainAxisAlignment.END,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.Alignment(1, 0),
                content=user_bubble_container,
            ),
            avatar,
        ],
    )


def create_assistant_bubble(
    content: str,
    timestamp: str,
    is_dark: bool,
    on_copy: Optional[Callable[[str], None]] = None,
    on_speak: Optional[Callable[[str], None]] = None,
    model_name: Optional[str] = None,
) -> ft.Control:
    return AssistantBubble(
        content=content,
        timestamp=timestamp,
        is_dark=is_dark,
        on_copy=on_copy,
        on_speak=on_speak,
        model_name=model_name,
    )


def create_thinking_bubble(is_dark: bool) -> ft.Control:
    theme = get_theme_colors(is_dark)

    return ft.Row(
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Container(
                width=34,
                height=34,
                border_radius=17,
                gradient=ft.LinearGradient(
                    colors=[theme["primary_gradient_start"], theme["primary_gradient_end"]],
                ),
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=18, color="#FFFFFF"),
            ),
            ft.Container(
                padding=ft.Padding(16, 12, 16, 12),
                bgcolor=theme["assistant_bubble"],
                border=ft.Border.all(width=1, color=theme["border"]),
                border_radius=ft.BorderRadius(
                    top_left=4,
                    top_right=18,
                    bottom_left=18,
                    bottom_right=18,
                ),
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.ProgressRing(
                            width=14,
                            height=14,
                            stroke_width=2.2,
                            color=theme["primary"],
                        ),
                        ft.Text(
                            "KESHAV AI is thinking...",
                            size=13,
                            color=theme["text_secondary"],
                            italic=True,
                        ),
                    ],
                ),
            ),
        ],
    )
