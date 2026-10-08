"""Independent metric/axis checks and complete held-out coverage guards."""
from pathlib import Path
import json
import unittest

import numpy as np

from lab2_evaluation import summarize_results, evaluate_test_set
from lab2_recognizer import NearestTemplateRecognizer

ROOT = Path(__file__).resolve().parents[1]


def example_rows():
    # Explicit expected confusion matrix, including an absent fourth class.
    examples = [('q1', 'a', ['b', 'c', 'a']), ('q2', 'a', ['a', 'c', 'b']),
                ('q3', 'b', ['b', 'a', 'c']), ('q4', 'c', ['a', 'c', 'b'])]
    return [{'file': file, 'true_label': true, 'predicted_label': ranking[0],
             **{f'top{i}_label': label for i, label in enumerate(ranking, 1)},
             **{f'top{i}_score': float(i) for i in range(1, 4)}}
            for file, true, ranking in examples]


class EvaluationTests(unittest.TestCase):
    def test_counts_axes_normalization_and_top_k(self):
        metrics = summarize_results(example_rows(), ['a', 'b', 'c', 'd'])
        expected = [[1, 1, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]]
        self.assertEqual(metrics['confusion_matrix'], expected)
        self.assertEqual(metrics['n_correct'], 2)
        self.assertEqual(metrics['accuracy'], 0.5)
        self.assertEqual(metrics['top_k_correct'], {'1': 2, '2': 3, '3': 4})
        np.testing.assert_array_equal(metrics['confusion_matrix_row_normalized'],
                                      [[.5, .5, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]])
        self.assertEqual(metrics['per_label'][0]['precision'], .5)
        self.assertEqual(metrics['per_label'][1]['recall'], 1)
        self.assertEqual(metrics['per_label'][2]['f1'], 0)
        self.assertEqual(metrics['per_label'][3]['support'], 0)

    def test_reject_bad_rows(self):
        with self.assertRaises(ValueError):
            summarize_results([])
        rows = example_rows()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            summarize_results([rows[0], rows[0]], ['a', 'b', 'c'])
        for updates in [{'true_label': 'unknown'}, {'predicted_label': 'c'},
                        {'top2_label': 'b'}, {'top1_score': float('nan')},
                        {'top1_score': -1}, {'top2_score': .1}]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                summarize_results([{**rows[0], **updates}, *rows[1:]], ['a', 'b', 'c'])

    def test_every_test_required_and_baseline_reproduction(self):
        model = NearestTemplateRecognizer.from_project(ROOT)
        details = json.loads((ROOT / 'outputs/phase7_recognition_details.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError, 'exactly every'):
            evaluate_test_set(model, {})
        rows, metrics = evaluate_test_set(model, details)
        self.assertEqual({r['file'] for r in rows},
                         {r['file'] for r in model.split_rows if r['split'] == 'test'})
        self.assertEqual(metrics['n_templates'], 15)
        self.assertEqual(metrics['accuracy'], .8)
        self.assertEqual(metrics['top_k_accuracy'], {'1': .8, '2': .9, '3': 1.0})
        self.assertEqual(metrics['confusion_matrix'],
                         [[0, 0, 2, 0, 0], [0, 2, 0, 0, 0], [0, 0, 2, 0, 0],
                          [0, 0, 0, 2, 0], [0, 0, 0, 0, 2]])
        bad = {k: dict(v) for k, v in details.items()}
        bad[next(iter(bad))]['query_audio_hash'] = 'stale'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            evaluate_test_set(model, bad)


if __name__ == '__main__':
    unittest.main()
