"""
Integration tests for Flask application routes (app.py).
Tests:
- Homepage rendering (GET /)
- Conflict marker detection endpoint (POST /api/parse)
- Conflict resolution endpoint (POST /api/resolve)
- Sample file loaders (GET /api/sample/<name>)
"""

import unittest
import json
from app import app


class TestAppRoutes(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_route(self):
        """Verify the homepage loads with status 200 and contains the app title."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"MergeMate", response.data)
        self.assertIn(b"Smart Git Merge Conflict Resolver", response.data)

    def test_api_parse_empty(self):
        """Verify parsing empty text returns 400 Bad Request."""
        response = self.client.post("/api/parse", json={"text": ""})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])

    def test_api_parse_standard_conflict(self):
        """Verify parsing standard conflicted code returns structured blocks."""
        conflict_code = (
            "<<<<<<< HEAD\n"
            "val = 10\n"
            "=======\n"
            "val = 20\n"
            ">>>>>>> branch-2\n"
        )
        response = self.client.post("/api/parse", json={"text": conflict_code})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertTrue(data["has_conflicts"])
        self.assertEqual(data["conflict_count"], 1)
        self.assertEqual(len(data["blocks"]), 1)
        self.assertFalse(data["blocks"][0]["has_base"])

    def test_api_parse_diff3_conflict(self):
        """Verify parsing diff3 conflicted code identifies common ancestor."""
        diff3_code = (
            "<<<<<<< HEAD\n"
            "val = 10\n"
            "||||||| base-tag\n"
            "val = 0\n"
            "=======\n"
            "val = 20\n"
            ">>>>>>> branch-2\n"
        )
        response = self.client.post("/api/parse", json={"text": diff3_code})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertTrue(data["blocks"][0]["has_base"])
        self.assertEqual(data["blocks"][0]["base_label"], "base-tag")
        self.assertEqual(data["blocks"][0]["base"], "val = 0\n")

    def test_api_resolve(self):
        """Verify resolution API cleanly applies user selection and preserves line endings."""
        blocks = [
            {
                "id": 1,
                "type": "conflict",
                "ours": "selected ours\n",
                "theirs": "ignored theirs\n"
            }
        ]
        response = self.client.post("/api/resolve", json={
            "blocks": blocks,
            "resolutions": {"1": "ours"},
            "line_ending": "\r\n"
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["resolved_code"], "selected ours\r\n")

    def test_api_samples(self):
        """Verify all built-in sample endpoints load correctly."""
        # Simple sample
        resp_simple = self.client.get("/api/sample/simple")
        self.assertEqual(resp_simple.status_code, 200)
        data_simple = json.loads(resp_simple.data)
        self.assertTrue(data_simple["success"])
        self.assertIn("HEAD", data_simple["content"])

        # Calculator sample
        resp_calc = self.client.get("/api/sample/calculator")
        self.assertEqual(resp_calc.status_code, 200)
        data_calc = json.loads(resp_calc.data)
        self.assertTrue(data_calc["success"])
        self.assertIn("multiply", data_calc["content"])

        # Diff3 sample
        resp_diff3 = self.client.get("/api/sample/diff3")
        self.assertEqual(resp_diff3.status_code, 200)
        data_diff3 = json.loads(resp_diff3.data)
        self.assertTrue(data_diff3["success"])
        self.assertIn("|||||||", data_diff3["content"])

        # Invalid sample
        resp_invalid = self.client.get("/api/sample/nonexistent")
        self.assertEqual(resp_invalid.status_code, 404)


if __name__ == "__main__":
    unittest.main()
