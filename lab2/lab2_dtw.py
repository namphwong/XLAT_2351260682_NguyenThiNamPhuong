"""Euclidean local distances and full dynamic-programming DTW for Lab 2."""
import numpy as np


def _feature_pair(X, Y):
    X, Y = np.asarray(X, dtype=np.float64), np.asarray(Y, dtype=np.float64)
    if X.ndim != 2 or Y.ndim != 2:
        raise ValueError('Each feature matrix must have shape (frames, dimensions)')
    if min(X.shape[0], Y.shape[0], X.shape[1], Y.shape[1]) == 0:
        raise ValueError('Feature sequences and dimensions must be nonempty')
    if X.shape[1] != Y.shape[1]:
        raise ValueError('Feature dimensions must match')
    if not np.isfinite(X).all() or not np.isfinite(Y).all():
        raise ValueError('Features must contain finite values')
    return X, Y


def local_distance_matrix(X, Y):
    """C[i,j] is Euclidean distance between frame i of X and frame j of Y."""
    X, Y = _feature_pair(X, Y)
    with np.errstate(over='ignore', invalid='ignore'):
        C = np.linalg.norm(X[:, None, :] - Y[None, :, :], axis=2)
    if not np.isfinite(C).all():
        raise ValueError('Euclidean distances overflowed; check feature scale')
    return C


def dtw_details(X, Y):
    """Minimize total local cost; divide that optimal path cost by its length.

    Steps: diagonal (1,1), vertical (1,0), horizontal (0,1). Exact total-cost
    ties prefer the shorter path, then diagonal, vertical, horizontal. This
    is not an optimizer of average cost and imposes no warping band.
    """
    C = local_distance_matrix(X, Y)
    N, M = C.shape
    accumulated = np.full((N + 1, M + 1), np.inf)
    accumulated[0, 0] = 0
    lengths = np.full((N + 1, M + 1), np.iinfo(np.int32).max, dtype=np.int64)
    lengths[0, 0] = 0
    back = np.full((N + 1, M + 1), 255, dtype=np.uint8)
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            options = [
                (accumulated[i - 1, j - 1], lengths[i - 1, j - 1], 0),
                (accumulated[i - 1, j], lengths[i - 1, j], 1),
                (accumulated[i, j - 1], lengths[i, j - 1], 2),
            ]
            previous_cost, previous_length, direction = min(options)
            accumulated[i, j] = C[i - 1, j - 1] + previous_cost
            lengths[i, j] = previous_length + 1
            back[i, j] = direction
    if not np.isfinite(accumulated[N, M]):
        raise ValueError('Accumulated DTW cost overflowed')
    path = []
    i, j = N, M
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        direction = back[i, j]
        if direction == 0:
            i, j = i - 1, j - 1
        elif direction == 1:
            i -= 1
        elif direction == 2:
            j -= 1
        else:
            raise RuntimeError('Invalid backtracking state')
    if i != 0 or j != 0:
        raise RuntimeError('Path did not reach origin')
    path.reverse()
    total_cost = float(accumulated[N, M])
    return {'normalized_cost': total_cost / len(path), 'total_cost': total_cost,
            'path': path, 'path_length': len(path), 'local_distance': C,
            'accumulated_cost': accumulated[1:, 1:]}


def dtw_distance(X, Y):
    """Baseline-compatible return: normalized score, path, accumulated matrix."""
    result = dtw_details(X, Y)
    return result['normalized_cost'], result['path'], result['accumulated_cost']


def path_statistics(path, n_frames, m_frames):
    path = np.asarray(path, dtype=int)
    steps = np.diff(path, axis=0)
    diagonal = int(np.sum(np.all(steps == (1, 1), axis=1)))
    vertical = int(np.sum(np.all(steps == (1, 0), axis=1)))
    horizontal = int(np.sum(np.all(steps == (0, 1), axis=1)))
    deviation = np.abs(path[:, 0] / max(1, n_frames - 1) -
                       path[:, 1] / max(1, m_frames - 1))
    return {'diagonal_steps': diagonal, 'vertical_steps': vertical,
            'horizontal_steps': horizontal,
            'mean_normalized_diagonal_deviation': float(deviation.mean())}
