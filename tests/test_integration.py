"""
Integration test verifying main(page) initialization and lifecycle.
"""

import os
import sys
import unittest
import flet as ft

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from main import main


class MockPage:
    def __init__(self):
        self.title = ""
        self.theme_mode = None
        self.padding = None
        self.spacing = None
        self.bgcolor = None
        self.width = 1040
        self.window = type("MockWindow", (), {"width": 0, "height": 0, "min_width": 0, "min_height": 0})()
        self.overlay = []
        self.services = []
        self.controls = []
        self.drawer = None
        self.dialog = None
        self.on_resize = None

    def add(self, control):
        self.controls.append(control)

    def update(self):
        pass

    def show_dialog(self, dialog):
        self.dialog = dialog

    def pop_dialog(self):
        self.dialog = None

    def show_drawer(self):
        pass

    def close_drawer(self):
        pass


class TestAppIntegration(unittest.TestCase):
    def setUp(self):
        database.init_db()

    def test_main_page_initialization_desktop(self):
        page = MockPage()
        page.width = 1040
        main(page)

        self.assertIn("KESHAV AI", page.title)
        self.assertIsNotNone(page.drawer)
        self.assertTrue(len(page.controls) > 0)
        self.assertTrue(len(page.services) > 0)

    def test_main_page_initialization_mobile(self):
        page = MockPage()
        page.width = 390  # Mobile screen width
        main(page)

        self.assertIn("KESHAV AI", page.title)
        self.assertIsNotNone(page.drawer)
        self.assertTrue(len(page.controls) > 0)


if __name__ == "__main__":
    unittest.main()
