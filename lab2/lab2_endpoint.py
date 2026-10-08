"""Energy hysteresis endpoint detection for isolated-word Lab 2 recordings."""
import numpy as np
from scipy.ndimage import median_filter
from lab2_time_features import time_features


def runs(mask):
    padded = np.r_[False, np.asarray(mask, dtype=bool), False].astype(int)
    changes = np.diff(padded)
    return list(zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)))


def bridge_short_gaps(mask, max_gap):
    result = np.asarray(mask, dtype=bool).copy()
    spans = runs(result)
    for (_, stop), (start, _) in zip(spans, spans[1:]):
        if start - stop <= max_gap:
            result[stop:start] = True
    return result


def detect_endpoint(y, sr=16000, frame_length=400, hop_length=160,
                    high_top_db=18, low_top_db=30, noise_high_db=12,
                    noise_low_db=6, min_speech_ms=120, gap_ms=40,
                    extend_ms=150, margin_ms=80, zcr_threshold=0.10,
                    use_zcr=True, eps=1e-9):
    """Return sample-exclusive bounds and diagnostics; reject click-only input.

    Main continuous segment is chosen for an isolated word. Does not guarantee
    phonetic boundaries and is unsuitable for continuous/multiword recordings.
    """
    if not 0 < high_top_db < low_top_db or not 0 <= noise_low_db < noise_high_db:
        raise ValueError('Invalid high/low thresholds')
    if min(min_speech_ms, gap_ms, extend_ms, margin_ms) < 0 or min_speech_ms == 0:
        raise ValueError('Invalid duration settings')
    if not 0 <= zcr_threshold <= 1:
        raise ValueError('Invalid ZCR threshold')
    f = time_features(y, sr, frame_length, hop_length, eps)
    if np.max(np.abs(y)) <= 1e-5:
        raise ValueError('No speech: empty-level recording')
    raw = f['log_energy_db']
    smooth = median_filter(raw, size=5, mode='nearest')
    peak = float(smooth.max())
    edge_count = max(1, round(0.2 * sr / hop_length))
    edge_values = np.r_[raw[:edge_count], raw[-edge_count:]]
    # Ignore digital zeros for background estimation; otherwise retain eps floor.
    nonzero_edges = edge_values[edge_values > 10 * np.log10(eps) + 3]
    noise = float(np.median(nonzero_edges)) if len(nonzero_edges) else float(10 * np.log10(eps))
    high = max(peak - high_top_db, noise + noise_high_db)
    low = max(peak - low_top_db, noise + noise_low_db)
    warnings = []
    if high >= peak - 3:
        warnings.append('Nền đầu/cuối có thể chứa âm mạnh; dùng ngưỡng tương đối theo peak')
        high, low = peak - high_top_db, peak - low_top_db
    if low >= high:
        low = high - 6
    gap_frames = max(0, round(gap_ms * sr / 1000 / hop_length))
    high_mask = bridge_short_gaps(smooth >= high, gap_frames)
    candidates = [(a, b) for a, b in runs(high_mask)
                  if ((b - a - 1) * hop_length + frame_length) / sr >= min_speech_ms / 1000]
    if not candidates:
        raise ValueError('No sustained speech segment: check audio or endpoint settings')
    core_a, core_b = max(candidates, key=lambda ab: (ab[1] - ab[0], float(f['energy'][ab[0]:ab[1]].sum())))
    # A high ZCR frame must also exceed the energy floor; noise alone cannot extend.
    low_mask = smooth >= low
    if use_zcr:
        weak_fricative = (f['zcr'] >= zcr_threshold) & (raw >= max(low - 5, noise + 3))
        low_mask |= weak_fricative
    low_mask = bridge_short_gaps(low_mask, gap_frames)
    limit = max(0, round(extend_ms * sr / 1000 / hop_length))
    a, b = core_a, core_b
    while a > max(0, core_a - limit) and low_mask[a - 1]:
        a -= 1
    while b < min(len(low_mask), core_b + limit) and low_mask[b]:
        b += 1
    margin = round(margin_ms * sr / 1000)
    start = max(0, int(f['starts'][a]) - margin)
    stop = min(len(y), int(f['starts'][b - 1]) + frame_length + margin)
    if stop - start < frame_length:
        raise ValueError('Trimmed segment is too short')
    excluded = [(int(f['starts'][x]), min(len(y), int(f['starts'][z - 1]) + frame_length))
                for x, z in candidates if (x, z) != (core_a, core_b)]
    if excluded:
        warnings.append('Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói')
    return {'start_sample': start, 'end_sample': stop, 'start_frame': a, 'end_frame': b - 1,
            'core_start_frame': core_a, 'core_end_frame': core_b - 1,
            'noise_db': noise, 'peak_db': peak, 'high_threshold_db': high,
            'low_threshold_db': low, 'smoothed_log_energy_db': smooth,
            'features': f, 'other_segments': excluded, 'warnings': warnings,
            'margin_ms': margin_ms}


def trim_endpoint(y, sr=16000, **kwargs):
    info = detect_endpoint(y, sr, **kwargs)
    return np.asarray(y)[info['start_sample']:info['end_sample']].copy(), info
