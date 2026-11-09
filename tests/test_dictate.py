import os
import unittest
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.testclient import TestClient


class TestDictateEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        dictate_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "dictate.html",
        )

        @self.app.get("/dictate", response_class=HTMLResponse)
        async def dictate_page():
            with open(dictate_path, "r", encoding="utf-8") as f:
                return f.read()

        self.client = TestClient(self.app)

    def test_dictate_page_renders_html5_speech(self):
        resp = self.client.get("/dictate")
        self.assertEqual(resp.status_code, 200)
        content = resp.text
        self.assertIn("SpeechRecognition", content)
        self.assertIn("webkitSpeechRecognition", content)
        self.assertIn("KESHAV AI", content)
        self.assertIn("Keshav Batra", content)
        self.assertIn("transcriptBox", content)
        self.assertIn("Ask KESHAV AI (Send Now)", content)


if __name__ == "__main__":
    unittest.main()
