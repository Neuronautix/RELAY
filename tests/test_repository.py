from pathlib import Path
import unittest

from scripts.validate_repository import validate_repository


class RepositoryValidationTest(unittest.TestCase):
    def test_repository_is_self_consistent(self):
        root = Path(__file__).resolve().parents[1]
        problems = validate_repository(root)
        self.assertEqual([], [str(problem) for problem in problems])


if __name__ == "__main__":
    unittest.main()
