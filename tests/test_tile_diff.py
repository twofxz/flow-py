"""Canvas snapshots must tell a new image apart from tiles already on screen."""

import unittest

from flow_api.editor import added_error_messages, new_image_srcs


class TestTileDiff(unittest.TestCase):
    def test_ignores_the_image_that_was_already_on_the_canvas(self):
        before = ["err:usage limit", "img:https://cdn.example/old"]
        after = ["err:usage limit", "err:usage limit", "img:https://cdn.example/old"]
        self.assertEqual(new_image_srcs(before, after), [])
        self.assertEqual(added_error_messages(before, after), ["usage limit"])

    def test_keeps_only_the_src_from_this_submit(self):
        before = ["img:https://cdn.example/old"]
        after = [
            "img:https://cdn.example/new-a",
            "img:https://cdn.example/new-b",
            "img:https://cdn.example/old",
        ]
        self.assertEqual(
            new_image_srcs(before, after),
            ["https://cdn.example/new-a", "https://cdn.example/new-b"],
        )
        self.assertEqual(added_error_messages(before, after), [])


if __name__ == "__main__":
    unittest.main()
