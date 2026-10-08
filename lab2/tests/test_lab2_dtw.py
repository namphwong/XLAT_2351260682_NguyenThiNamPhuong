"""Independent checks for DTW, including exhaustive small-grid paths."""
import unittest
import numpy as np
from lab2_dtw import local_distance_matrix, dtw_details, dtw_distance


def all_paths(n, m, i=0, j=0):
    if i == n - 1 and j == m - 1:
        yield [(i, j)]
        return
    for di, dj in [(1, 1), (1, 0), (0, 1)]:
        if i + di < n and j + dj < m:
            for tail in all_paths(n, m, i + di, j + dj):
                yield [(i, j), *tail]


class DTWTests(unittest.TestCase):
    def test_euclidean_example(self):
        self.assertEqual(local_distance_matrix([[1, 2]], [[4, 6]])[0, 0], 5)

    def test_exhaustive_small_sequences(self):
        rng = np.random.default_rng(457)
        for n in range(1, 5):
            for m in range(1, 5):
                for _ in range(3):
                    X, Y = rng.integers(0, 4, (n, 1)), rng.integers(0, 4, (m, 1))
                    C = np.abs(X[:, 0, None] - Y[None, :, 0])
                    # Enumerate all legal alignments, independent of dynamic programming.
                    expected_cost, expected_length = min(
                        (sum(C[i, j] for i, j in p), len(p)) for p in all_paths(n, m))
                    result = dtw_details(X, Y)
                    self.assertEqual(result['total_cost'], expected_cost)
                    self.assertEqual(result['path_length'], expected_length)
                    self.assertEqual(result['normalized_cost'], expected_cost / expected_length)
                    self.assertEqual(result['path'][0], (0, 0))
                    self.assertEqual(result['path'][-1], (n - 1, m - 1))
                    steps = np.diff(result['path'], axis=0)
                    self.assertTrue(all(tuple(s) in [(1, 1), (1, 0), (0, 1)] for s in steps))
                    reverse = dtw_details(Y, X)
                    self.assertEqual(result['normalized_cost'], reverse['normalized_cost'])

    def test_identical_and_repeated_frames(self):
        X = np.array([[0, 1], [2, 3], [4, 5]], dtype=float)
        identical = dtw_details(X, X)
        self.assertEqual(identical['normalized_cost'], 0)
        self.assertEqual(identical['path'], [(0, 0), (1, 1), (2, 2)])
        score, path, D = dtw_distance(X, np.repeat(X, [2, 1, 3], axis=0))
        self.assertEqual(score, 0)
        self.assertEqual(D.shape, (3, 6))
        self.assertEqual(path[-1], (2, 5))

    def test_path_sum(self):
        rng = np.random.default_rng(19)
        X, Y = rng.normal(size=(8, 13)), rng.normal(size=(5, 13))
        result = dtw_details(X, Y)
        i, j = np.array(result['path']).T
        self.assertAlmostEqual(result['total_cost'], result['local_distance'][i, j].sum())
        self.assertAlmostEqual(result['normalized_cost'], result['total_cost'] / len(i))

    def test_invalid_inputs(self):
        for X, Y in [(np.empty((0, 13)), np.ones((2, 13))),
                     (np.ones((2, 12)), np.ones((2, 13))),
                     (np.ones(13), np.ones((2, 13))),
                     (np.full((2, 13), np.nan), np.ones((2, 13))),
                     (np.ones((2, 0)), np.ones((2, 0))),
                     (np.full((2, 1), 1e308), np.full((2, 1), -1e308))]:
            with self.assertRaises(ValueError):
                dtw_details(X, Y)


if __name__ == '__main__':
    unittest.main()
