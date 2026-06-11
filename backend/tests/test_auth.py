import unittest

from app.auth import ANONYMOUS_USER_TOKEN, get_user_token


class AuthTests(unittest.TestCase):
    def test_get_user_token_accepts_bearer_header(self):
        self.assertEqual(get_user_token("Bearer abc-123"), "abc-123")

    def test_get_user_token_falls_back_to_anonymous(self):
        self.assertEqual(get_user_token(None), ANONYMOUS_USER_TOKEN)
        self.assertEqual(get_user_token("Bearer   "), ANONYMOUS_USER_TOKEN)


if __name__ == "__main__":
    unittest.main()
