"""
Tests for multi-tenant / client isolation in database.
Ensures that visitors accessing KESHAV AI get completely isolated chats
and cannot see any other visitor's history.
"""

import unittest
import database


class TestClientIsolation(unittest.TestCase):
    def setUp(self):
        database.init_db()
        self.client_a = "test-client-alice-uuid-1111"
        self.client_b = "test-client-bob-uuid-2222"

    def tearDown(self):
        # Cleanup test sessions
        for s in database.get_sessions(client_id=self.client_a):
            database.delete_session(s["id"])
        for s in database.get_sessions(client_id=self.client_b):
            database.delete_session(s["id"])

    def test_client_sessions_are_strictly_isolated(self):
        # Client A creates a session
        sess_a = database.create_session(title="Alice Secret Chat", client_id=self.client_a)
        database.add_message(sess_a, "user", "Alice message: Hello KESHAV AI")
        database.add_message(sess_a, "assistant", "Hello Alice!")

        # Client B creates a session
        sess_b = database.create_session(title="Bob Private Chat", client_id=self.client_b)
        database.add_message(sess_b, "user", "Bob message: Weather today?")
        database.add_message(sess_b, "assistant", "Hi Bob! It is sunny.")

        # Query sessions for Client A
        sessions_a = database.get_sessions(client_id=self.client_a)
        a_ids = [s["id"] for s in sessions_a]
        self.assertIn(sess_a, a_ids)
        self.assertNotIn(sess_b, a_ids)
        for s in sessions_a:
            self.assertEqual(s["client_id"], self.client_a)

        # Query sessions for Client B
        sessions_b = database.get_sessions(client_id=self.client_b)
        b_ids = [s["id"] for s in sessions_b]
        self.assertIn(sess_b, b_ids)
        self.assertNotIn(sess_a, b_ids)
        for s in sessions_b:
            self.assertEqual(s["client_id"], self.client_b)

    def test_get_or_create_initial_session_for_new_client(self):
        new_client = "brand-new-visitor-3333"
        init_sess_id = database.get_or_create_initial_session(client_id=new_client)
        sess = database.get_session(init_sess_id)
        self.assertIsNotNone(sess)
        self.assertEqual(sess["client_id"], new_client)
        self.assertEqual(sess["title"], "New Chat")

        # Cleanup
        database.delete_session(init_sess_id)

    def test_search_sessions_scopes_strictly_to_client(self):
        sess_a = database.create_session(title="Alice Economics", client_id=self.client_a)
        database.add_message(sess_a, "user", "What is ex ante?")

        sess_b = database.create_session(title="Bob Economics", client_id=self.client_b)
        database.add_message(sess_b, "user", "What is ex post?")

        # Alice searches for 'ex ante'
        res_a = database.search_sessions("ex ante", client_id=self.client_a)
        self.assertEqual(len(res_a), 1)
        self.assertEqual(res_a[0]["id"], sess_a)

        # Bob searches for 'ex ante' - should find nothing
        res_b = database.search_sessions("ex ante", client_id=self.client_b)
        self.assertEqual(len(res_b), 0)

        # Bob searches for 'ex post' - should find only his
        res_b2 = database.search_sessions("ex post", client_id=self.client_b)
        self.assertEqual(len(res_b2), 1)
        self.assertEqual(res_b2[0]["id"], sess_b)
