import os
import unittest
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.testclient import TestClient

import database
import ai_service


class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        database.init_db()
        self.app = FastAPI()

        @self.app.get("/share/{session_id}", response_class=HTMLResponse)
        async def share_conversation_page(session_id: str):
            session = database.get_session(session_id)
            if not session:
                return HTMLResponse("<html><body>Not Found</body></html>", status_code=404)
            messages = database.get_messages(session_id)
            template_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "assets",
                "share_template.html",
            )
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            rendered = template.replace("{{TITLE}}", session.get("title", ""))
            return HTMLResponse(rendered)

        self.client = TestClient(self.app)

    def test_search_request_detection(self):
        self.assertTrue(ai_service.is_search_request("/search latest AI news"))
        self.assertTrue(ai_service.is_search_request("/web python 3.14 features"))
        self.assertTrue(ai_service.is_search_request("can you search web for quantum computing"))
        self.assertTrue(ai_service.is_search_request("latest news on Mars rover"))
        self.assertFalse(ai_service.is_search_request("Hello how are you today?"))
        self.assertFalse(ai_service.is_search_request("Write a quick python script"))

    def test_extract_search_query(self):
        q1 = ai_service.extract_search_query("/search latest AI breakthroughs")
        self.assertEqual(q1, "latest AI breakthroughs")
        q2 = ai_service.extract_search_query("/web artificial intelligence")
        self.assertEqual(q2, "artificial intelligence")

    def test_share_endpoint_404_for_unknown_session(self):
        resp = self.client.get("/share/non-existent-session-id-12345")
        self.assertEqual(resp.status_code, 404)

    def test_share_endpoint_200_for_valid_session(self):
        sess_id = database.create_session("Test Shared Session Title")
        database.add_message(sess_id, "user", "What is KESHAV AI?")
        database.add_message(sess_id, "assistant", "KESHAV AI was created by Keshav Batra.")

        resp = self.client.get(f"/share/{sess_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Test Shared Session Title", resp.text)
        self.assertIn("KESHAV AI", resp.text)
        self.assertIn("Keshav Batra", resp.text)

    def test_pypdf_extraction_capability(self):
        import io
        import pypdf

        # Generate minimal valid PDF in memory
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=72, height=72)
        stream = io.BytesIO()
        writer.write(stream)
        stream.seek(0)

        reader = pypdf.PdfReader(stream)
        self.assertEqual(len(reader.pages), 1)


if __name__ == "__main__":
    unittest.main()
