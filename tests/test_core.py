"""
Unit tests for KESHAV AI Assistant core modules including streaming.
"""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ai_service
import database


class TestCoreModules(unittest.TestCase):
    def setUp(self):
        database.init_db()

    def test_database_session_and_message_lifecycle(self):
        # Create session
        session_id = database.create_session(title="Test Architecture Chat")
        self.assertIsNotNone(session_id)

        # Check session retrieved
        session = database.get_session(session_id)
        self.assertEqual(session["title"], "Test Architecture Chat")

        # Add user message
        user_msg = database.add_message(session_id, "user", "How do I implement Clean Architecture in Python?")
        self.assertEqual(user_msg["role"], "user")
        self.assertIn("Clean Architecture", user_msg["content"])

        # Add assistant message
        asst_msg = database.add_message(session_id, "assistant", "Clean Architecture separates concerns into entities, use cases, and adapters.")
        self.assertEqual(asst_msg["role"], "assistant")

        # Retrieve messages
        messages = database.get_messages(session_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")

        # Update title
        database.update_session_title(session_id, "Python Clean Architecture")
        updated = database.get_session(session_id)
        self.assertEqual(updated["title"], "Python Clean Architecture")

        # Clear messages
        database.clear_messages(session_id)
        self.assertEqual(len(database.get_messages(session_id)), 0)

        # Test message editing and truncation
        m1 = database.add_message(session_id, "user", "Original query")
        m2 = database.add_message(session_id, "assistant", "Original answer")
        m3 = database.add_message(session_id, "user", "Follow up")
        self.assertEqual(len(database.get_messages(session_id)), 3)

        database.update_message(m1["id"], "Edited query")
        msgs = database.get_messages(session_id)
        self.assertEqual(msgs[0]["content"], "Edited query")

        database.delete_messages_after(session_id, m1["id"])
        msgs_after = database.get_messages(session_id)
        self.assertEqual(len(msgs_after), 1)
        self.assertEqual(msgs_after[0]["id"], m1["id"])

        # Delete session
        database.delete_session(session_id)
        self.assertIsNone(database.get_session(session_id))

    def test_settings_storage(self):
        initial_prov = database.get_setting("provider", "gemini")
        try:
            database.set_setting("provider", "gemini")
            val = database.get_setting("provider")
            self.assertEqual(val, "gemini")

            database.set_setting("provider", "demo")
            self.assertEqual(database.get_setting("provider"), "demo")
        finally:
            database.set_setting("provider", initial_prov)

    def test_mock_ai_engine(self):
        messages = [{"role": "user", "content": "Can you write a python function?"}]
        reply = ai_service.MockAIEngine.generate_reply(messages, "You are a coding helper.")
        self.assertIn("```python", reply)

        greetings = [{"role": "user", "content": "Hello!"}]
        reply_greet = ai_service.MockAIEngine.generate_reply(greetings, "")
        self.assertIn("KESHAV AI", reply_greet)

    def test_streaming_demo_response(self):
        async def _test():
            messages = [{"role": "user", "content": "Hi Keshav"}]
            chunks = []
            async for chunk in ai_service.stream_demo_response(messages, ""):
                chunks.append(chunk)
            self.assertTrue(len(chunks) > 5)
            self.assertTrue(len(chunks[-1]) > len(chunks[0]))

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
