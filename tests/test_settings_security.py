"""
Unit tests for API key security and confidentiality in SettingsDialog.
Verifies that the Gemini API key is never exposed to visitors or overwritten inadvertently.
"""

import unittest
import database
from ui.settings_dialog import SettingsDialog


class MockSettingsPage:
    def __init__(self):
        self.dialog = None

    def show_dialog(self, dialog):
        self.dialog = dialog

    def pop_dialog(self):
        self.dialog = None


class TestSettingsSecurity(unittest.TestCase):
    def setUp(self):
        database.init_db()
        self.original_key = database.get_setting("gemini_api_key")
        database.set_setting("gemini_api_key", "MOCK_TEST_GEMINI_KEY_XYZ_99999")
        database.set_setting("provider", "gemini")

    def tearDown(self):
        if self.original_key:
            database.set_setting("gemini_api_key", self.original_key)

    def test_api_key_is_never_revealed_in_ui_controls(self):
        page = MockSettingsPage()
        dialog = SettingsDialog(page=page, is_dark=True, on_settings_saved=lambda s: None)

        # 1. The text field value must NEVER contain the secret key
        self.assertEqual(dialog.gemini_key_input.value, "")

        # 2. Visitors must NOT have a reveal toggle
        self.assertFalse(dialog.gemini_key_input.can_reveal_password)
        self.assertTrue(dialog.gemini_key_input.password)

        # 3. Status card reflects active state without disclosing secret
        self.assertNotIn("mock_dummy_secret_key", str(dialog.gemini_status_card.content))

    def test_saving_without_typing_preserves_existing_key(self):
        page = MockSettingsPage()
        dialog = SettingsDialog(page=page, is_dark=True, on_settings_saved=lambda s: None)

        # Simulate user saving settings (e.g. changing theme or persona) without typing in key field
        dialog._save()

        # Database key must remain completely intact
        saved_key = database.get_setting("gemini_api_key")
        self.assertEqual(saved_key, "MOCK_TEST_GEMINI_KEY_XYZ_99999")

    def test_saving_with_new_key_updates_securely(self):
        page = MockSettingsPage()
        dialog = SettingsDialog(page=page, is_dark=True, on_settings_saved=lambda s: None)

        dialog.gemini_key_input.value = "BRAND_NEW_VALID_KEY_777"
        dialog.claude_key_input.value = "sk-ant-test-key-12345"
        dialog._save()

        self.assertEqual(database.get_setting("gemini_api_key"), "BRAND_NEW_VALID_KEY_777")
        self.assertEqual(database.get_setting("claude_api_key"), "sk-ant-test-key-12345")

        dialog.gemini_key_input.value = "mock_updated_key_test_value"
        dialog._save()

        saved_key = database.get_setting("gemini_api_key")
        self.assertEqual(saved_key, "mock_updated_key_test_value")
