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

        @self.app.get("/health")
        @self.app.get("/ping")
        async def ping_health():
            return {
                "status": "online",
                "app": "KESHAV AI",
                "developer": "Keshav Batra",
                "keep_alive": True,
            }

        @self.app.get("/dictate", response_class=HTMLResponse)
        async def dictate_page():
            with open(dictate_path, "r", encoding="utf-8") as f:
                return f.read()

        @self.app.get("/robots.txt")
        async def robots_txt():
            return "User-agent: *\nAllow: /\nSitemap: https://keshav-ai.onrender.com/sitemap.xml\n"

        @self.app.get("/sitemap.xml")
        async def sitemap_xml():
            return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://keshav-ai.onrender.com/</loc></url>
</urlset>"""

        @self.app.get("/google{code}.html")
        async def google_verification_file(code: str):
            return f"google-site-verification: google{code}.html"

        @self.app.get("/logo.png")
        async def logo_file():
            return HTMLResponse("fake png data", media_type="image/png")

        @self.app.get("/favicon.png")
        async def favicon_file():
            return HTMLResponse("fake icon data", media_type="image/png")

        self.client = TestClient(self.app)

    def test_logo_and_favicon_endpoints(self):
        resp_logo = self.client.get("/logo.png")
        self.assertEqual(resp_logo.status_code, 200)
        resp_fav = self.client.get("/favicon.png")
        self.assertEqual(resp_fav.status_code, 200)

    def test_robots_and_sitemap(self):
        resp_robots = self.client.get("/robots.txt")
        self.assertEqual(resp_robots.status_code, 200)
        self.assertIn("User-agent: *", resp_robots.text)
        self.assertIn("sitemap.xml", resp_robots.text)

        resp_sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(resp_sitemap.status_code, 200)
        self.assertIn("keshav-ai.onrender.com", resp_sitemap.text)

        resp_google = self.client.get("/googleF3DyA0ho9fPeBQxxoh1_-mjpwreKhkHvQuIhBxI5XJw.html")
        self.assertEqual(resp_google.status_code, 200)
        self.assertIn("google-site-verification: googleF3DyA0ho9fPeBQxxoh1_-mjpwreKhkHvQuIhBxI5XJw.html", resp_google.text)

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

    def test_health_and_ping_endpoints(self):
        resp_health = self.client.get("/health")
        self.assertEqual(resp_health.status_code, 200)
        self.assertEqual(resp_health.json()["status"], "online")
        self.assertEqual(resp_health.json()["developer"], "Keshav Batra")

        resp_ping = self.client.get("/ping")
        self.assertEqual(resp_ping.status_code, 200)
        self.assertEqual(resp_ping.json()["status"], "online")


if __name__ == "__main__":
    unittest.main()
