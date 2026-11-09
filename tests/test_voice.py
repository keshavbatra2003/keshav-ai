"""
Unit tests for Voice Service and text cleaning algorithms.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_service import voice_service


class TestVoiceService(unittest.TestCase):
    def test_clean_text_for_speech_removes_code_blocks(self):
        markdown_text = (
            "Here is the code you asked for:\n"
            "```python\ndef add(a, b):\n    return a + b\n```\n"
            "It computes the sum."
        )
        cleaned = voice_service.clean_text_for_speech(markdown_text)
        self.assertNotIn("def add(a, b)", cleaned)
        self.assertIn("Here is the code", cleaned)
        self.assertIn("It computes the sum", cleaned)

    def test_clean_text_for_speech_removes_symbols(self):
        text = "### Welcome to **KESHAV AI**! Visit [our site](https://example.com) for > updates."
        cleaned = voice_service.clean_text_for_speech(text)
        self.assertNotIn("###", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertIn("Welcome to KESHAV AI", cleaned)
        self.assertIn("our site", cleaned)


if __name__ == "__main__":
    unittest.main()
