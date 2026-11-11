"""
Test UI components instantiation and control tree construction with attachments and voice.
"""

import os
import sys
import unittest
import flet as ft

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from ui.chat_bubble import create_assistant_bubble, create_thinking_bubble, create_user_bubble
from ui.history_drawer import HistorySidebar


class TestUIComponents(unittest.TestCase):
    def setUp(self):
        database.init_db()

    def test_bubbles_creation_with_attachments_and_speech(self):
        # User bubble with attachments
        ub = create_user_bubble(
            content="Please review this file",
            timestamp="2026-11-08T10:00:00",
            is_dark=True,
            attachments=["main.py", "schema.sql"],
        )
        self.assertIsInstance(ub, ft.Row)

        # Assistant bubble with speech callback
        spoken_text = []

        def mock_speak(t):
            spoken_text.append(t)

        ab = create_assistant_bubble(
            content="**Hi there!** Here is a snippet:\n```python\nprint(1)\n```",
            timestamp="2026-11-08T10:00:05",
            is_dark=True,
            on_speak=mock_speak,
            model_name="Gemini 1.5 Flash",
        )
        self.assertIsInstance(ab, ft.Row)

        # Thinking bubble
        tb = create_thinking_bubble(is_dark=True)
        self.assertIsInstance(tb, ft.Row)

    def test_sidebar_creation(self):
        session_id = database.get_or_create_initial_session()
        mindful_clicked = []
        sidebar = HistorySidebar(
            current_session_id=session_id,
            is_dark=True,
            on_select_session=lambda sid: None,
            on_new_chat=lambda: None,
            on_delete_session=lambda sid: None,
            on_open_settings=lambda: None,
            on_new_mindful_chat=lambda: mindful_clicked.append(True),
        )
        self.assertIsInstance(sidebar, ft.Container)
        self.assertTrue(len(sidebar.session_list_view.controls) > 0)
        sidebar.on_new_mindful_chat()
        self.assertTrue(mindful_clicked[0])

    def test_settings_dialog_instantiation(self):
        from ui.settings_dialog import SettingsDialog
        class MockPage:
            def show_dialog(self, d): pass
            def pop_dialog(self): pass
        dialog = SettingsDialog(page=MockPage(), is_dark=True, on_settings_saved=lambda s: None)
        self.assertIsNotNone(dialog.provider_dropdown)


if __name__ == "__main__":
    unittest.main()
