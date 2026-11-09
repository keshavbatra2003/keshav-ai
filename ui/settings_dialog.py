"""
Settings modal dialog for configuring AI providers, API keys, models, system persona, and theme.
Supports Google Gemini, Groq (Free Online), OpenAI, Local Ollama, and Demo Mode.
"""

from typing import Callable, Dict
import flet as ft
import database
from theme import get_theme_colors

PERSONA_PROMPTS = {
    "Helpful Assistant": (
        "You are KESHAV AI, an intelligent, helpful, and concise AI assistant developed by Keshav Batra. "
        "Keep responses structured, informative, and engaging. Use markdown for code."
    ),
    "Code Architect": (
        "You are a Principal Software Engineer. Provide elegant, robust, type-safe, "
        "and clean code solutions with brief architectural explanations and edge case considerations."
    ),
    "Concise Analyst": (
        "You are an analytical assistant. Provide direct, bullet-pointed, data-driven "
        "responses without conversational filler. Focus purely on accuracy and actionable insights."
    ),
    "Creative Companion": (
        "You are a creative, imaginative, and articulate writing companion. "
        "Help draft engaging stories, marketing copy, brainstorms, and expressive concepts."
    ),
}


class SettingsDialog:
    def __init__(
        self,
        page: ft.Page,
        is_dark: bool,
        on_settings_saved: Callable[[Dict[str, str]], None],
    ):
        self.page = page
        self.is_dark = is_dark
        self.on_settings_saved = on_settings_saved
        self.settings = database.get_all_settings()
        self.theme = get_theme_colors(is_dark)

        self._build_controls()

    def _build_controls(self):
        current_provider = self.settings.get("provider", "demo")

        # Provider Selector
        self.provider_dropdown = ft.Dropdown(
            label="AI Inference Engine",
            value=current_provider,
            options=[
                ft.dropdown.Option("gemini", "Google Gemini API (Free Tier Recommended)"),
                ft.dropdown.Option("openai", "OpenAI / Groq / Ollama / Compatible API"),
                ft.dropdown.Option("demo", "Built-in Offline Engine (Simulated)"),
            ],
            dense=True,
            border_radius=10,
            on_select=self._on_provider_change,
        )

        # Gemini Controls
        has_gemini_key = bool(self.settings.get("gemini_api_key", "").strip())

        self.gemini_status_card = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=10,
            bgcolor=self.theme["surface_variant"],
            border=ft.Border.all(1, "#10B981" if has_gemini_key else self.theme["border"]),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(
                        ft.Icons.LOCK_ROUNDED if has_gemini_key else ft.Icons.KEY_OFF_ROUNDED,
                        color="#10B981" if has_gemini_key else self.theme["text_muted"],
                        size=20,
                    ),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(
                                "Gemini API Key: Connected & Protected" if has_gemini_key else "No Gemini API Key Configured",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=self.theme["text_primary"],
                            ),
                            ft.Text(
                                "•••••••••••••••••••• (Hidden for privacy & security)" if has_gemini_key else "Provide an API key to enable online AI",
                                size=11,
                                color="#10B981" if has_gemini_key else self.theme["text_muted"],
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.gemini_key_input = ft.TextField(
            label="Update Gemini API Key",
            value="",
            password=True,
            can_reveal_password=False,
            hint_text="Leave blank to keep current key",
            dense=True,
            border=ft.OutlineInputBorder(border_radius=10),
            helper="Current API key is securely managed on server and hidden from visitors.",
        )

        current_gemini_model = self.settings.get("gemini_model", "gemini-3.5-flash")
        if current_gemini_model.startswith("gemini-1.5") or current_gemini_model.startswith("gemini-2.5"):
            current_gemini_model = "gemini-3.5-flash"

        self.gemini_model_dropdown = ft.Dropdown(
            label="Gemini Model",
            value=current_gemini_model,
            options=[
                ft.dropdown.Option("gemini-3.5-flash", "Gemini 3.5 Flash (Fast & Recommended)"),
                ft.dropdown.Option("gemini-3.8-flash", "Gemini 3.8 Flash (Latest Intelligent)"),
                ft.dropdown.Option("gemini-flash-latest", "Gemini Flash Latest (Auto-Updated)"),
                ft.dropdown.Option("gemini-3.5-flash-lite", "Gemini 3.5 Flash Lite (Lightweight)"),
                ft.dropdown.Option("gemini-3.1-pro-preview", "Gemini 3.1 Pro (Deep Reasoning)"),
            ],
            dense=True,
            border_radius=10,
        )

        get_gemini_key_btn = ft.FilledTonalButton(
            "Get Free Gemini Key at Google AI Studio",
            icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
            url="https://aistudio.google.com/app/apikey",
        )

        self.gemini_box = ft.Column(
            spacing=10,
            visible=(current_provider == "gemini"),
            controls=[
                self.gemini_status_card,
                get_gemini_key_btn,
                self.gemini_key_input,
                self.gemini_model_dropdown,
            ],
        )

        # OpenAI / Groq / Ollama Controls
        self.openai_key_input = ft.TextField(
            label="API Key (Leave empty to keep current or for Ollama)",
            value="",
            password=True,
            can_reveal_password=False,
            hint_text="Leave blank to keep existing key",
            dense=True,
            border=ft.OutlineInputBorder(border_radius=10),
        )

        self.openai_base_url_input = ft.TextField(
            label="Base URL",
            value=self.settings.get("openai_base_url", "https://api.openai.com/v1"),
            hint_text="e.g. https://api.groq.com/openai/v1 or http://localhost:11434/v1",
            dense=True,
            border=ft.OutlineInputBorder(border_radius=10),
        )

        self.openai_model_input = ft.TextField(
            label="Model Name",
            value=self.settings.get("openai_model", "gpt-4o-mini"),
            hint_text="e.g. llama-3.3-70b-versatile, gpt-4o-mini, llama3",
            dense=True,
            border=ft.OutlineInputBorder(border_radius=10),
        )

        # Quick preset buttons for Groq, OpenAI, Ollama
        preset_chips = ft.Row(
            wrap=True,
            spacing=6,
            controls=[
                ft.Chip(
                    label=ft.Text("⚡ Groq (Free)", size=11),
                    tooltip="Free high-speed cloud Llama 3.3 70B",
                    on_click=lambda _: self._apply_openai_preset(
                        "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"
                    ),
                ),
                ft.Chip(
                    label=ft.Text("🤖 OpenAI", size=11),
                    tooltip="OpenAI GPT-4o Mini",
                    on_click=lambda _: self._apply_openai_preset(
                        "https://api.openai.com/v1", "gpt-4o-mini"
                    ),
                ),
                ft.Chip(
                    label=ft.Text("💻 Local Ollama", size=11),
                    tooltip="Run 100% locally with Ollama",
                    on_click=lambda _: self._apply_openai_preset(
                        "http://localhost:11434/v1", "llama3"
                    ),
                ),
            ],
        )

        self.openai_box = ft.Column(
            spacing=10,
            visible=(current_provider == "openai"),
            controls=[
                ft.Text("Quick Presets:", size=11, weight=ft.FontWeight.BOLD, color=self.theme["text_muted"]),
                preset_chips,
                self.openai_base_url_input,
                self.openai_key_input,
                self.openai_model_input,
            ],
        )

        # Persona / System Instructions
        saved_persona = self.settings.get("persona", "Helpful Assistant")
        self.persona_dropdown = ft.Dropdown(
            label="Assistant Persona Preset",
            value=saved_persona,
            options=[ft.dropdown.Option(k, k) for k in PERSONA_PROMPTS.keys()] + [ft.dropdown.Option("Custom", "Custom")],
            dense=True,
            border_radius=10,
            on_select=self._on_persona_change,
        )

        self.system_prompt_input = ft.TextField(
            label="System Instructions",
            value=self.settings.get("system_prompt", PERSONA_PROMPTS["Helpful Assistant"]),
            multiline=True,
            min_lines=2,
            max_lines=4,
            dense=True,
            border=ft.OutlineInputBorder(border_radius=10),
        )

        # Theme Switcher
        self.theme_switch = ft.Switch(
            label="Dark Theme Mode",
            value=(self.settings.get("theme_mode", "dark") == "dark"),
        )

    def _apply_openai_preset(self, base_url: str, model: str):
        self.openai_base_url_input.value = base_url
        self.openai_model_input.value = model
        try:
            self.openai_base_url_input.update()
            self.openai_model_input.update()
        except Exception:
            pass

    def _on_provider_change(self, e):
        prov = self.provider_dropdown.value
        self.gemini_box.visible = (prov == "gemini")
        self.openai_box.visible = (prov == "openai")
        try:
            self.dialog_content.update()
        except Exception:
            pass

    def _on_persona_change(self, e):
        preset = self.persona_dropdown.value
        if preset in PERSONA_PROMPTS:
            self.system_prompt_input.value = PERSONA_PROMPTS[preset]
            try:
                self.system_prompt_input.update()
            except Exception:
                pass

    def show(self):
        self.dialog_content = ft.Container(
            width=500,
            content=ft.Column(
                tight=True,
                spacing=16,
                scroll=ft.ScrollMode.ADAPTIVE,
                controls=[
                    ft.Text(
                        "Configure live online AI inference (Gemini, Groq, OpenAI) or local models.",
                        size=12.5,
                        color=self.theme["text_secondary"],
                    ),
                    ft.Divider(height=1, color=self.theme["border"]),
                    ft.Text("AI INFERENCE ENGINE", size=11, weight=ft.FontWeight.BOLD, color=self.theme["primary"]),
                    self.provider_dropdown,
                    self.gemini_box,
                    self.openai_box,
                    ft.Divider(height=1, color=self.theme["border"]),
                    ft.Text("PERSONA & INSTRUCTIONS", size=11, weight=ft.FontWeight.BOLD, color=self.theme["primary"]),
                    self.persona_dropdown,
                    self.system_prompt_input,
                    ft.Divider(height=1, color=self.theme["border"]),
                    ft.Text("APPEARANCE", size=11, weight=ft.FontWeight.BOLD, color=self.theme["primary"]),
                    self.theme_switch,
                    ft.Divider(height=1, color=self.theme["border"]),
                    ft.Container(
                        padding=ft.Padding(12, 10, 12, 10),
                        border_radius=10,
                        bgcolor=self.theme["surface_variant"],
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.VERIFIED_ROUNDED, size=16, color=self.theme["primary"]),
                                ft.Text(
                                    "Developer: Keshav Batra",
                                    size=12.5,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.theme["text_primary"],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

        self.dialog = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.TUNE_ROUNDED, size=22, color=self.theme["primary"]),
                    ft.Text("KESHAV AI Settings", size=18, weight=ft.FontWeight.BOLD),
                ],
            ),
            content=self.dialog_content,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close()),
                ft.FilledButton(
                    "Save & Connect",
                    icon=ft.Icons.CHECK_ROUNDED,
                    on_click=lambda _: self._save(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.show_dialog(self.dialog)

    def _close(self):
        self.page.pop_dialog()

    def _save(self):
        prov = self.provider_dropdown.value
        database.set_setting("provider", prov)

        # Only update API keys if user entered a new one, keeping existing keys secure and unchanged
        new_gemini_key = self.gemini_key_input.value.strip()
        if new_gemini_key:
            database.set_setting("gemini_api_key", new_gemini_key)

        database.set_setting("gemini_model", self.gemini_model_dropdown.value)

        new_openai_key = self.openai_key_input.value.strip()
        if new_openai_key:
            database.set_setting("openai_api_key", new_openai_key)

        database.set_setting("openai_base_url", self.openai_base_url_input.value.strip())
        database.set_setting("openai_model", self.openai_model_input.value.strip())
        database.set_setting("persona", self.persona_dropdown.value)
        database.set_setting("system_prompt", self.system_prompt_input.value.strip())

        new_theme = "dark" if self.theme_switch.value else "light"
        database.set_setting("theme_mode", new_theme)

        updated_settings = database.get_all_settings()
        self.page.pop_dialog()
        self.on_settings_saved(updated_settings)
