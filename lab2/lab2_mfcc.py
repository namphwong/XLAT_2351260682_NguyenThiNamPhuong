"""MFCC pipeline matching the Lab 2 formulas, with explicit frame alignment."""
import numpy as np
from scipy.signal import lfilter
from scipy.fft import dct
from lab2_time_features import frame_signal


def hz_to_mel(frequency):
    frequency = np.asarray(frequency, dtype=np.float64)
    if np.any(frequency < 0):
        raise ValueError('Frequency must be nonnegative')
    return 1125 * np.log1p(frequency / 700)


def mel_to_hz(mel):
    return 700 * np.expm1(np.asarray(mel, dtype=np.float64) / 1125)


def mel_filterbank(sr=16000, n_fft=512, n_mels=24):
    if sr <= 0 or n_fft < 2 or n_mels < 1:
        raise ValueError('Invalid filterbank settings')
    frequencies = np.fft.rfftfreq(n_fft, 1 / sr)
    mel_points = np.linspace(hz_to_mel(0), hz_to_mel(sr / 2), n_mels + 2)
    hz_points = mel_to_hz(mel_points)
    bank = np.zeros((n_mels, len(frequencies)))
    for m in range(n_mels):
        left, center, right = hz_points[m:m + 3]
        rising = (frequencies - left) / (center - left)
        falling = (right - frequencies) / (right - center)
        bank[m] = np.maximum(0, np.minimum(rising, falling))
    if np.any(bank.sum(axis=1) == 0):
        raise ValueError('Empty Mel filter: increase n_fft or reduce n_mels')
    return bank, frequencies, hz_points


def mfcc_details(y, sr=16000, frame_length=400, hop_length=160, n_fft=512,
                 n_mels=24, n_mfcc=13, alpha=0.97, use_cmn=True, eps=1e-9):
    """Preemphasis -> full L-frame Hamming -> padded FFT -> Mel -> ln -> DCT-II.

    All feature matrices have frames in rows. The FFT is padded after the
    400-sample frame, rather than framing 512 samples as librosa STFT does.
    """
    if not 0 <= alpha < 1 or eps <= 0 or not 1 <= n_mfcc <= n_mels:
        raise ValueError('Invalid MFCC settings')
    if n_fft < frame_length:
        raise ValueError('n_fft must be >= frame_length')
    y = np.asarray(y, dtype=np.float64)
    if y.ndim != 1 or not np.isfinite(y).all():
        raise ValueError('Expected finite mono audio')
    emphasized = lfilter([1, -alpha], [1], y)
    frames, starts = frame_signal(emphasized, frame_length, hop_length)
    windowed = frames * np.hamming(frame_length)
    power = np.abs(np.fft.rfft(windowed, n=n_fft, axis=1)) ** 2 / n_fft
    bank, frequencies, hz_points = mel_filterbank(sr, n_fft, n_mels)
    mel_energy = power @ bank.T
    log_mel = np.log(mel_energy + eps)
    raw_mfcc = dct(log_mel, type=2, axis=1, norm='ortho')[:, :n_mfcc]
    features = raw_mfcc - raw_mfcc.mean(axis=0, keepdims=True) if use_cmn else raw_mfcc.copy()
    if not np.isfinite(features).all():
        raise ValueError('Nonfinite MFCC output')
    return {'mfcc': features, 'raw_mfcc': raw_mfcc, 'log_mel': log_mel,
            'mel_energy': mel_energy, 'power': power, 'filterbank': bank,
            'frequencies': frequencies, 'mel_hz_points': hz_points,
            'times': (starts + (frame_length - 1) / 2) / sr,
            'starts': starts, 'emphasized': emphasized,
            'dropped_tail_samples': len(y) - (starts[-1] + frame_length)}


def mfcc_feature(y, sr=16000, **kwargs):
    """Return a (T, n_mfcc) array suitable for frame-to-frame DTW."""
    return mfcc_details(y, sr, **kwargs)['mfcc']
