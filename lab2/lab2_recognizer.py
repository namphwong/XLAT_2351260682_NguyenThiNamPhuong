"""Closed-set nearest-template recognition with the fixed Lab 2 pipeline."""
from pathlib import Path
import argparse
import csv
import hashlib
import json

import numpy as np
import soundfile as sf

from lab2_data import LABELS
from lab2_dtw import dtw_details
from lab2_endpoint import trim_endpoint
from lab2_mfcc import mfcc_feature

MFCC_KEYS = ('frame_length', 'hop_length', 'n_fft', 'n_mels', 'n_mfcc',
             'alpha', 'use_cmn', 'eps')


def decoded_audio_hash(y, sr):
    digest = hashlib.sha256(f'{sr}:1:'.encode())
    digest.update(np.ascontiguousarray(y, dtype='<f8').tobytes())
    return digest.hexdigest()


def read_wav(path, sr=16000):
    path = Path(path)
    info = sf.info(path)
    if (info.format != 'WAV' or info.samplerate != sr or
            info.channels != 1 or info.subtype != 'PCM_16'):
        raise ValueError('Expected WAV PCM_16, mono, 16000 Hz; convert audio first')
    y, actual_sr = sf.read(path, dtype='float64')
    if not len(y) or not np.isfinite(y).all():
        raise ValueError('Audio must be nonempty and finite')
    return y, actual_sr


class NearestTemplateRecognizer:
    """Rank labels by minimum normalized DTW over their training templates.

    Equal scores use label/file alphabetic order for deterministic results.
    No probability calibration or unknown-word rejection is performed.
    """

    def __init__(self, templates, mfcc_config, endpoint_config, sample_rate=16000):
        if sample_rate != 16000:
            raise ValueError('The Lab 2 recognizer requires 16000 Hz')
        self.sample_rate = sample_rate
        self.mfcc_config = {key: mfcc_config[key] for key in MFCC_KEYS}
        self.endpoint_config = dict(endpoint_config)
        self.templates = []
        files = set()
        for item in templates:
            feature = np.asarray(item['mfcc'], dtype=np.float64).copy()
            if (feature.ndim != 2 or feature.shape[0] == 0 or
                    feature.shape[1] != self.mfcc_config['n_mfcc'] or
                    not np.isfinite(feature).all()):
                raise ValueError('Invalid template feature matrix')
            if not item['label'] or not item['file'] or item['file'] in files:
                raise ValueError('Template labels/files must be nonempty; files unique')
            files.add(item['file'])
            feature.setflags(write=False)
            self.templates.append({**item, 'mfcc': feature})
        if not self.templates:
            raise ValueError('At least one training template is required')

    @classmethod
    def from_project(cls, project_root):
        """Load only train features and verify input/configuration provenance."""
        root = Path(project_root).resolve()
        manifest = root / 'data_split.csv'
        metadata = json.loads((root / 'mfcc_config.json').read_text(encoding='utf-8'))
        endpoint = json.loads((root / 'endpoint_config.json').read_text(encoding='utf-8'))
        if metadata['split_sha256'] != hashlib.sha256(manifest.read_bytes()).hexdigest():
            raise ValueError('Split changed after MFCC extraction; rebuild features')
        sr = metadata['sample_rate']
        endpoint_sr = endpoint.pop('sample_rate')
        if endpoint_sr != sr or endpoint != metadata['endpoint_config']:
            raise ValueError('Endpoint configurations do not match')
        with manifest.open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.DictReader(handle))
        if any(r['split'] not in ('train', 'test') or r['label'] not in LABELS for r in rows):
            raise ValueError('Unknown split or label in manifest')
        if (len({r['file'] for r in rows}) != len(rows) or
                len({r['audio_hash'] for r in rows}) != len(rows)):
            raise ValueError('Duplicate files/audio in split manifest')
        training = [r for r in rows if r['split'] == 'train']
        if any(sum(r['label'] == label for r in training) != 3 for label in LABELS):
            raise ValueError('The locked baseline requires three templates per label')
        templates = []
        for row in training:
            relative = Path(row['file'])
            if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != row['label']:
                raise ValueError('Invalid dataset-relative path')
            source = root / 'dataset' / relative
            y, actual_sr = read_wav(source, sr)
            if decoded_audio_hash(y, actual_sr) != row['audio_hash']:
                raise ValueError(f'Training source changed: {relative}')
            trimmed_path = root / 'trimmed' / relative
            trimmed, _ = read_wav(trimmed_path, sr)
            fresh_trimmed, _ = trim_endpoint(y, sr, **endpoint)
            if not np.array_equal(trimmed, fresh_trimmed):
                raise ValueError(f'Trim does not match the current endpoint: {relative}')
            cache = root / 'features' / 'mfcc' / relative.with_suffix('.npz')
            with np.load(cache, allow_pickle=False) as saved:
                if json.loads(str(saved['config_json'].item())) != metadata:
                    raise ValueError(f'Feature configuration changed: {relative}')
                if str(saved['input_sha256'].item()) != hashlib.sha256(trimmed_path.read_bytes()).hexdigest():
                    raise ValueError(f'Trimmed WAV changed: {relative}')
                feature = saved['mfcc'].copy()
            fresh_feature = mfcc_feature(trimmed, sr, **{k: metadata[k] for k in MFCC_KEYS})
            if not np.allclose(feature, fresh_feature, rtol=1e-12, atol=1e-12):
                raise ValueError(f'Cached feature does not match audio: {relative}')
            templates.append({**row, 'mfcc': feature, 'source_path': str(source.resolve()),
                              'trimmed_sha256': hashlib.sha256(trimmed_path.read_bytes()).hexdigest()})
        model = cls(templates, metadata, endpoint, sr)
        model.split_rows = rows
        model.metadata = metadata
        model.project_root = root
        return model

    def recognize_features(self, features, top_k=3):
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError('top_k must be a positive integer')
        template_scores = []
        for template in self.templates:
            result = dtw_details(features, template['mfcc'])
            template_scores.append({'label': template['label'], 'template_file': template['file'],
                                    'score': result['normalized_cost'],
                                    'total_cost': result['total_cost'], 'path_length': result['path_length']})
        template_scores.sort(key=lambda r: (r['score'], r['label'], r['template_file']))
        best_by_label = {}
        for row in template_scores:
            best_by_label.setdefault(row['label'], row)
        ranking = sorted(best_by_label.values(), key=lambda r: (r['score'], r['label'], r['template_file']))
        best = ranking[0]
        return {'prediction': best['label'], 'score': best['score'],
                'winning_template': best['template_file'],
                'score_gap': ranking[1]['score'] - best['score'] if len(ranking) > 1 else None,
                'top_k': ranking[:top_k], 'label_ranking': ranking,
                'template_ranking': template_scores, 'n_templates': len(self.templates)}

    def recognize_wav(self, path, top_k=3):
        """Process an original, untrimmed WAV; refuse training audio as a demo."""
        path = Path(path).resolve()
        y, sr = read_wav(path, self.sample_rate)
        digest = decoded_audio_hash(y, sr)
        if any(t.get('audio_hash') == digest or t.get('source_path') == str(path)
               for t in self.templates):
            raise ValueError('Query is training audio; use a held-out or new recording')
        trimmed, endpoint = trim_endpoint(y, sr, **self.endpoint_config)
        feature = mfcc_feature(trimmed, sr, **self.mfcc_config)
        result = self.recognize_features(feature, top_k)
        result.update(query_file=str(path), query_audio_hash=digest,
                      input_duration_s=len(y) / sr, trimmed_duration_s=len(trimmed) / sr,
                      n_frames=len(feature), start_sample=endpoint['start_sample'],
                      end_sample=endpoint['end_sample'], endpoint_warnings=endpoint['warnings'])
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lab 2: WAV -> endpoint -> MFCC -> nearest-template DTW')
    parser.add_argument('wav', type=Path, help='Original WAV PCM_16 mono 16 kHz outside training')
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--top-k', type=int, default=3)
    args = parser.parse_args()
    recognizer = NearestTemplateRecognizer.from_project(args.project_root)
    print(json.dumps(recognizer.recognize_wav(args.wav, args.top_k), ensure_ascii=False, indent=2))
