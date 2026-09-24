import unittest

import fastmath


class FastMathTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(fastmath.add(10, 20), 30)

    def test_dot_product(self):
        self.assertEqual(fastmath.dot_product([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]), 32.0)

    def test_dot_product_rejects_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            fastmath.dot_product([1.0], [1.0, 2.0])


if __name__ == "__main__":
    unittest.main()

