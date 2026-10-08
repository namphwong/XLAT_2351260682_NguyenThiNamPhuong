"""Recognition checks: label aggregation, held-out pipeline and leakage guards."""
from pathlib import Path
import json
import tempfile
import unittest

import numpy as np
import soundfile as sf

from lab2_recognizer import NearestTemplateRecognizer, read_wav
from lab2_dtw import dtw_details
from lab2_mfcc import mfcc_feature
from lab2_endpoint import trim_endpoint

ROOT = Path(__file__).resolve().parents[1]


class RecognizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = NearestTemplateRecognizer.from_project(ROOT)

    def test_minimum_per_label_and_distinct_top_three(self):
        config = self.model.mfcc_config
        # Several nearest templates can share a label; top-3 must still be distinct.
        templates = [{'file': file, 'label': label, 'mfcc': np.full((2, 13), value)}
                     for file, label, value in [('a1', 'a', 1), ('a2', 'a', 2),
                                                 ('b1', 'b', 3), ('b2', 'b', 4), ('c1', 'c', 5)]]
        model = NearestTemplateRecognizer(templates, config, {})
        result = model.recognize_features(np.zeros((2, 13)))
        self.assertEqual([r['label'] for r in result['top_k']], ['a', 'b', 'c'])
        self.assertEqual(result['winning_template'], 'a1')
        self.assertAlmostEqual(result['score'], np.sqrt(13))
        self.assertEqual(len(result['template_ranking']), 5)
        self.assertAlmostEqual(result['score_gap'], 2 * np.sqrt(13))

    def test_tie_order_and_invalid_features(self):
        template = np.zeros((2, 13))
        model = NearestTemplateRecognizer([
            {'label': 'b', 'file': 'b1', 'mfcc': template},
            {'label': 'a', 'file': 'a2', 'mfcc': template},
            {'label': 'a', 'file': 'a1', 'mfcc': template}], self.model.mfcc_config, {})
        result = model.recognize_features(template, top_k=9)
        self.assertEqual(result['prediction'], 'a')
        self.assertEqual(result['winning_template'], 'a1')
        self.assertEqual(len(result['top_k']), 2)
        for feature in [np.empty((0, 13)), np.ones((2, 12)), np.full((2, 13), np.nan)]:
            with self.assertRaises(ValueError):
                model.recognize_features(feature)
        for top_k in [0, -1, 1.5, True]:
            with self.assertRaises(ValueError):
                model.recognize_features(template, top_k)

    def test_only_train_templates(self):
        self.assertEqual(len(self.model.templates), 15)
        test_files = {r['file'] for r in self.model.split_rows if r['split'] == 'test'}
        self.assertTrue(test_files.isdisjoint({r['file'] for r in self.model.templates}))
        self.assertTrue(all(t['split'] == 'train' for t in self.model.templates))

    def test_held_out_wav_matches_cached_feature_scores(self):
        relative = 'khong/khong_04.wav'
        result = self.model.recognize_wav(ROOT / 'dataset' / relative)
        with np.load(ROOT / 'features' / 'mfcc' / Path(relative).with_suffix('.npz')) as saved:
            cached = saved['mfcc']
        y, sr = read_wav(ROOT / 'dataset' / relative)
        trimmed, endpoint = trim_endpoint(y, sr, **self.model.endpoint_config)
        np.testing.assert_allclose(mfcc_feature(trimmed, sr, **self.model.mfcc_config), cached,
                                   atol=1e-12, rtol=1e-12)
        expected = {t['file']: dtw_details(cached, t['mfcc'])['normalized_cost']
                    for t in self.model.templates}
        self.assertEqual(result['n_templates'], 15)
        for row in result['template_ranking']:
            self.assertAlmostEqual(row['score'], expected[row['template_file']], places=12)
        self.assertEqual(result['start_sample'], endpoint['start_sample'])
        self.assertEqual(result['end_sample'], endpoint['end_sample'])

    def test_training_audio_and_copy_are_rejected(self):
        source = ROOT / 'dataset' / self.model.templates[0]['file']
        with self.assertRaisesRegex(ValueError, 'training audio'):
            self.model.recognize_wav(source)
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / 'new_name.wav'
            y, sr = read_wav(source)
            sf.write(copied, y, sr, subtype='PCM_16')
            with self.assertRaisesRegex(ValueError, 'training audio'):
                self.model.recognize_wav(copied)

    def test_format_silence_and_stale_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'silence.wav'
            sf.write(path, np.zeros(16000), 16000, subtype='PCM_16')
            with self.assertRaisesRegex(ValueError, 'speech'):
                self.model.recognize_wav(path)
            sf.write(path, np.zeros((16000, 2)), 16000, subtype='PCM_16')
            with self.assertRaisesRegex(ValueError, 'mono'):
                read_wav(path)
            root = Path(directory)
            (root / 'data_split.csv').write_bytes((ROOT / 'data_split.csv').read_bytes())
            metadata = dict(self.model.metadata)
            metadata['split_sha256'] = 'outdated'
            (root / 'mfcc_config.json').write_text(json.dumps(metadata), encoding='utf-8')
            (root / 'endpoint_config.json').write_bytes((ROOT / 'endpoint_config.json').read_bytes())
            with self.assertRaisesRegex(ValueError, 'Split changed'):
                NearestTemplateRecognizer.from_project(root)


if __name__ == '__main__':
    unittest.main()
