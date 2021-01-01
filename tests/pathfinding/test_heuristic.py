import unittest


class EuclideanHeuristicTestCase(unittest.TestCase):
    def test_heuristic(self):
        self.assertEqual(True, False)


class ManhattanHeuristicTestCase(unittest.TestCase):
    def test_heuristic(self):
        pass


class EuclideanRiskHeuristicTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_heuristic(self):
        pass


if __name__ == '__main__':
    unittest.main()
