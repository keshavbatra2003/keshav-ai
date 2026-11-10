"""
Main chat conversation view: real-time streaming, file & document attachments,
voice dictation (STT), voice narration (TTS), interactive prompt suggestions,
and chat exporting.
"""

import asyncio
from datetime import datetime
import os
from typing import Callable, Dict, List, Optional
import flet as ft
import ai_service
import database
from theme import get_theme_colors
from ui.chat_bubble import (
    AssistantBubble,
    create_assistant_bubble,
    create_thinking_bubble,
    create_user_bubble,
)
from voice_service import voice_service

SUGGESTED_PROMPTS = [
    ("🎨 AI Image: Cyberpunk City", "/image futuristic cyberpunk neon city in rain 4k photorealistic"),
    ("🎨 AI Image: Cute Baby Panda", "/image adorable fluffy baby panda drinking milk in bamboo forest"),
    ("💡 Explain Quantum Computing", "Explain the basics of quantum computing in simple bullet points."),
    ("💻 Python FastAPI App", "Write a clean, production-ready Python FastAPI boilerplate with health check and CRUD endpoints."),
    ("📝 Draft Professional Email", "Draft a polite and concise email declining a meeting invite due to a schedule conflict."),
    ("🧠 5 Startup Ideas", "Brainstorm 5 innovative startup ideas for 2026 leveraging AI agents and local-first software."),
]


class ChatView(ft.Container):
    def __init__(
        self,
        page: ft.Page,
        session_id: str,
        is_dark: bool,
        is_mobile: bool,
        on_toggle_drawer: Optional[Callable[[], None]] = None,
        on_session_title_changed: Optional[Callable[[str, str], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_new_chat: Optional[Callable[[], None]] = None,
        client_id: str = "default",
    ):
        super().__init__()
        self.app_page = page
        self.session_id = session_id
        self.is_dark = is_dark
        self.is_mobile = is_mobile
        self.on_toggle_drawer = on_toggle_drawer
        self.on_session_title_changed = on_session_title_changed
        self.on_open_settings = on_open_settings
        self.on_new_chat = on_new_chat
        self.client_id = client_id
        self.is_generating = False
        self.attached_files: List[Dict[str, str]] = []

        self.expand = True
        self.update_colors()

        # Services (attached to page.services, NOT page.overlay)
        self.clipboard = ft.Clipboard()
        self.file_picker = ft.FilePicker(on_result=self._on_files_selected)
        if hasattr(self.app_page, "services"):
            self.app_page.services.append(self.clipboard)
            self.app_page.services.append(self.file_picker)

        # UI Components
        self._init_controls()
        self._build_layout()
        self.load_session(self.session_id)

    def update_colors(self):
        self.theme = get_theme_colors(self.is_dark)
        self.bgcolor = self.theme["bg"]

    def set_dark_mode(self, is_dark: bool):
        self.is_dark = is_dark
        self.update_colors()
        self.header_title.color = self.theme["text_primary"]
        self.text_input.bgcolor = self.theme["input_bg"]
        self.text_input.color = self.theme["text_primary"]
        self.text_input.hint_style = ft.TextStyle(size=14, color=self.theme["text_muted"])
        self.input_card.bgcolor = self.theme["input_bg"]
        self.input_card.border = ft.Border.all(1, self.theme["border"])
        self.send_btn.bgcolor = "#FFFFFF" if is_dark else "#000000"
        self.send_icon.color = "#000000" if is_dark else "#FFFFFF"
        self.send_spinner.color = "#000000" if is_dark else "#FFFFFF"
        if hasattr(self, "footer_disclaimer"):
            self.footer_disclaimer.color = self.theme["text_muted"]
        self.header_container.bgcolor = self.theme["surface"]
        self.header_container.border = ft.Border(
            bottom=ft.BorderSide(1, self.theme["border"])
        )
        self.load_session(self.session_id)

    def set_mobile_mode(self, is_mobile: bool):
        self.is_mobile = is_mobile
        self.menu_btn.visible = is_mobile
        self.header_title.visible = not is_mobile
        self.rename_btn.visible = not is_mobile
        self.export_btn.visible = not is_mobile
        self.new_chat_btn.visible = True
        self.messages_list.padding = ft.Padding(8, 12, 8, 12) if is_mobile else ft.Padding(16, 20, 16, 20)
        if hasattr(self, "input_wrapper"):
            self.input_wrapper.padding = ft.Padding(8, 4, 8, 8) if is_mobile else ft.Padding(16, 8, 16, 14)
        self.update_model_badge()
        try:
            self.header_container.update()
            self.update()
        except RuntimeError:
            pass

    def _init_controls(self):
        # Header title
        self.header_title = ft.Text(
            "New Chat",
            size=16,
            weight=ft.FontWeight.W_600,
            color=self.theme["text_primary"],
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            visible=not self.is_mobile,
            expand=True,
        )

        # Model badge
        self.model_badge_text = ft.Text(
            "Demo Mode",
            size=11,
            weight=ft.FontWeight.W_600,
            color=self.theme["badge_text"],
        )
        self.model_badge = ft.Container(
            padding=ft.Padding(10, 5, 10, 5),
            border_radius=14,
            bgcolor=self.theme["surface_variant"],
            border=ft.Border.all(1, self.theme["border"]),
            content=self.model_badge_text,
            tooltip="Click to switch AI Model (Gemini, ChatGPT)",
            on_click=lambda _: self._open_quick_model_switcher(),
        )

        # Menu button (for mobile drawer)
        self.menu_btn = ft.IconButton(
            icon=ft.Icons.MENU_ROUNDED,
            icon_size=22,
            icon_color=self.theme["text_primary"],
            visible=self.is_mobile,
            tooltip="Open History & Settings",
            on_click=lambda _: self.on_toggle_drawer() if self.on_toggle_drawer else None,
        )

        # New Chat button: prominent pill button on phone & laptop
        self.new_chat_btn = ft.Container(
            padding=ft.Padding(10, 6, 12, 6),
            border_radius=16,
            gradient=ft.LinearGradient(
                colors=[self.theme["primary_gradient_start"], self.theme["primary_gradient_end"]],
            ),
            content=ft.Row(
                spacing=5,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.ADD_ROUNDED, size=16, color="#FFFFFF"),
                    ft.Text("New Chat", size=12.5, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ],
            ),
            tooltip="Start New Chat",
            on_click=lambda _: self._trigger_new_chat(),
        )

        # Rename session button
        self.rename_btn = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=17,
            icon_color=self.theme["text_secondary"],
            visible=not self.is_mobile,
            tooltip="Rename Chat",
            on_click=lambda _: self._open_rename_dialog(),
        )

        # Share AI link button (WhatsApp / Clipboard)
        self.share_btn = ft.IconButton(
            icon=ft.Icons.SHARE_ROUNDED,
            icon_size=18,
            icon_color=self.theme["accent"],
            tooltip="Share Link (WhatsApp / Clipboard)",
            on_click=lambda _: self._open_share_dialog(),
        )

        # Export session button
        self.export_btn = ft.IconButton(
            icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
            icon_size=18,
            icon_color=self.theme["text_secondary"],
            visible=not self.is_mobile,
            tooltip="Export Conversation (Markdown)",
            on_click=lambda _: self.export_conversation(),
        )

        # Clear session messages button
        self.clear_btn = ft.IconButton(
            icon=ft.Icons.CLEANING_SERVICES_ROUNDED,
            icon_size=18,
            icon_color=self.theme["text_secondary"],
            tooltip="Clear Chat Messages",
            on_click=lambda _: self._confirm_clear_chat(),
        )

        # Message List View
        self.messages_list = ft.ListView(
            expand=True,
            spacing=14,
            padding=ft.Padding(8, 12, 8, 12) if self.is_mobile else ft.Padding(16, 20, 16, 20),
            auto_scroll=True,
        )

        # Attachment chips row (appears above input field when files attached)
        self.attachment_chips_row = ft.Row(
            wrap=True,
            spacing=8,
            controls=[],
        )
        self.attachment_container = ft.Container(
            padding=ft.Padding(10, 4, 10, 4),
            visible=False,
            content=self.attachment_chips_row,
        )

        # Attach file button (using PickFiles client action for web & desktop compatibility)
        self.attach_btn = ft.IconButton(
            icon=ft.Icons.ADD_ROUNDED,
            icon_size=20,
            icon_color=self.theme["text_secondary"],
            tooltip="Attach Code or Document",
            action=ft.PickFiles(
                self.file_picker,
                allow_multiple=True,
                with_data=True,
                allowed_extensions=["py", "txt", "md", "json", "js", "ts", "html", "css", "yaml", "yml", "csv", "sql", "sh"],
            ),
        )

        # Inline Voice Dictation Controller
        self.is_voice_dictating = False

        sample_voice_prompts = [
            ("💡 Explain concept", "Explain the concept of "),
            ("📝 Draft email", "Draft a professional email regarding "),
            ("💻 Write Python code", "Write clean Python code for "),
            ("🔍 Top recommendations", "Give me the top 5 recommendations for "),
        ]

        voice_chips = []
        for label, prompt_text in sample_voice_prompts:
            chip = ft.Chip(
                label=ft.Text(label, size=11),
                on_click=lambda _, p=prompt_text: self._insert_dictated_text(p),
            )
            voice_chips.append(chip)

        self.inline_voice_bar = ft.Container(
            visible=False,
            padding=ft.Padding(10, 8, 10, 8),
            bgcolor=self.theme["surface_variant"],
            border=ft.Border.all(1, self.theme["primary"]),
            border_radius=12,
            content=ft.Column(
                tight=True,
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.MIC_ROUNDED, size=16, color=self.theme["primary"]),
                                    ft.Text(
                                        "🎙️ Voice Typing: Tap your keyboard mic or choose a quick prompt:",
                                        size=11.5,
                                        weight=ft.FontWeight.W_600,
                                        color=self.theme["text_primary"],
                                    ),
                                ],
                            ),
                            ft.TextButton(
                                "Close",
                                style=ft.ButtonStyle(color=self.theme["primary"], padding=2),
                                on_click=lambda _: self._toggle_inline_voice(force_off=True),
                            ),
                        ],
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=6,
                        controls=voice_chips,
                    ),
                    ft.Text(
                        "📱 Phone Tip: Tap the prompt box and press the 🎙️ mic key on your keyboard to speak with 100% accuracy!",
                        size=11,
                        color=self.theme["primary"],
                        weight=ft.FontWeight.W_500,
                    ),
                ],
            ),
        )

        # AI Image Generation button
        self.image_btn = ft.IconButton(
            icon=ft.Icons.PALETTE_ROUNDED,
            icon_size=20,
            icon_color=self.theme["text_secondary"],
            tooltip="Generate AI Image with FLUX.1 (/image)",
            on_click=self._on_image_btn_click,
        )

        # Microphone / Real Voice Dictation button
        self.voice_btn = ft.IconButton(
            icon=ft.Icons.MIC_ROUNDED,
            icon_size=20,
            icon_color=self.theme["text_secondary"],
            tooltip="Voice Dictation (Speech-to-Text)",
            url=f"/dictate?session_id={self.session_id}",
        )

        # Bottom text input (ChatGPT style)
        self.text_input = ft.TextField(
            hint_text="Message KESHAV AI...",
            hint_style=ft.TextStyle(size=14, color=self.theme["text_muted"]),
            multiline=True,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            expand=True,
            border=ft.NoInputBorder(),
            color=self.theme["text_primary"],
            on_submit=lambda _: self.send_message(),
        )

        # ChatGPT Circular Send Button
        self.send_icon = ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, size=18, color="#000000" if self.is_dark else "#FFFFFF")
        self.send_spinner = ft.ProgressRing(width=16, height=16, stroke_width=2.2, color="#000000" if self.is_dark else "#FFFFFF", visible=False)

        self.send_btn = ft.Container(
            width=34,
            height=34,
            border_radius=17,
            bgcolor="#FFFFFF" if self.is_dark else "#000000",
            alignment=ft.Alignment(0, 0),
            content=ft.Stack(
                alignment=ft.Alignment(0, 0),
                controls=[self.send_icon, self.send_spinner],
            ),
            on_click=lambda _: self.send_message(),
            tooltip="Send Message",
        )

    def _build_layout(self):
        # Header Container
        self.header_container = ft.Container(
            height=60,
            padding=ft.Padding(12, 8, 16, 8),
            bgcolor=self.theme["surface"],
            border=ft.Border(bottom=ft.BorderSide(1, self.theme["border"])),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.menu_btn,
                            self.new_chat_btn,
                            self.header_title,
                            self.rename_btn,
                        ],
                    ),
                    ft.Row(
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.model_badge,
                            self.share_btn,
                            self.export_btn,
                            self.clear_btn,
                        ],
                    ),
                ],
            ),
        )

        # ChatGPT Floating Input Capsule
        self.input_card = ft.Container(
            padding=ft.Padding(10, 6, 10, 6),
            bgcolor=self.theme["input_bg"],
            border=ft.Border.all(1, self.theme["border"]),
            border_radius=28,
            shadow=ft.BoxShadow(
                blur_radius=16,
                spread_radius=0,
                color="rgba(0,0,0,0.25)" if self.is_dark else "rgba(0,0,0,0.06)",
            ),
            content=ft.Column(
                tight=True,
                spacing=4,
                controls=[
                    self.attachment_container,
                    self.inline_voice_bar,
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        controls=[
                            self.attach_btn,
                            self.image_btn,
                            self.voice_btn,
                            self.text_input,
                            self.send_btn,
                        ],
                    ),
                ],
            ),
        )

        # ChatGPT Footer Disclaimer
        self.footer_disclaimer = ft.Text(
            spans=[
                ft.TextSpan("KESHAV AI can make mistakes. Check important info. • Developed by "),
                ft.TextSpan(
                    "Keshav Batra",
                    url="https://github.com/keshavbatra2003",
                    style=ft.TextStyle(
                        decoration=ft.TextDecoration.UNDERLINE,
                        color=self.theme["text_primary"],
                    ),
                ),
            ],
            size=11,
            color=self.theme["text_muted"],
            text_align=ft.TextAlign.CENTER,
        )

        # Input Wrapper with max width constraint for laptop/desktop
        self.input_wrapper = ft.Container(
            padding=ft.Padding(8, 4, 8, 8) if self.is_mobile else ft.Padding(16, 6, 16, 12),
            alignment=ft.Alignment(0, 0),
            content=ft.Container(
                max_width=780,
                content=ft.Column(
                    tight=True,
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.input_card,
                        self.footer_disclaimer,
                    ],
                ),
            ),
        )

        self.content = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self.header_container,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Container(
                        max_width=860,
                        expand=True,
                        content=self.messages_list,
                    ),
                ),
                self.input_wrapper,
            ],
        )

    def _open_file_picker(self):
        async def _pick():
            try:
                await self.file_picker.pick_files(
                    dialog_title="Attach PDF, Document, Code, or Notes",
                    allow_multiple=True,
                    with_data=True,
                    allowed_extensions=[
                        "pdf", "docx", "txt", "md", "py", "json", "js", "ts",
                        "html", "css", "yaml", "yml", "csv", "sql", "sh", "xml", "log"
                    ],
                )
            except Exception as err:
                print("File picker error:", err)

        asyncio.create_task(_pick())

    def _on_files_selected(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        for f in e.files:
            name = getattr(f, "name", "file")
            content_text = ""
            size_kb = 0
            is_pdf = name.lower().endswith(".pdf")

            # Handle PDF extraction with pypdf
            if is_pdf:
                try:
                    import io
                    import pypdf
                    pdf_stream = None
                    if hasattr(f, "bytes") and f.bytes:
                        pdf_stream = io.BytesIO(f.bytes)
                        size_kb = round(len(f.bytes) / 1024, 1)
                    elif hasattr(f, "path") and f.path and os.path.exists(f.path):
                        pdf_stream = open(f.path, "rb")
                        size_kb = round(os.path.getsize(f.path) / 1024, 1)

                    if pdf_stream:
                        reader = pypdf.PdfReader(pdf_stream)
                        pages_text = []
                        for p_idx, page in enumerate(reader.pages):
                            p_txt = page.extract_text()
                            if p_txt and p_txt.strip():
                                pages_text.append(f"--- Page {p_idx + 1} ---\n{p_txt.strip()}")
                        content_text = "\n\n".join(pages_text) if pages_text else "[Empty or scanned PDF document]"
                        if hasattr(pdf_stream, "close") and not isinstance(pdf_stream, io.BytesIO):
                            pdf_stream.close()
                except Exception as pdf_err:
                    content_text = f"[PDF Extraction Error: {pdf_err}]"

            # Handle text/code files
            elif hasattr(f, "bytes") and f.bytes:
                try:
                    content_text = f.bytes.decode("utf-8", errors="ignore")
                except Exception:
                    content_text = str(f.bytes)
                size_kb = round(len(f.bytes) / 1024, 1)
            elif hasattr(f, "path") and f.path and os.path.exists(f.path):
                try:
                    with open(f.path, "r", encoding="utf-8", errors="ignore") as file_obj:
                        content_text = file_obj.read()
                    size_kb = round(os.path.getsize(f.path) / 1024, 1)
                    if not name:
                        name = os.path.basename(f.path)
                except Exception as read_err:
                    print("Error reading file:", read_err)

            # Limit text size to 30,000 chars for optimal model context
            if len(content_text) > 30000:
                content_text = content_text[:30000] + "\n\n[Document truncated to first 30,000 characters for optimal AI reasoning]"

            self.attached_files.append({
                "name": name,
                "content": content_text,
                "size_str": f"{size_kb} KB",
                "is_pdf": is_pdf,
            })

        self._refresh_attachment_chips()

    def _refresh_attachment_chips(self):
        self.attachment_chips_row.controls.clear()
        if not self.attached_files:
            self.attachment_container.visible = False
        else:
            self.attachment_container.visible = True
            for i, att in enumerate(self.attached_files):
                chip = ft.Container(
                    padding=ft.Padding(8, 4, 6, 4),
                    border_radius=8,
                    bgcolor=self.theme["surface_variant"],
                    border=ft.Border.all(1, self.theme["border"]),
                    content=ft.Row(
                        tight=True,
                        spacing=6,
                        controls=[
                            ft.Icon(
                                ft.Icons.PICTURE_AS_PDF_ROUNDED if att.get("is_pdf") else (
                                    ft.Icons.CODE_ROUNDED if att["name"].endswith((".py", ".js", ".ts", ".html")) else ft.Icons.DESCRIPTION_OUTLINED
                                ),
                                size=15,
                                color="#EF4444" if att.get("is_pdf") else self.theme["primary"],
                            ),
                            ft.Text(f"{att['name']} ({att['size_str']})", size=11.5, color=self.theme["text_primary"]),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_size=13,
                                icon_color=self.theme["text_muted"],
                                tooltip="Remove attachment",
                                on_click=lambda _, idx=i: self._remove_attachment(idx),
                            ),
                        ],
                    ),
                )
                self.attachment_chips_row.controls.append(chip)

        try:
            self.input_card.update()
        except RuntimeError:
            pass

    def _trigger_new_chat(self):
        """Starts a fresh new chat session."""
        if self.on_new_chat:
            self.on_new_chat()
        else:
            new_id = database.create_session(title="New Chat", client_id=self.client_id)
            self.load_session(new_id)

    def _on_image_btn_click(self, _):
        """Quickly prefixes the prompt input with /image for FLUX.1 generation."""
        current = (self.text_input.value or "").strip()
        if not current.startswith("/image"):
            if current:
                self.text_input.value = f"/image {current} "
            else:
                self.text_input.value = "/image "
        try:
            self.text_input.update()
            self.app_page.run_task(self.text_input.focus)
        except Exception:
            pass

    def _toggle_inline_voice(self, force_off: bool = False):
        """Activates or stops inline voice dictation directly inside chat bar."""
        if force_off:
            self.is_voice_dictating = False
        else:
            self.is_voice_dictating = not self.is_voice_dictating

        self.inline_voice_bar.visible = self.is_voice_dictating

        if self.is_voice_dictating:
            self.voice_btn.icon_color = self.theme["primary"]
            self.voice_btn.tooltip = "Voice Prompts & Dictation Active"
            self.text_input.hint_text = "🎙️ Tap the mic on your keyboard to dictate..."
            try:
                self.app_page.run_task(self.text_input.focus)
            except Exception:
                pass
            if self.is_mobile:
                try:
                    self.app_page.show_dialog(
                        ft.SnackBar(
                            content=ft.Text("🎙️ Tap the mic (🎙️) on your keyboard to speak live into the box!"),
                            duration=3000,
                        )
                    )
                except Exception:
                    pass
        else:
            self.voice_btn.icon_color = self.theme["text_secondary"]
            self.voice_btn.tooltip = "Voice Dictation (Speech-to-Text)"
            self.text_input.hint_text = "Ask KESHAV AI anything... (Press Enter to send, Shift+Enter for newline)"

        try:
            self.input_card.update()
        except RuntimeError:
            pass

    def _insert_dictated_text(self, text: str):
        """Appends dictated voice phrase directly into chat input."""
        current_val = self.text_input.value or ""
        if current_val.strip():
            self.text_input.value = current_val.strip() + " " + text
        else:
            self.text_input.value = text

        try:
            self.text_input.update()
            asyncio.create_task(self.text_input.focus())
        except Exception:
            pass

    def _remove_attachment(self, index: int):
        if 0 <= index < len(self.attached_files):
            self.attached_files.pop(index)
            self._refresh_attachment_chips()

    def _open_voice_dictation_dialog(self):
        """Interactive Voice Dictation modal supporting simulated and recorded speech input."""
        transcript_input = ft.TextField(
            label="Speech Transcript",
            value="",
            hint_text="Listening... speak or tap a sample below",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border=ft.OutlineInputBorder(border_radius=10),
            expand=True,
        )

        sample_prompts = [
            "Explain binary search algorithm with Python code",
            "Draft a status update email for our cross-platform app project",
            "Compare monolithic architecture with microservices",
        ]

        sample_chips = []
        for prompt in sample_prompts:
            btn = ft.Chip(
                label=ft.Text(prompt, size=11),
                on_click=lambda _, p=prompt: self._set_dictation_text(transcript_input, p),
            )
            sample_chips.append(btn)

        pulse_ring = ft.ProgressRing(width=48, height=48, stroke_width=3, color=self.theme["primary"])

        mic_avatar = ft.Container(
            width=70,
            height=70,
            border_radius=35,
            gradient=ft.LinearGradient(
                colors=[self.theme["primary_gradient_start"], self.theme["primary_gradient_end"]],
            ),
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(ft.Icons.MIC_ROUNDED, size=36, color="#FFFFFF"),
        )

        dialog_content = ft.Container(
            width=460,
            content=ft.Column(
                tight=True,
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Stack(
                        alignment=ft.Alignment(0, 0),
                        controls=[pulse_ring, mic_avatar],
                    ),
                    ft.Text(
                        "Voice Dictation",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=self.theme["text_primary"],
                    ),
                    ft.Text(
                        "Microphone active. Speak or click a sample prompt to insert into chat.",
                        size=12,
                        color=self.theme["text_secondary"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    transcript_input,
                    ft.Text("Quick Samples:", size=11, weight=ft.FontWeight.BOLD, color=self.theme["text_muted"]),
                    ft.Column(spacing=6, controls=sample_chips),
                ],
            ),
        )

        def use_transcription(_):
            val = transcript_input.value.strip()
            if val:
                self.text_input.value = val
                try:
                    self.text_input.update()
                except RuntimeError:
                    pass
            self.app_page.pop_dialog()

        dialog = ft.AlertDialog(
            content=dialog_content,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.app_page.pop_dialog()),
                ft.FilledButton(
                    "Insert Voice Text",
                    icon=ft.Icons.CHECK_ROUNDED,
                    on_click=use_transcription,
                ),
            ],
        )
        self.app_page.show_dialog(dialog)

    def _set_dictation_text(self, text_field: ft.TextField, text: str):
        text_field.value = text
        try:
            text_field.update()
        except RuntimeError:
            pass

    def update_model_badge(self):
        settings = database.get_all_settings()
        prov = settings.get("provider", "gemini")
        if self.is_mobile:
            if prov == "gemini":
                self.model_badge_text.value = "✨ Gemini ▾"
            elif prov in ("openai", "chatgpt"):
                self.model_badge_text.value = "🟢 ChatGPT ▾"
            else:
                self.model_badge_text.value = "⚡ Demo ▾"
        else:
            if prov == "gemini":
                m = settings.get("gemini_model", "gemini-2.0-flash-lite")
                self.model_badge_text.value = f"✨ Gemini ({m}) ▾"
            elif prov in ("openai", "chatgpt"):
                m = settings.get("openai_model", "gpt-4o")
                self.model_badge_text.value = f"🟢 ChatGPT ({m}) ▾"
            else:
                self.model_badge_text.value = "⚡ Demo Engine ▾"

        try:
            self.model_badge.update()
        except RuntimeError:
            pass

    def _open_quick_model_switcher(self):
        settings = database.get_all_settings()
        curr_prov = settings.get("provider", "gemini")

        def choose_model(p: str, m: str):
            database.set_setting("provider", p)
            if p == "gemini":
                database.set_setting("gemini_model", m)
            elif p in ("openai", "chatgpt"):
                database.set_setting("openai_model", m)
            self.page.pop_dialog()
            self.update_model_badge()

        def make_model_card(title: str, subtitle: str, p: str, m: str, icon_color: str):
            is_selected = (curr_prov == p)
            return ft.Container(
                padding=ft.Padding(12, 10, 12, 10),
                border_radius=12,
                bgcolor=self.theme["surface_variant"] if is_selected else "transparent",
                border=ft.Border.all(1.5 if is_selected else 1, self.theme["primary"] if is_selected else self.theme["border"]),
                ink=True,
                on_click=lambda _: choose_model(p, m),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=10,
                                    height=10,
                                    border_radius=5,
                                    bgcolor=icon_color,
                                ),
                                ft.Column(
                                    spacing=2,
                                    tight=True,
                                    controls=[
                                        ft.Text(title, size=13.5, weight=ft.FontWeight.BOLD, color=self.theme["text_primary"]),
                                        ft.Text(subtitle, size=11, color=self.theme["text_muted"]),
                                    ],
                                ),
                            ],
                        ),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_ROUNDED if is_selected else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                            size=18,
                            color=self.theme["primary"] if is_selected else self.theme["text_muted"],
                        ),
                    ],
                ),
            )

        cards = [
            make_model_card("Google Gemini 2.0 Flash Lite", "Ultra-fast Google AI • Free Forever", "gemini", "gemini-2.0-flash-lite", "#4285F4"),
            make_model_card("Google Gemini 2.0 Flash", "Standard Google AI Model • Free Forever", "gemini", "gemini-2.0-flash", "#4285F4"),
            make_model_card("ChatGPT (GPT-4o)", "OpenAI flagship intelligence • Free & No Key Needed", "openai", "gpt-4o", "#10A37F"),
            make_model_card("ChatGPT (GPT-4o Mini)", "Lightweight, ultra-fast ChatGPT engine • Free", "openai", "gpt-4o-mini", "#10A37F"),
        ]

        dialog = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.TUNE_ROUNDED, size=20, color=self.theme["primary"]),
                    ft.Text("Switch AI Model", size=17, weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    spacing=8,
                    tight=True,
                    controls=cards,
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.page.pop_dialog()),
            ],
        )
        self.page.show_dialog(dialog)

    def load_session(self, session_id: str):
        self.session_id = session_id
        if hasattr(self, "voice_btn") and self.voice_btn:
            self.voice_btn.url = f"/dictate?session_id={session_id}"
            try:
                self.voice_btn.update()
            except RuntimeError:
                pass
        session = database.get_session(session_id)
        if not session:
            return

        self.header_title.value = session["title"]
        self.update_model_badge()
        self.render_messages()

    def render_messages(self):
        self.messages_list.controls.clear()
        messages = database.get_messages(self.session_id)

        if not messages:
            self.messages_list.controls.append(self._build_empty_state())
        else:
            settings = database.get_all_settings()
            prov = settings.get("provider", "demo")
            model_tag = "Demo"
            if prov == "gemini":
                model_tag = settings.get("gemini_model", "gemini-2.0-flash-lite")
            elif prov == "openai":
                model_tag = settings.get("openai_model", "gpt-4o-mini")

            for msg in messages:
                if msg["role"] == "user":
                    bubble = create_user_bubble(
                        content=msg["content"],
                        timestamp=msg["created_at"],
                        is_dark=self.is_dark,
                        message_id=msg.get("id"),
                        on_edit=self._open_edit_message_dialog,
                        on_copy=self._copy_to_clipboard,
                    )
                else:
                    bubble = create_assistant_bubble(
                        content=msg["content"],
                        timestamp=msg["created_at"],
                        is_dark=self.is_dark,
                        on_copy=self._copy_to_clipboard,
                        on_speak=self._speak_message,
                        model_name=model_tag,
                    )
                self.messages_list.controls.append(bubble)

        try:
            self.messages_list.update()
            self.header_title.update()
        except RuntimeError:
            pass

    def _build_empty_state(self) -> ft.Control:
        prompt_cards = [
            ("🌐 Live Web Search", "Real-time AI news & facts", "/search latest artificial intelligence breakthroughs and news in 2026"),
            ("🎨 Generate Image", "Glowing cyber-mandala in 8K", "/image futuristic glowing cyber-mandala emblem with KB initials in 8k photorealistic metallic chrome"),
            ("💻 Code Python", "High-performance cache with TTL", "Write a clean, production-ready Python in-memory cache decorator with TTL and thread safety."),
            ("📝 Executive Writing", "Partnership outreach proposal", "Draft a persuasive, professional partnership outreach email for an innovative AI collaboration."),
        ]

        card_controls = []
        for icon_title, desc, prompt_text in prompt_cards:
            card = ft.Container(
                width=250 if not self.is_mobile else None,
                padding=ft.Padding(14, 12, 14, 12),
                border_radius=14,
                bgcolor=self.theme["surface_variant"],
                border=ft.Border.all(1, self.theme["border"]),
                ink=True,
                tooltip="Click to ask instantly",
                on_click=lambda _, p=prompt_text: self._use_prompt(p, auto_send=True),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=3,
                            tight=True,
                            controls=[
                                ft.Text(icon_title, size=13, weight=ft.FontWeight.W_600, color=self.theme["text_primary"]),
                                ft.Text(desc, size=11.5, color=self.theme["text_muted"]),
                            ],
                        ),
                        ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=16, color=self.theme["text_muted"]),
                    ],
                ),
            )
            card_controls.append(card)

        return ft.Container(
            padding=ft.Padding(16, 50, 16, 30),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.Container(
                        width=68,
                        height=68,
                        border_radius=34,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        border=ft.Border.all(1.5, "#383838" if self.is_dark else "#CCCCCC"),
                        bgcolor="#000000",
                        content=ft.Image(
                            src="/logo.png",
                            width=68,
                            height=68,
                            fit=ft.BoxFit.COVER,
                        ),
                    ),
                    ft.Text(
                        "What can I help with?",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=self.theme["text_primary"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        spans=[
                            ft.TextSpan("KESHAV AI • Developed by "),
                            ft.TextSpan(
                                "Keshav Batra",
                                url="https://github.com/keshavbatra2003",
                                style=ft.TextStyle(
                                    decoration=ft.TextDecoration.UNDERLINE,
                                    color=self.theme["text_primary"],
                                ),
                            ),
                        ],
                        size=12.5,
                        color=self.theme["text_muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        wrap=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        run_spacing=10,
                        controls=card_controls,
                    ),
                ],
            ),
        )

    def _use_prompt(self, prompt: str, auto_send: bool = True):
        self.text_input.value = prompt
        try:
            self.text_input.update()
        except RuntimeError:
            pass
        if auto_send:
            self._send_message(None)
        else:
            try:
                self.app_page.run_task(self.text_input.focus)
            except Exception:
                pass

    def _copy_to_clipboard(self, text: str):
        async def _do_copy():
            try:
                await self.clipboard.set(text)
                self.app_page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Copied response to clipboard!"),
                        duration=2000,
                    )
                )
            except Exception as e:
                print("Clipboard copy error:", e)

        asyncio.create_task(_do_copy())

    def _speak_message(self, text: str):
        """Speaks the message aloud using native TTS narration."""
        if voice_service.is_speaking:
            voice_service.stop()
            self.app_page.show_dialog(
                ft.SnackBar(content=ft.Text("Speech narration stopped."), duration=1500)
            )
        else:
            self.app_page.show_dialog(
                ft.SnackBar(content=ft.Text("🔊 Reading message aloud..."), duration=2000)
            )
            asyncio.create_task(voice_service.speak_async(text))

    def send_message(self):
        text = self.text_input.value.strip()
        has_attachments = bool(self.attached_files)

        if (not text and not has_attachments) or self.is_generating:
            return

        if self.is_voice_dictating:
            self._toggle_inline_voice(force_off=True)

        self.text_input.value = ""
        try:
            self.text_input.update()
        except RuntimeError:
            pass

        # If this is an empty state, clear the welcome card
        messages = database.get_messages(self.session_id)
        if not messages:
            self.messages_list.controls.clear()

        # Auto-detect if user pasted a Gemini API key into the chat
        if (text.startswith("AIzaSy") or text.startswith("AQ.")) and len(text) >= 35:
            database.set_setting("gemini_api_key", text)
            database.set_setting("provider", "gemini")
            self.update_model_badge()

            user_msg = database.add_message(self.session_id, "user", "[Configured Gemini API Key]")
            user_bubble = create_user_bubble(
                content="Configured Gemini API Key: •••••••••••••••••••• (Key Activated & Secured)",
                timestamp=user_msg["created_at"],
                is_dark=self.is_dark,
            )
            self.messages_list.controls.append(user_bubble)

            asst_text = (
                "🎉 **Google Gemini API Key Activated!**\n\n"
                "KESHAV AI is now **100% online** and connected live to Google Gemini.\n\n"
                "You can now ask any question, attach files, or brainstorm ideas with frontier intelligence!"
            )
            asst_msg = database.add_message(self.session_id, "assistant", asst_text)
            asst_bubble = create_assistant_bubble(
                content=asst_text,
                timestamp=asst_msg["created_at"],
                is_dark=self.is_dark,
                on_copy=self._copy_to_clipboard,
                on_speak=self._speak_message,
                model_name="Gemini Online",
            )
            self.messages_list.controls.append(asst_bubble)
            try:
                self.messages_list.update()
            except RuntimeError:
                pass
            return

        # Auto-detect if user pasted an OpenAI API key into the chat
        if (text.startswith("sk-proj-") or text.startswith("sk-")) and len(text) >= 30:
            database.set_setting("openai_api_key", text)
            database.set_setting("provider", "openai")
            self.update_model_badge()

            user_msg = database.add_message(self.session_id, "user", "[Configured OpenAI API Key]")
            user_bubble = create_user_bubble(
                content="Configured OpenAI API Key: •••••••••••••••••••• (Key Activated & Secured)",
                timestamp=user_msg["created_at"],
                is_dark=self.is_dark,
            )
            self.messages_list.controls.append(user_bubble)

            asst_text = (
                "🎉 **OpenAI ChatGPT API Key Activated!**\n\n"
                "KESHAV AI is now connected to **ChatGPT (GPT-4o)**.\n\n"
                "You can now chat directly with OpenAI's flagship intelligence!"
            )
            asst_msg = database.add_message(self.session_id, "assistant", asst_text)
            asst_bubble = create_assistant_bubble(
                content=asst_text,
                timestamp=asst_msg["created_at"],
                is_dark=self.is_dark,
                on_copy=self._copy_to_clipboard,
                on_speak=self._speak_message,
                model_name="ChatGPT Online",
            )
            self.messages_list.controls.append(asst_bubble)
            try:
                self.messages_list.update()
            except RuntimeError:
                pass
            return

        # Build prompt context if files are attached
        attachment_names = []
        full_content_for_ai = text
        if has_attachments:
            attachment_snippets = []
            for att in self.attached_files:
                attachment_names.append(att["name"])
                ext = att["name"].split(".")[-1] if "." in att["name"] else ""
                snippet = f"--- File: {att['name']} ({att['size_str']}) ---\n```{ext}\n{att['content']}\n```"
                attachment_snippets.append(snippet)

            combined_files_text = "\n\n".join(attachment_snippets)
            full_content_for_ai = f"{combined_files_text}\n\n[User Prompt]:\n{text if text else 'Please review and analyze the attached files.'}"

            # Clear attachments bar
            self.attached_files = []
            self._refresh_attachment_chips()

        # Save user message
        user_msg = database.add_message(self.session_id, "user", full_content_for_ai)
        user_bubble = create_user_bubble(
            content=text if text else "Attached files for analysis",
            timestamp=user_msg["created_at"],
            is_dark=self.is_dark,
            attachments=attachment_names if attachment_names else None,
            message_id=user_msg["id"],
            on_edit=self._open_edit_message_dialog,
            on_copy=self._copy_to_clipboard,
        )
        self.messages_list.controls.append(user_bubble)

        # Auto-update session title if first user message
        if not messages:
            display_title = text if text else (attachment_names[0] if attachment_names else "New Chat")
            new_title = display_title[:36] + ("..." if len(display_title) > 36 else "")
            database.update_session_title(self.session_id, new_title)
            self.header_title.value = new_title
            try:
                self.header_title.update()
            except RuntimeError:
                pass
            if self.on_session_title_changed:
                self.on_session_title_changed(self.session_id, new_title)

        # Show Thinking indicator
        thinking_bubble = create_thinking_bubble(self.is_dark)
        self.messages_list.controls.append(thinking_bubble)
        try:
            self.messages_list.update()
        except RuntimeError:
            pass

        # Update Send button state
        self.is_generating = True
        self.send_icon.visible = False
        self.send_spinner.visible = True
        try:
            self.send_btn.update()
        except RuntimeError:
            pass

        # Trigger real-time streaming in background task
        asyncio.create_task(self._process_streaming_ai_response(thinking_bubble))

    async def _process_streaming_ai_response(self, thinking_bubble: ft.Control):
        settings = database.get_all_settings()
        history = database.get_messages(self.session_id)

        # Check if the user prompt is an AI image generation request!
        last_user_msg = ""
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "").strip()
                break

        if ai_service.is_image_request(last_user_msg):
            image_prompt = ai_service.extract_image_prompt(last_user_msg)
            image_url = ai_service.get_flux_image_url(image_prompt)
            full_text = ai_service.format_image_markdown(image_prompt, image_url)

            if thinking_bubble in self.messages_list.controls:
                self.messages_list.controls.remove(thinking_bubble)

            now_str = datetime.now().isoformat()
            assistant_bubble = AssistantBubble(
                content=full_text,
                timestamp=now_str,
                is_dark=self.is_dark,
                on_copy=self._copy_to_clipboard,
                on_speak=self._speak_message,
                model_name="FLUX.1 Image AI",
            )
            self.messages_list.controls.append(assistant_bubble)
            database.add_message(self.session_id, "assistant", full_text)
            try:
                self.messages_list.update()
            except RuntimeError:
                pass
            self.is_generating = False
            self.send_icon.visible = True
            self.send_spinner.visible = False
            try:
                self.send_btn.update()
            except RuntimeError:
                pass
            return

        prov = settings.get("provider", "demo")
        model_tag = "Demo"
        if prov == "gemini":
            model_tag = settings.get("gemini_model", "gemini-2.0-flash-lite")
            if not settings.get("gemini_api_key", "").strip():
                full_text = (
                    "⚠️ **Google Gemini API Key Needed to Go Online**\n\n"
                    "To connect KESHAV AI online using Google Gemini:\n\n"
                    "1. Open **[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** in your browser.\n"
                    "2. Sign in with Google and click **\"Create API key\"** (100% free, no credit card needed).\n"
                    "3. **Paste your key (`AIzaSy...`) right here in this chat box** or in **⚙️ Settings**!\n\n"
                    "KESHAV AI will immediately activate and start responding with live Gemini intelligence."
                )
                assistant_bubble = AssistantBubble(
                    content=full_text,
                    timestamp=datetime.now().isoformat(),
                    is_dark=self.is_dark,
                    on_copy=self._copy_to_clipboard,
                    on_speak=self._speak_message,
                    model_name="Gemini Setup",
                )
                if thinking_bubble in self.messages_list.controls:
                    self.messages_list.controls.remove(thinking_bubble)
                self.messages_list.controls.append(assistant_bubble)
                database.add_message(self.session_id, "assistant", full_text)
                try:
                    self.messages_list.update()
                except RuntimeError:
                    pass
                self.is_generating = False
                self.send_icon.visible = True
                self.send_spinner.visible = False
                try:
                    self.send_btn.update()
                except RuntimeError:
                    pass
                return
        elif prov in ("openai", "chatgpt"):
            model_tag = settings.get("openai_model", "gpt-4o")

        assistant_bubble: Optional[AssistantBubble] = None
        full_text = ""

        try:
            async for chunk in ai_service.stream_ai_response(history, settings):
                if assistant_bubble is None:
                    if thinking_bubble in self.messages_list.controls:
                        self.messages_list.controls.remove(thinking_bubble)
                    now_str = datetime.now().isoformat()
                    assistant_bubble = AssistantBubble(
                        content="",
                        timestamp=now_str,
                        is_dark=self.is_dark,
                        on_copy=self._copy_to_clipboard,
                        on_speak=self._speak_message,
                        model_name=model_tag,
                    )
                    self.messages_list.controls.append(assistant_bubble)
                    try:
                        self.messages_list.update()
                    except RuntimeError:
                        pass

                full_text = chunk
                assistant_bubble.set_content(full_text)

        except Exception as e:
            full_text = (
                f"⚠️ **Error generating response:**\n\n"
                f"`{str(e)}`\n\n"
                "Please verify your API key or network connection in **Settings**."
            )
            if assistant_bubble is None:
                if thinking_bubble in self.messages_list.controls:
                    self.messages_list.controls.remove(thinking_bubble)
                now_str = datetime.now().isoformat()
                assistant_bubble = AssistantBubble(
                    content=full_text,
                    timestamp=now_str,
                    is_dark=self.is_dark,
                    on_copy=self._copy_to_clipboard,
                    on_speak=self._speak_message,
                    model_name=model_tag,
                )
                self.messages_list.controls.append(assistant_bubble)
            else:
                assistant_bubble.set_content(full_text)

        finally:
            if thinking_bubble in self.messages_list.controls:
                self.messages_list.controls.remove(thinking_bubble)

            if full_text:
                database.add_message(self.session_id, "assistant", full_text)

            try:
                self.messages_list.update()
            except RuntimeError:
                pass

            self.is_generating = False
            self.send_icon.visible = True
            self.send_spinner.visible = False
            try:
                self.send_btn.update()
            except RuntimeError:
                pass

    def export_conversation(self):
        """Exports the active conversation to a clean Markdown file and clipboard."""
        session = database.get_session(self.session_id)
        messages = database.get_messages(self.session_id)
        if not session or not messages:
            self.app_page.show_dialog(
                ft.SnackBar(content=ft.Text("Conversation is empty - nothing to export!"), duration=2000)
            )
            return

        title = session["title"]
        lines = [
            f"# {title}",
            f"*Exported from KESHAV AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
        ]

        for msg in messages:
            role_name = "👤 **User**" if msg["role"] == "user" else "🤖 **KESHAV AI**"
            created_at = msg["created_at"].split("T")[0]
            lines.append(f"### {role_name} *({created_at})*")
            lines.append(msg["content"])
            lines.append("")
            lines.append("---")
            lines.append("")

        export_content = "\n".join(lines)

        export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"chat_{self.session_id[:8]}.md"
        file_path = os.path.join(export_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(export_content)

        async def _copy_export():
            try:
                await self.clipboard.set(export_content)
                self.app_page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Exported to exports/{filename} and copied to clipboard!"),
                        duration=3000,
                    )
                )
            except Exception as e:
                print("Clipboard export error:", e)

        asyncio.create_task(_copy_export())

    def _open_rename_dialog(self):
        current_title = self.header_title.value
        title_input = ft.TextField(
            label="Chat Title",
            value=current_title,
            autofocus=True,
            dense=True,
            border=ft.OutlineInputBorder(border_radius=10),
        )

        def save_title(_):
            val = title_input.value.strip()
            if val:
                database.update_session_title(self.session_id, val)
                self.header_title.value = val
                try:
                    self.header_title.update()
                except RuntimeError:
                    pass
                if self.on_session_title_changed:
                    self.on_session_title_changed(self.session_id, val)
            self.app_page.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("Rename Conversation", size=16, weight=ft.FontWeight.BOLD),
            content=title_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.app_page.pop_dialog()),
                ft.FilledButton("Save", on_click=save_title),
            ],
        )
        self.app_page.show_dialog(dialog)

    def _confirm_clear_chat(self):
        def do_clear(_):
            database.clear_messages(self.session_id)
            self.app_page.pop_dialog()
            self.render_messages()

        dialog = ft.AlertDialog(
            title=ft.Text("Clear Messages?", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Text("Are you sure you want to clear all messages in this conversation?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.app_page.pop_dialog()),
                ft.FilledButton("Clear", on_click=do_clear),
            ],
        )
        self.app_page.show_dialog(dialog)

    def _open_edit_message_dialog(self, message_id: str, old_content: str):
        """Allows editing a user prompt with option to regenerate AI response."""
        edit_input = ft.TextField(
            value=old_content,
            multiline=True,
            min_lines=3,
            max_lines=8,
            autofocus=True,
            border=ft.OutlineInputBorder(border_radius=10),
            expand=True,
        )

        regenerate_checkbox = ft.Checkbox(
            label="Regenerate AI response for updated message",
            value=True,
        )

        def save_and_apply(_):
            new_text = edit_input.value.strip()
            if not new_text or new_text == old_content:
                self.app_page.pop_dialog()
                return

            self.app_page.pop_dialog()

            if regenerate_checkbox.value:
                # Truncate subsequent conversation history after this message
                database.delete_messages_after(self.session_id, message_id)
                # Update message in database
                database.update_message(message_id, new_text)
                # Re-render conversation
                self.render_messages()
                # Create thinking bubble and stream AI response from Google Gemini
                thinking_bubble = create_thinking_bubble(self.is_dark)
                self.messages_list.controls.append(thinking_bubble)
                try:
                    self.messages_list.update()
                except RuntimeError:
                    pass

                self.is_generating = True
                self.send_icon.visible = False
                self.send_spinner.visible = True
                try:
                    self.send_btn.update()
                except RuntimeError:
                    pass

                asyncio.create_task(self._process_streaming_ai_response(thinking_bubble))
            else:
                # Just update the text without regenerating
                database.update_message(message_id, new_text)
                self.render_messages()

        dialog = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.EDIT_ROUNDED, color=self.theme["primary"], size=22),
                    ft.Text("Edit Message", size=18, weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Container(
                width=500,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Text(
                            "Update your prompt. You can choose to regenerate the response or simply update the text:",
                            size=12,
                            color=self.theme["text_secondary"],
                        ),
                        edit_input,
                        regenerate_checkbox,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.app_page.pop_dialog()),
                ft.FilledButton(
                    "Save & Send",
                    icon=ft.Icons.SEND_ROUNDED,
                    on_click=save_and_apply,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app_page.show_dialog(dialog)

    def _open_share_dialog(self):
        """Modal dialog displaying public shareable conversation link with social sharing buttons."""
        import urllib.parse

        share_url = f"https://keshav-ai.onrender.com/share/{self.session_id}"
        home_url = "https://keshav-ai.onrender.com"

        share_text = f"🤖 Check out this conversation on KESHAV AI by Keshav Batra: {share_url}"
        encoded_wa_text = urllib.parse.quote(share_text)
        wa_url = f"https://api.whatsapp.com/send?text={encoded_wa_text}"
        encoded_tweet = urllib.parse.quote(f"Check out this AI conversation on KESHAV AI by Keshav Batra! {share_url}")
        twitter_url = f"https://twitter.com/intent/tweet?text={encoded_tweet}"

        def copy_share_link(_):
            async def _do():
                try:
                    await self.clipboard.set(share_url)
                    self.app_page.show_dialog(
                        ft.SnackBar(content=ft.Text("✅ Conversation link copied to clipboard!"), duration=2500)
                    )
                except Exception as e:
                    print("Clipboard error:", e)
            asyncio.create_task(_do())
            self.app_page.pop_dialog()

        def copy_invite_text(_):
            async def _do():
                try:
                    await self.clipboard.set(share_text)
                    self.app_page.show_dialog(
                        ft.SnackBar(content=ft.Text("✅ WhatsApp message copied to clipboard!"), duration=2500)
                    )
                except Exception as e:
                    print("Clipboard error:", e)
            asyncio.create_task(_do())
            self.app_page.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.SHARE_ROUNDED, color=self.theme["primary"], size=22),
                    ft.Text("Share Conversation", size=18, weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Text(
                            "Anyone with this link can view this conversation with live formatted code and markdown:",
                            size=13,
                            color=self.theme["text_secondary"],
                        ),
                        # Public HTTPS Box
                        ft.Container(
                            padding=ft.Padding(12, 10, 12, 10),
                            bgcolor=self.theme["surface_variant"],
                            border=ft.Border.all(1, self.theme["primary"]),
                            border_radius=10,
                            content=ft.Column(
                                tight=True,
                                spacing=4,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Icon(ft.Icons.PUBLIC_ROUNDED, size=15, color=self.theme["primary"]),
                                            ft.Text("Public View Link", size=12, weight=ft.FontWeight.BOLD, color=self.theme["primary"]),
                                        ],
                                    ),
                                    ft.Text(
                                        share_url,
                                        selectable=True,
                                        size=12.5,
                                        weight=ft.FontWeight.W_600,
                                        color=self.theme["text_primary"],
                                    ),
                                ],
                            ),
                        ),
                        # WhatsApp & Twitter / X Buttons
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.FilledButton(
                                    "WhatsApp",
                                    icon=ft.Icons.SEND_ROUNDED,
                                    url=wa_url,
                                    expand=True,
                                    style=ft.ButtonStyle(
                                        bgcolor="#25D366",
                                        color="#FFFFFF",
                                    ),
                                ),
                                ft.FilledButton(
                                    "Share on X",
                                    icon=ft.Icons.TAG_ROUNDED,
                                    url=twitter_url,
                                    expand=True,
                                    style=ft.ButtonStyle(
                                        bgcolor="#1DA1F2",
                                        color="#FFFFFF",
                                    ),
                                ),
                            ],
                        ),
                        # Copy formatted link & invite
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.FilledTonalButton(
                                    "Copy Link",
                                    icon=ft.Icons.COPY_ROUNDED,
                                    on_click=copy_share_link,
                                    expand=True,
                                ),
                                ft.OutlinedButton(
                                    "Copy Invite Text",
                                    icon=ft.Icons.CONTENT_PASTE_ROUNDED,
                                    on_click=copy_invite_text,
                                    expand=True,
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.app_page.pop_dialog()),
            ],
        )
        self.app_page.show_dialog(dialog)
        self.app_page.show_dialog(dialog)
