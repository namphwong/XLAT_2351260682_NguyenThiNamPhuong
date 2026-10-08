"""Evaluate the locked Lab 2 recognizer on every held-out recording."""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from lab2_data import LABELS, write_csv
from lab2_recognizer import NearestTemplateRecognizer, decoded_audio_hash, read_wav


def summarize_results(rows, labels=LABELS):
    """Rows are complete predictions; confusion matrix rows=true, columns=predicted."""
    labels = list(labels)
    if not rows or not labels or len(set(labels)) != len(labels):
        raise ValueError('Nonempty predictions and unique labels are required')
    if len({row['file'] for row in rows}) != len(rows):
        raise ValueError('Duplicate query file in evaluation')
    for row in rows:
        if row['true_label'] not in labels or row['predicted_label'] not in labels:
            raise ValueError('Unknown true/predicted label')
        ranked = [row[f'top{i}_label'] for i in range(1, 4)]
        scores = np.array([row[f'top{i}_score'] for i in range(1, 4)], dtype=float)
        if (len(set(ranked)) != 3 or not set(ranked).issubset(labels) or
                row['predicted_label'] != ranked[0] or not np.isfinite(scores).all() or
                np.any(scores < 0) or np.any(np.diff(scores) < 0)):
            raise ValueError('Invalid distinct-label top-3 ranking or score order')
    true = [row['true_label'] for row in rows]
    predicted = [row['predicted_label'] for row in rows]
    cm = confusion_matrix(true, predicted, labels=labels)
    support = cm.sum(axis=1)
    normalized = np.divide(cm, support[:, None], out=np.zeros(cm.shape, dtype=float),
                           where=support[:, None] != 0)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true, predicted, labels=labels, zero_division=0)
    correct = int(np.trace(cm))
    top_k_correct = {str(k): sum(row['true_label'] in [row[f'top{i}_label']
                                                    for i in range(1, k + 1)] for row in rows)
                     for k in (1, 2, 3)}
    metrics = {'n_test': len(rows), 'n_correct': correct, 'n_errors': len(rows) - correct,
               'accuracy': float(accuracy_score(true, predicted)),
               'top_k_correct': top_k_correct,
               'top_k_accuracy': {k: count / len(rows) for k, count in top_k_correct.items()},
               'labels': labels, 'confusion_matrix': cm.tolist(),
               'confusion_matrix_row_normalized': normalized.tolist(),
               'confusion_matrix_axes': 'rows=true labels, columns=predicted labels',
               'zero_division': 0,
               'per_label': [{'label': label, 'support': int(support[i]),
                              'correct': int(cm[i, i]), 'precision': float(precision[i]),
                              'recall': float(recall[i]), 'f1': float(f1[i])}
                             for i, label in enumerate(labels)],
               'macro_precision': float(precision.mean()),
               'macro_recall': float(recall.mean()), 'macro_f1': float(f1.mean())}
    assert metrics['accuracy'] == correct / len(rows)
    assert top_k_correct['1'] == correct and int(cm.sum()) == len(rows)
    return metrics


def evaluate_test_set(model, recognition_results=None):
    """Evaluate every manifest test row; optional existing results must cover all tests.

    Existing results are from the current model's Phase 7 run, not manually
    supplied labels. Input hashes are checked even when results are reused.
    """
    test = [row for row in model.split_rows if row['split'] == 'test']
    if not test:
        raise ValueError('No test recordings in the locked split')
    if recognition_results is not None and set(recognition_results) != {r['file'] for r in test}:
        raise ValueError('Recognition results must cover exactly every held-out test file')
    training_files = {t['file'] for t in model.templates}
    training_hashes = {t['audio_hash'] for t in model.templates}
    rows = []
    for item in test:
        relative = Path(item['file'])
        if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != item['label']:
            raise ValueError('Invalid dataset-relative test path')
        if item['file'] in training_files or item['audio_hash'] in training_hashes:
            raise ValueError('Train/test leakage detected')
        query = model.project_root / 'dataset' / relative
        y, sr = read_wav(query, model.sample_rate)
        digest = decoded_audio_hash(y, sr)
        if digest != item['audio_hash']:
            raise ValueError(f'Test source changed: {relative}')
        result = (model.recognize_wav(query) if recognition_results is None
                  else recognition_results[item['file']])
        if result['query_audio_hash'] != digest or result['n_templates'] != len(model.templates):
            raise ValueError('Recognition provenance does not match current test/model')
        ranking = result['label_ranking']
        if (len(ranking) != len(LABELS) or {r['label'] for r in ranking} != set(LABELS) or
                any(r['template_file'] not in training_files for r in ranking) or
                any(t['label'] != r['label'] for r in ranking for t in model.templates
                    if t['file'] == r['template_file'])):
            raise ValueError('Invalid label ranking or nontraining winning template')
        true_rank, true_result = next((i, r) for i, r in enumerate(ranking, 1)
                                      if r['label'] == item['label'])
        row = {'file': item['file'], 'true_label': item['label'],
               'predicted_label': result['prediction'],
               'correct': item['label'] == result['prediction'],
               'winning_template': result['winning_template'],
               'score_gap': result['score_gap'], 'true_label_rank': true_rank,
               'true_label_score': true_result['score'],
               'true_label_template': true_result['template_file'],
               'true_minus_pred_score': true_result['score'] - result['score'],
               'n_frames': result['n_frames'], 'input_duration_s': result['input_duration_s'],
               'trimmed_duration_s': result['trimmed_duration_s'],
               'endpoint_warnings': '; '.join(result['endpoint_warnings']),
               'query_audio_hash': digest}
        for i, candidate in enumerate(ranking[:3], 1):
            row.update({f'top{i}_label': candidate['label'], f'top{i}_score': candidate['score'],
                        f'top{i}_template': candidate['template_file']})
        rows.append(row)
    metrics = summarize_results(rows)
    metrics.update(n_templates=len(model.templates),
                   baseline='endpoint 80 ms + MFCC 13 CMN + normalized Euclidean DTW; min per label',
                   split_sha256=model.metadata['split_sha256'],
                   evaluation_policy='all held-out files; no threshold or parameter tuning on test',
                   unknown_rejection=False)
    return rows, metrics


def save_evaluation(project_root, rows, metrics):
    root = Path(project_root)
    write_csv(root / 'results.csv', rows, list(rows[0]))
    labels = metrics['labels']
    for name, key in [('outputs/phase8_confusion_matrix.csv', 'confusion_matrix'),
                      ('outputs/phase8_confusion_matrix_normalized.csv', 'confusion_matrix_row_normalized')]:
        table = [{'true_label': label, **dict(zip(labels, values))}
                 for label, values in zip(labels, metrics[key])]
        write_csv(root / name, table, ['true_label', *labels])
    write_csv(root / 'outputs/phase8_per_label_metrics.csv', metrics['per_label'], list(metrics['per_label'][0]))
    (root / 'outputs/phase8_metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2),
                                           encoding='utf-8')
    provenance = {'split_sha256': metrics['split_sha256'],
                  'test_files': [r['file'] for r in rows],
                  'test_audio_hashes': {r['file']: r['query_audio_hash'] for r in rows},
                  'configuration_and_code_sha256': {
                      name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                      for name in ['mfcc_config.json', 'endpoint_config.json', 'dtw_config.json',
                                   'recognizer_config.json', 'lab2_mfcc.py', 'lab2_endpoint.py',
                                   'lab2_dtw.py', 'lab2_recognizer.py', 'lab2_evaluation.py']}}
    (root / 'outputs/phase8_evaluation_provenance.json').write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate all locked Lab 2 test recordings')
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    model = NearestTemplateRecognizer.from_project(args.project_root)
    rows, metrics = evaluate_test_set(model)
    save_evaluation(args.project_root, rows, metrics)
    print(f"Accuracy: {metrics['n_correct']}/{metrics['n_test']} = {metrics['accuracy']:.1%}")
    print(f"Top-2: {metrics['top_k_accuracy']['2']:.1%}; top-3: {metrics['top_k_accuracy']['3']:.1%}")
    print(f"Saved results.csv and Phase 8 metric files to {args.project_root.resolve()}")
