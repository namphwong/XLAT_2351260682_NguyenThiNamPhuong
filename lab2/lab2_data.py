"""Data collection utilities for Lab 2; no recognition or endpoint trimming."""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import re
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

LABELS = ['khong', 'mot', 'hai', 'ba', 'bon']
NAMES = dict(zip(LABELS, ['không', 'một', 'hai', 'ba', 'bốn']))
FIELDS = ['file', 'label', 'sample_rate', 'channels', 'subtype', 'duration_s',
          'peak', 'rms', 'clipping_percent', 'leading_quiet_s', 'trailing_quiet_s',
          'audio_hash', 'format_ok', 'warnings', 'error']


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def quiet_edges(y, sr):
    """Preliminary RMS heuristic for recording QA, not speech boundaries."""
    hop = max(1, round(sr * 0.01))
    levels = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2))
                       for i in range(0, len(y), hop)])
    active = np.flatnonzero(levels > max(1e-4, levels.max() * 0.05))
    if not len(active):
        return len(y) / sr, len(y) / sr
    return active[0] * hop / sr, max(0, len(y) - (active[-1] + 1) * hop) / sr


def audit_dataset(root):
    root = Path(root)
    rows = []
    for label in LABELS:
        for path in sorted((root / label).glob('*')):
            if path.suffix.lower() != '.wav':
                continue
            row = dict.fromkeys(FIELDS, '')
            row.update(file=path.relative_to(root).as_posix(), label=label)
            try:
                info = sf.info(path)
                y, sr = sf.read(path, dtype='float64', always_2d=True)
                if not len(y) or not np.isfinite(y).all():
                    raise ValueError('Tín hiệu rỗng hoặc chứa giá trị không hữu hạn')
                mono = y.mean(axis=1)
                peak = float(np.max(np.abs(y)))
                rms = float(np.sqrt(np.mean(y ** 2)))
                clip = float(np.mean(np.abs(y) >= 0.999) * 100)
                lead, trail = quiet_edges(mono, sr)
                fmt = sr == 16000 and info.channels == 1 and info.subtype.startswith('PCM_') and info.format in ('WAV', 'WAVEX')
                notes = []
                if not fmt:
                    notes.append('Cần WAV PCM mono 16 kHz')
                if peak <= 1e-5:
                    notes.append('Không có tín hiệu; cần thu lại')
                elif rms < 0.005:
                    notes.append('Âm lượng nhỏ; nghe lại')
                if clip > 0:
                    notes.append('Có mẫu gần full-scale; nghe/kiểm tra clipping')
                if lead < 0.2 or trail < 0.2:
                    notes.append('Khoảng yên đầu/cuối ngắn; nghe lại')
                if lead > 0.5 or trail > 0.5:
                    notes.append('Khoảng yên đầu/cuối dài hơn khuyến nghị')
                # Hash decoded audio and format, not headers: catches copied utterances.
                digest = hashlib.sha256()
                digest.update(f'{sr}:{info.channels}:'.encode())
                digest.update(np.ascontiguousarray(y, dtype='<f8').tobytes())
                row.update(sample_rate=sr, channels=info.channels, subtype=info.subtype,
                           duration_s=round(len(y) / sr, 4), peak=round(peak, 6),
                           rms=round(rms, 6), clipping_percent=round(clip, 5),
                           leading_quiet_s=round(lead, 3), trailing_quiet_s=round(trail, 3),
                           audio_hash=digest.hexdigest(), format_ok=fmt,
                           warnings='; '.join(notes))
            except Exception as exc:
                row.update(format_ok=False, error=str(exc))
            rows.append(row)
    groups = {}
    for row in rows:
        if row['audio_hash']:
            groups.setdefault(row['audio_hash'], []).append(row)
    for group in groups.values():
        if len(group) > 1:
            for row in group:
                row['warnings'] += ('; ' if row['warnings'] else '') + 'Trùng nội dung âm thanh'
    return rows


def dataset_issues(rows, minimum=5):
    issues = []
    for label in LABELS:
        count = sum(row['label'] == label for row in rows)
        if count < minimum:
            issues.append(f'{NAMES[label]}: {count}/{minimum} file, thiếu {minimum - count}')
    if any(row['error'] or not row['format_ok'] for row in rows):
        issues.append('Có file lỗi hoặc chưa đúng WAV PCM mono 16 kHz')
    if any(row['peak'] != '' and row['peak'] <= 1e-5 for row in rows):
        issues.append('Có file không có tín hiệu')
    hashes = [row['audio_hash'] for row in rows if row['audio_hash']]
    if len(set(hashes)) != len(hashes):
        issues.append('Có bản ghi trùng nội dung; cần các lần nói độc lập')
    return issues


def lock_split(rows, manifest_path, n_templates=3, minimum=5):
    """Create a fixed split once; reject data changes rather than silently resplit."""
    issues = dataset_issues(rows, minimum)
    if issues:
        raise ValueError('\n'.join(issues))
    fields = ['file', 'label', 'split', 'audio_hash']
    expected = []
    for label in LABELS:
        files = sorted((row for row in rows if row['label'] == label), key=lambda r: r['file'])
        if not 0 < n_templates < len(files):
            raise ValueError('Cần ít nhất một template và một test mỗi nhãn')
        for i, row in enumerate(files):
            expected.append({key: row[key] for key in ['file', 'label', 'audio_hash']} | {'split': 'train' if i < n_templates else 'test'})
    manifest_path = Path(manifest_path)
    if manifest_path.exists():
        with manifest_path.open(encoding='utf-8-sig', newline='') as handle:
            saved = list(csv.DictReader(handle))
        if saved != expected:
            raise ValueError('Dữ liệu/cấu hình split đã thay đổi. Kiểm tra và lưu bản cũ trước khi chủ động xóa data_split.csv để chốt lại split.')
        return saved
    write_csv(manifest_path, expected, fields)
    return expected


def convert_recording(source, destination, target_sr=16000):
    """Explicit conversion, retaining source, silence and amplitude; no overwrite."""
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise FileExistsError(f'Không ghi đè: {destination}')
    y, sr = sf.read(source, dtype='float64', always_2d=True)
    if not len(y) or not np.isfinite(y).all():
        raise ValueError('Tín hiệu rỗng hoặc không hữu hạn')
    y = y.mean(axis=1)
    if sr != target_sr:
        ratio = Fraction(target_sr, sr)
        y = resample_poly(y, ratio.numerator, ratio.denominator)
    if np.max(np.abs(y)) >= 1:
        raise ValueError('Biên độ đạt/vượt full-scale; kiểm tra gain nguồn trước khi chuyển đổi PCM')
    destination.parent.mkdir(parents=True, exist_ok=True)
    sf.write(destination, y, target_sr, subtype='PCM_16')
    return destination


def prepare_mp3_dataset(root, manifest_path):
    """Convert original recorder names to numbered WAVs; verify on later runs."""
    root, manifest_path = Path(root), Path(manifest_path)
    fields = ['source', 'destination', 'source_sha256', 'wav_sha256',
              'source_sample_rate', 'source_channels', 'target_sample_rate', 'target_subtype']
    records = []
    if manifest_path.exists():
        with manifest_path.open(encoding='utf-8-sig', newline='') as handle:
            records = list(csv.DictReader(handle))
    known = {r['destination']: r for r in records}
    sources = []
    for label in LABELS:
        for source in (root / label).glob('*'):
            match = re.fullmatch(re.escape(label) + r'(?:\((\d+)\))?\.mp3', source.name, re.I)
            if match:
                number = int(match.group(1) or 0) + 1
                sources.append((label, number, source))
    destinations = [f'{label}/{label}_{number:02}.wav' for label, number, _ in sources]
    if len(set(destinations)) != len(destinations):
        raise ValueError('Nhiều MP3 ánh xạ tới cùng một tên WAV; kiểm tra lại tên file')
    for label, number, source in sorted(sources):
        destination = root / label / f'{label}_{number:02}.wav'
        relative = destination.relative_to(root).as_posix()
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if destination.exists():
            old = known.get(relative)
            wav_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
            if not old or old['source_sha256'] != source_hash or old['wav_sha256'] != wav_hash:
                raise ValueError(f'Không ghi đè {relative}: file nguồn/đích đã thay đổi hoặc chưa có manifest chuyển đổi')
            continue
        info = sf.info(source)
        convert_recording(source, destination)
        record = dict(source=source.relative_to(root).as_posix(), destination=relative,
                      source_sha256=source_hash,
                      wav_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                      source_sample_rate=info.samplerate, source_channels=info.channels,
                      target_sample_rate=16000, target_subtype='PCM_16')
        records = [r for r in records if r['destination'] != relative] + [record]
        records.sort(key=lambda r: r['destination'])
        known[relative] = record
        write_csv(manifest_path, records, fields)
    return records
