"""
Unit tests for conflict_parser.py
Covers:
- Standard 2-way Git conflicts
- diff3 Git conflicts (with common ancestor)
- CRLF and LF line ending preservation
- Malformed and unclosed markers
- Multiple mixed conflicts
- Reversion to Base ancestor
"""

import unittest
from conflict_parser import (
    parse_conflict_text,
    resolve_conflicts,
    detect_line_ending,
    normalize_line_endings
)


class TestConflictParser(unittest.TestCase):

    def test_empty_input(self):
        result = parse_conflict_text("")
        self.assertFalse(result["has_conflicts"])
        self.assertEqual(result["conflict_count"], 0)
        self.assertEqual(len(result["blocks"]), 0)
        self.assertEqual(resolve_conflicts(result["blocks"], {}), "")

    def test_no_conflicts(self):
        clean_text = "def hello():\n    print('Hello World')\n"
        result = parse_conflict_text(clean_text)
        self.assertFalse(result["has_conflicts"])
        self.assertEqual(result["conflict_count"], 0)
        self.assertEqual(len(result["blocks"]), 1)
        self.assertEqual(result["blocks"][0]["type"], "normal")
        self.assertEqual(result["blocks"][0]["content"], clean_text)

        resolved = resolve_conflicts(result["blocks"], {})
        self.assertEqual(resolved, clean_text)

    def test_single_standard_conflict(self):
        text = (
            "header line\n"
            "<<<<<<< HEAD\n"
            "our code\n"
            "=======\n"
            "their code\n"
            ">>>>>>> feature-branch\n"
            "footer line\n"
        )
        result = parse_conflict_text(text)
        self.assertTrue(result["has_conflicts"])
        self.assertEqual(result["conflict_count"], 1)
        self.assertEqual(len(result["blocks"]), 3)

        conflict = result["blocks"][1]
        self.assertEqual(conflict["type"], "conflict")
        self.assertFalse(conflict["has_base"])
        self.assertEqual(conflict["ours_label"], "HEAD")
        self.assertEqual(conflict["theirs_label"], "feature-branch")
        self.assertEqual(conflict["ours"], "our code\n")
        self.assertEqual(conflict["theirs"], "their code\n")

    def test_diff3_conflict_with_base_ancestor(self):
        text = (
            "<<<<<<< HEAD\n"
            "our change\n"
            "||||||| base-commit-hash\n"
            "original ancestor code\n"
            "=======\n"
            "their change\n"
            ">>>>>>> incoming-branch\n"
        )
        result = parse_conflict_text(text)
        self.assertTrue(result["has_conflicts"])
        self.assertEqual(result["conflict_count"], 1)

        conflict = result["blocks"][0]
        self.assertTrue(conflict["has_base"])
        self.assertEqual(conflict["ours_label"], "HEAD")
        self.assertEqual(conflict["base_label"], "base-commit-hash")
        self.assertEqual(conflict["theirs_label"], "incoming-branch")
        self.assertEqual(conflict["ours"], "our change\n")
        self.assertEqual(conflict["base"], "original ancestor code\n")
        self.assertEqual(conflict["theirs"], "their change\n")

        # Test resolution to Base (rejecting both changes)
        resolved_base = resolve_conflicts(result["blocks"], {"1": "base"})
        self.assertEqual(resolved_base, "original ancestor code\n")

        # Test resolution to Ours
        resolved_ours = resolve_conflicts(result["blocks"], {"1": "ours"})
        self.assertEqual(resolved_ours, "our change\n")

    def test_line_ending_preservation_crlf(self):
        windows_text = (
            "line 1\r\n"
            "<<<<<<< HEAD\r\n"
            "windows ours\r\n"
            "=======\r\n"
            "windows theirs\r\n"
            ">>>>>>> feature\r\n"
            "line 2\r\n"
        )
        self.assertEqual(detect_line_ending(windows_text), "\r\n")
        result = parse_conflict_text(windows_text)
        self.assertEqual(result["line_ending"], "\r\n")

        resolved = resolve_conflicts(result["blocks"], {"1": "theirs"}, target_ending="\r\n")
        self.assertIn("\r\n", resolved)
        self.assertNotIn("windows ours", resolved)
        self.assertEqual(resolved, "line 1\r\nwindows theirs\r\nline 2\r\n")

    def test_line_ending_preservation_lf(self):
        unix_text = (
            "line 1\n"
            "<<<<<<< HEAD\n"
            "unix ours\n"
            "=======\n"
            "unix theirs\n"
            ">>>>>>> feature\n"
            "line 2\n"
        )
        self.assertEqual(detect_line_ending(unix_text), "\n")
        result = parse_conflict_text(unix_text)
        self.assertEqual(result["line_ending"], "\n")

        resolved = resolve_conflicts(result["blocks"], {"1": "ours"}, target_ending="\n")
        self.assertEqual(resolved, "line 1\nunix ours\nline 2\n")

    def test_resolution_permutations(self):
        text = (
            "<<<<<<< HEAD\n"
            "apple\n"
            "=======\n"
            "banana\n"
            ">>>>>>> branch\n"
        )
        blocks = parse_conflict_text(text)["blocks"]

        # Ours
        self.assertEqual(resolve_conflicts(blocks, {"1": "ours"}), "apple\n")
        # Theirs
        self.assertEqual(resolve_conflicts(blocks, {"1": "theirs"}), "banana\n")
        # Both (Ours First)
        self.assertEqual(resolve_conflicts(blocks, {"1": "both_ours_first"}), "apple\nbanana\n")
        # Both (Theirs First)
        self.assertEqual(resolve_conflicts(blocks, {"1": "both_theirs_first"}), "banana\napple\n")
        # Custom
        self.assertEqual(
            resolve_conflicts(blocks, {"1": "custom", "1_custom": "cherry\n"}),
            "cherry\n"
        )

    def test_multiple_mixed_conflicts(self):
        text = (
            "start\n"
            "<<<<<<< HEAD\n"
            "standard ours\n"
            "=======\n"
            "standard theirs\n"
            ">>>>>>> branch-1\n"
            "middle\n"
            "<<<<<<< HEAD\n"
            "diff3 ours\n"
            "||||||| base\n"
            "diff3 base\n"
            "=======\n"
            "diff3 theirs\n"
            ">>>>>>> branch-2\n"
            "end\n"
        )
        result = parse_conflict_text(text)
        self.assertEqual(result["conflict_count"], 2)
        self.assertFalse(result["blocks"][1]["has_base"])
        self.assertTrue(result["blocks"][3]["has_base"])

        # Resolve 1 with theirs, 2 with base
        resolved = resolve_conflicts(result["blocks"], {"1": "theirs", "2": "base"})
        expected = "start\nstandard theirs\nmiddle\ndiff3 base\nend\n"
        self.assertEqual(resolved, expected)

    def test_malformed_unclosed_ours(self):
        # File cuts off after <<<<<<<
        text = "header\n<<<<<<< HEAD\npartial ours code"
        result = parse_conflict_text(text)
        # Should not crash, leaves partial marker as plain text
        resolved = resolve_conflicts(result["blocks"], {})
        self.assertIn("header", resolved)
        self.assertIn("partial ours code", resolved)

    def test_malformed_consecutive_opening_markers(self):
        # Second <<<<<<< appears before first is closed
        text = (
            "<<<<<<< HEAD\n"
            "interrupted line\n"
            "<<<<<<< main\n"
            "real ours\n"
            "=======\n"
            "real theirs\n"
            ">>>>>>> feature\n"
        )
        result = parse_conflict_text(text)
        self.assertEqual(result["conflict_count"], 1)
        resolved = resolve_conflicts(result["blocks"], {"1": "theirs"})
        self.assertIn("real theirs", resolved)

    def test_empty_branch_deletion_conflicts(self):
        # Case 1: Ours is empty (incoming branch added lines)
        text_empty_ours = (
            "<<<<<<< HEAD\n"
            "=======\n"
            "added in feature\n"
            ">>>>>>> feature\n"
        )
        parsed1 = parse_conflict_text(text_empty_ours)
        self.assertEqual(parsed1["conflict_count"], 1)
        self.assertEqual(parsed1["blocks"][0]["ours"], "")
        self.assertEqual(parsed1["blocks"][0]["theirs"], "added in feature\n")
        self.assertEqual(resolve_conflicts(parsed1["blocks"], {"1": "ours"}), "")
        self.assertEqual(resolve_conflicts(parsed1["blocks"], {"1": "theirs"}), "added in feature\n")

        # Case 2: Theirs is empty (our branch added lines)
        text_empty_theirs = (
            "<<<<<<< HEAD\n"
            "added in main\n"
            "=======\n"
            ">>>>>>> feature\n"
        )
        parsed2 = parse_conflict_text(text_empty_theirs)
        self.assertEqual(parsed2["conflict_count"], 1)
        self.assertEqual(parsed2["blocks"][0]["ours"], "added in main\n")
        self.assertEqual(parsed2["blocks"][0]["theirs"], "")
        self.assertEqual(resolve_conflicts(parsed2["blocks"], {"1": "theirs"}), "")

    def test_unicode_and_emojis_support(self):
        text_unicode = (
            "<<<<<<< HEAD\n"
            "print('Hello 🌍 Rocket 🚀')\n"
            "=======\n"
            "print('Bonjour 🥐 Star ⭐')\n"
            ">>>>>>> feature-i18n\n"
        )
        parsed = parse_conflict_text(text_unicode)
        self.assertEqual(parsed["conflict_count"], 1)
        res_ours = resolve_conflicts(parsed["blocks"], {"1": "ours"})
        self.assertIn("🚀", res_ours)
        res_theirs = resolve_conflicts(parsed["blocks"], {"1": "theirs"})
        self.assertIn("🥐", res_theirs)

    def test_whitespace_and_indentation_preservation(self):
        text_indented = (
            "def calculate():\n"
            "<<<<<<< HEAD\n"
            "    # 4 spaces indentation\n"
            "    return x * 2\n"
            "=======\n"
            "\t# tab indentation\n"
            "\treturn x << 1\n"
            ">>>>>>> feature-bitwise\n"
        )
        parsed = parse_conflict_text(text_indented)
        res_ours = resolve_conflicts(parsed["blocks"], {"1": "ours"})
        self.assertIn("    # 4 spaces", res_ours)
        res_theirs = resolve_conflicts(parsed["blocks"], {"1": "theirs"})
        self.assertIn("\t# tab", res_theirs)


if __name__ == "__main__":
    unittest.main()
