"""Delta formula and controlled train/test pipeline checks."""
from pathlib import Path
import json
import unittest

import numpy as np

from lab2_experiments import delta_features, extract_variant, rank_templates, VARIANTS
from lab2_mfcc import mfcc_feature
from lab2_recognizer import MFCC_KEYS, NearestTemplateRecognizer

ROOT = Path(__file__).resolve().parents[1]


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        metadata = json.loads((ROOT / 'mfcc_config.json').read_text(encoding='utf-8'))
        cls.mfcc = {key: metadata[key] for key in MFCC_KEYS}
        cls.endpoint = metadata['endpoint_config']

    def test_delta_known_ramp_and_edges(self):
        ramp = np.arange(7, dtype=float)[:, None]
        expected = np.array([.5, .8, 1, 1, 1, .8, .5])[:, None]
        np.testing.assert_allclose(delta_features(ramp), expected, atol=1e-15)
        np.testing.assert_allclose(delta_features(np.c_[ramp, -3*ramp]), np.c_[expected, -3*expected])
        np.testing.assert_array_equal(delta_features(np.ones((1, 13))), np.zeros((1, 13)))
        np.testing.assert_array_equal(delta_features(np.full((8, 13), 4)), np.zeros((8, 13)))
        np.testing.assert_allclose(delta_features([[0], [10]]), [[3], [3]])

    def test_delta_translation_invariance_and_bad_input(self):
        rng = np.random.default_rng(29)
        x = rng.normal(size=(13, 13))
        np.testing.assert_allclose(delta_features(x), delta_features(x - x.mean(axis=0)), atol=1e-15)
        for invalid in [np.empty((0, 13)), np.ones(13), np.full((2, 13), np.inf)]:
            with self.assertRaises(ValueError):
                delta_features(invalid)
        for radius in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                delta_features(x, radius)

    def test_controlled_extraction_changes_only_one_factor(self):
        sr = 16000
        y = np.r_[np.zeros(4000), .05*np.sin(2*np.pi*180*np.arange(8000)/sr), np.zeros(4000)]
        source = y.copy()
        baseline, full, dynamic = [extract_variant(y, sr, v, self.mfcc, self.endpoint) for v in VARIANTS]
        np.testing.assert_array_equal(y, source)
        self.assertEqual(full['start_sample'], 0)
        self.assertEqual(full['end_sample'], len(y))
        self.assertEqual(len(full['features']), 1+(len(y)-400)//160)
        np.testing.assert_array_equal(full['features'], mfcc_feature(y, sr, **self.mfcc))
        self.assertGreater(baseline['start_sample'], 0)
        self.assertLess(len(baseline['features']), len(full['features']))
        self.assertEqual(dynamic['features'].shape, (len(baseline['features']), 26))
        np.testing.assert_array_equal(dynamic['features'][:, :13], baseline['features'])
        np.testing.assert_array_equal(dynamic['features'][:, 13:], delta_features(baseline['features']))
        np.testing.assert_array_equal(dynamic['times'], baseline['times'])
        self.assertEqual(dynamic['start_sample'], baseline['start_sample'])
        self.assertEqual(dynamic['end_sample'], baseline['end_sample'])

    def test_ranking_matches_recognizer_and_supports_26_dimensions(self):
        rng = np.random.default_rng(7)
        templates = [{'file': f'{label}{i}', 'label': label, 'features': rng.normal(size=(i+2, 13))}
                     for label in ['c', 'b', 'a'] for i in (1, 2)]
        query = rng.normal(size=(4, 13))
        model = NearestTemplateRecognizer([{**t, 'mfcc': t['features']} for t in templates], self.mfcc, self.endpoint)
        expected = model.recognize_features(query)
        ranking, scores = rank_templates(query, templates)
        self.assertEqual(ranking, expected['label_ranking'])
        self.assertEqual(scores, expected['template_ranking'])
        query26 = np.c_[query, delta_features(query)]
        templates26 = [{**t, 'features': np.c_[t['features'], delta_features(t['features'])]} for t in templates]
        ranking26, scores26 = rank_templates(query26, templates26)
        self.assertEqual(len(ranking26), 3)
        self.assertEqual(len(scores26), 6)
        self.assertTrue(all(np.isfinite(r['score']) for r in scores26))
        with self.assertRaises(ValueError):
            rank_templates(query, templates26)


if __name__ == '__main__':
    unittest.main()
