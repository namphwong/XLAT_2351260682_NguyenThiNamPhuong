"""Short-time speech analysis implemented with NumPy for Lab 2."""
import numpy as np


def frame_signal(y, frame_length=400, hop_length=160):
    """Return complete rectangular frames and sample starts; drop partial tail."""
    y = np.asarray(y, dtype=np.float64)
    if y.ndim != 1 or not np.isfinite(y).all():
        raise ValueError('Expected a finite mono signal')
    if not isinstance(frame_length, (int, np.integer)) or frame_length < 2:
        raise ValueError('frame_length must be an integer >= 2')
    if not isinstance(hop_length, (int, np.integer)) or hop_length < 1:
        raise ValueError('hop_length must be a positive integer')
    if len(y) < frame_length:
        raise ValueError('Signal is shorter than one complete frame')
    starts = np.arange(0, len(y) - frame_length + 1, hop_length)
    frames = np.stack([y[s:s + frame_length] for s in starts])
    return frames, starts


def time_features(y, sr=16000, frame_length=400, hop_length=160, eps=1e-9):
    """Hamming energy/RMS/magnitude; rectangular ZCR using zero >= 0."""
    if sr <= 0 or eps <= 0:
        raise ValueError('sr and eps must be positive')
    frames, starts = frame_signal(y, frame_length, hop_length)
    windowed = frames * np.hamming(frame_length)
    energy = np.sum(windowed ** 2, axis=1)
    magnitude = np.sum(np.abs(windowed), axis=1)
    rms = np.sqrt(energy / frame_length)
    # A sign difference contributes 2 in the formula; each crossing / L.
    zcr = np.sum((frames[:, 1:] >= 0) != (frames[:, :-1] >= 0), axis=1) / frame_length
    return {
        'frames': frames, 'starts': starts,
        'times': (starts + (frame_length - 1) / 2) / sr,
        'energy': energy, 'log_energy_db': 10 * np.log10(energy + eps),
        'rms': rms, 'magnitude': magnitude, 'zcr': zcr,
        'dropped_tail_samples': len(y) - (starts[-1] + frame_length),
    }


def normalized_autocorrelation(frame):
    """Remove DC, apply Hamming, and normalize one-sided correlation by R[0]."""
    frame = np.asarray(frame, dtype=np.float64)
    if frame.ndim != 1 or not len(frame) or not np.isfinite(frame).all():
        raise ValueError('Expected a finite nonempty frame')
    windowed = (frame - frame.mean()) * np.hamming(len(frame))
    r = np.correlate(windowed, windowed, mode='full')[len(frame) - 1:]
    if r[0] <= np.finfo(float).tiny:
        return np.zeros(len(frame))
    return r / r[0]


def pitch_candidate(frame, sr=16000, fmin=70, fmax=400, min_correlation=0.3):
    """Illustrative autocorrelation estimate, not a validated pitch tracker."""
    if not 0 < fmin < fmax < sr / 2:
        raise ValueError('Invalid pitch search range')
    r = normalized_autocorrelation(frame)
    lo = max(1, int(np.ceil(sr / fmax)))
    hi = min(len(r) - 2, int(np.floor(sr / fmin)))
    if hi < lo:
        raise ValueError('Frame too short for pitch range')
    peaks = [k for k in range(lo, hi + 1) if r[k] > r[k - 1] and r[k] >= r[k + 1]]
    if not peaks:
        return {'lag': None, 'f0_hz': None, 'correlation': 0.0, 'acf': r}
    lag = max(peaks, key=lambda k: r[k])
    strength = float(r[lag])
    return {'lag': lag if strength >= min_correlation else None,
            'f0_hz': sr / lag if strength >= min_correlation else None,
            'correlation': strength, 'acf': r}


def illustrative_frames(features, sr=16000):
    """Select examples from longest high-energy run; labels remain candidates."""
    energy, zcr, frames = features['energy'], features['zcr'], features['frames']
    active = energy >= energy.max() * 10 ** (-18 / 10)
    indices = np.flatnonzero(active)
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
    main = max(groups, key=len)
    strong = main[energy[main] >= energy[main].max() * 10 ** (-6 / 10)]
    estimates = {int(i): pitch_candidate(frames[i], sr) for i in strong}
    voiced = max(strong, key=lambda i: estimates[int(i)]['correlation'])
    # Prefer low energy outside the main region for a background example.
    outside = np.flatnonzero((np.arange(len(frames)) < main[0]) |
                             (np.arange(len(frames)) > main[-1]))
    background = int(outside[np.argmin(energy[outside])]) if len(outside) else int(np.argmin(energy))
    # Largest ZCR in the main region is only a contrast example, not phonetic truth.
    high_zcr = int(main[np.argmax(zcr[main])])
    # Inspect onset vicinity as well; weak fricatives may precede strong speech.
    vicinity = np.arange(max(0, main[0] - 15), main[-1] + 1)
    candidates = vicinity[(energy[vicinity] >= energy[main].max() * 10 ** (-35 / 10)) &
                          (zcr[vicinity] >= 0.10)]
    nonperiodic = [int(i) for i in candidates
                  if pitch_candidate(frames[i], sr)['correlation'] < 0.30]
    unvoiced = max(nonperiodic, key=lambda i: zcr[i]) if nonperiodic else None
    return {'background': background, 'voiced_candidate': int(voiced),
            'high_zcr_candidate': high_zcr, 'unvoiced_candidate': unvoiced, 'main_indices': main,
            'voiced_pitch': estimates[int(voiced)]}
