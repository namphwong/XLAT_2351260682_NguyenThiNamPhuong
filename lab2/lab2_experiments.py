"""Controlled E1/E2 experiments; preserve the Phase 8 baseline outputs."""
from pathlib import Path
import argparse
import csv
import hashlib
import json

import numpy as np

from lab2_data import LABELS, write_csv
from lab2_dtw import dtw_details, path_statistics
from lab2_endpoint import trim_endpoint
from lab2_evaluation import summarize_results
from lab2_mfcc import mfcc_details
from lab2_recognizer import MFCC_KEYS, read_wav, decoded_audio_hash

VARIANTS = [
    {'name': 'trim_mfcc13', 'trim': True, 'include_delta': False, 'dimensions': 13},
    {'name': 'no_trim_mfcc13', 'trim': False, 'include_delta': False, 'dimensions': 13},
    {'name': 'trim_mfcc_delta26', 'trim': True, 'include_delta': True, 'dimensions': 26},
]
DELTA_CONFIG = {'order': 1, 'radius_frames': 2, 'boundary': 'edge replication',
                'weight': 1.0, 'input': '13 static MFCC after per-utterance CMN',
                'extra_delta_cmn': False, 'units': 'coefficient change per frame; not per second'}


def delta_features(features, radius=2):
    """Regression delta: sum n*(c[t+n]-c[t-n]) / (2*sum n**2).

    Replicate end frames; preserve T, including one-frame inputs. Apply after
    static CMN; do not normalize the delta block again or tune its weight.
    """
    x = np.asarray(features, dtype=np.float64)
    if x.ndim != 2 or min(x.shape) == 0 or not np.isfinite(x).all():
        raise ValueError('Expected nonempty finite (frames, dimensions) features')
    if isinstance(radius, bool) or not isinstance(radius, int) or radius < 1:
        raise ValueError('Delta radius must be a positive integer')
    padded = np.pad(x, ((radius, radius), (0, 0)), mode='edge')
    delta = np.zeros_like(x)
    for n in range(1, radius + 1):
        delta += n * (padded[radius+n:radius+n+len(x)] - padded[radius-n:radius-n+len(x)])
    delta /= 2 * sum(n*n for n in range(1, radius + 1))
    return delta


def extract_variant(y, sr, variant, mfcc_config, endpoint_config):
    """Extract from original WAV, with identical processing on train/test."""
    if variant not in VARIANTS:
        raise ValueError('Use one of the predefined controlled configurations')
    y = np.asarray(y, dtype=np.float64)
    if y.ndim != 1 or not len(y) or not np.isfinite(y).all():
        raise ValueError('Expected nonempty finite mono audio')
    endpoint = None
    prepared = y
    if variant['trim']:
        prepared, endpoint = trim_endpoint(y, sr, **endpoint_config)
    details = mfcc_details(prepared, sr, **mfcc_config)
    static = details['mfcc']
    delta = delta_features(static, DELTA_CONFIG['radius_frames']) if variant['include_delta'] else np.empty((len(static), 0))
    features = np.concatenate([static, delta], axis=1)
    assert features.shape == (len(static), variant['dimensions'])
    return {'features': features, 'static_mfcc': static, 'delta': delta,
            'times': details['times'], 'prepared': prepared, 'endpoint': endpoint,
            'start_sample': endpoint['start_sample'] if endpoint else 0,
            'end_sample': endpoint['end_sample'] if endpoint else len(y)}


def rank_templates(query, templates):
    """Same label-min aggregation and tie rule as Phase 7, arbitrary feature D."""
    scores = []
    for template in templates:
        details = dtw_details(query, template['features'])
        scores.append({'label': template['label'], 'template_file': template['file'],
                       'score': details['normalized_cost'], 'total_cost': details['total_cost'],
                       'path_length': details['path_length']})
    if not scores:
        raise ValueError('Training templates are required')
    scores.sort(key=lambda r: (r['score'], r['label'], r['template_file']))
    best = {}
    for row in scores:
        best.setdefault(row['label'], row)
    return list(best.values()), scores


def _json_write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def run_experiments(project_root, progress=None):
    root = Path(project_root).resolve()
    output = root / 'experiments' / 'phase9'
    output.mkdir(parents=True, exist_ok=True)
    feature_root = root / 'features' / 'experiments'
    manifest = root / 'data_split.csv'
    split_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    metadata = json.loads((root / 'mfcc_config.json').read_text(encoding='utf-8'))
    endpoint_metadata = json.loads((root / 'endpoint_config.json').read_text(encoding='utf-8'))
    dtw_config = json.loads((root / 'dtw_config.json').read_text(encoding='utf-8'))
    if metadata['split_sha256'] != split_hash:
        raise ValueError('Split differs from locked MFCC configuration')
    sr = metadata['sample_rate']
    if sr != 16000 or endpoint_metadata.pop('sample_rate') != sr or endpoint_metadata != metadata['endpoint_config']:
        raise ValueError('Endpoint configuration/sample rate mismatch')
    mfcc_config = {k: metadata[k] for k in MFCC_KEYS}
    with manifest.open(encoding='utf-8-sig', newline='') as handle:
        split = list(csv.DictReader(handle))
    if len(split) != 25 or len({r['file'] for r in split}) != 25 or len({r['audio_hash'] for r in split}) != 25:
        raise ValueError('Expected 25 distinct recordings in the locked split')
    if any(r['split'] not in ('train', 'test') or r['label'] not in LABELS for r in split):
        raise ValueError('Invalid split/label')
    for label in LABELS:
        if any(sum(r['label'] == label and r['split'] == group for r in split) != count
               for group, count in [('train', 3), ('test', 2)]):
            raise ValueError('Expected three training and two test recordings per label')
    for row in split:
        relative = Path(row['file'])
        if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != row['label']:
            raise ValueError('Invalid dataset-relative file')
        y, actual_sr = read_wav(root / 'dataset' / relative, sr)
        if decoded_audio_hash(y, actual_sr) != row['audio_hash']:
            raise ValueError(f"Source WAV changed: {row['file']}")
    protected = [manifest, root / 'results.csv', root / 'outputs/phase8_metrics.json',
                 root / 'mfcc_config.json', root / 'endpoint_config.json', root / 'dtw_config.json',
                 root / 'recognizer_config.json', *sorted((root / 'dataset').rglob('*.wav'))]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    summary, all_predictions, all_feature_rows, runs = [], [], [], {}
    for variant in VARIANTS:
        name = variant['name']
        if progress: progress(f'{name}: extracting fresh features for all 25 WAVs')
        directory = output / name
        directory.mkdir(parents=True, exist_ok=True)
        config = {'variant': variant, 'mfcc': metadata, 'endpoint_applied': variant['trim'],
                  'delta': DELTA_CONFIG if variant['include_delta'] else None,
                  'dtw': dtw_config, 'split_sha256': split_hash,
                  'label_score': 'minimum normalized DTW over three training files per label',
                  'tie_break': 'score, label alphabetical, template filename alphabetical'}
        _json_write(directory / 'config.json', config)
        features, feature_rows = {}, []
        for item in split:
            relative = Path(item['file'])
            source = root / 'dataset' / relative
            y, actual_sr = read_wav(source, sr)
            details = extract_variant(y, actual_sr, variant, mfcc_config, endpoint_metadata)
            features[item['file']] = details
            cache = feature_root / name / relative.with_suffix('.npz')
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(cache, features=details['features'], static_mfcc=details['static_mfcc'],
                                delta=details['delta'], times=details['times'],
                                start_sample=details['start_sample'], end_sample=details['end_sample'],
                                config_json=json.dumps(config, ensure_ascii=False),
                                source_audio_hash=item['audio_hash'],
                                source_wav_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
            feature_rows.append({'variant': name, 'file': item['file'], 'label': item['label'],
                                 'split': item['split'], 'trim': variant['trim'],
                                 'n_frames': len(details['features']), 'dimensions': details['features'].shape[1],
                                 'input_duration_s': len(y)/sr, 'feature_audio_duration_s': len(details['prepared'])/sr,
                                 'start_sample': details['start_sample'], 'end_sample': details['end_sample'],
                                 'endpoint_warnings': '; '.join(details['endpoint']['warnings']) if details['endpoint'] else ''})
        templates = [{**r, 'features': features[r['file']]['features']} for r in split if r['split'] == 'train']
        test = [r for r in split if r['split'] == 'test']
        rows, template_rows, label_rows = [], [], []
        grid_cells = 0
        for index, item in enumerate(test, 1):
            query = features[item['file']]['features']
            ranking, scores = rank_templates(query, templates)
            assert len(scores) == 15 and len(ranking) == 5
            true_rank, true_candidate = next((i, r) for i, r in enumerate(ranking, 1) if r['label'] == item['label'])
            result = {'variant': name, 'file': item['file'], 'true_label': item['label'],
                      'predicted_label': ranking[0]['label'], 'correct': ranking[0]['label'] == item['label'],
                      'winning_template': ranking[0]['template_file'],
                      'score_gap': ranking[1]['score'] - ranking[0]['score'],
                      'true_label_rank': true_rank, 'true_label_score': true_candidate['score'],
                      'true_label_template': true_candidate['template_file'],
                      'n_frames': len(query), 'dimensions': query.shape[1]}
            for i, candidate in enumerate(ranking[:3], 1):
                result.update({f'top{i}_label': candidate['label'], f'top{i}_score': candidate['score'],
                               f'top{i}_template': candidate['template_file']})
            rows.append(result)
            template_rows.extend({'query_file': item['file'], **r} for r in scores)
            label_rows.extend({'query_file': item['file'], **r} for r in ranking)
            grid_cells += sum(len(query) * len(t['features']) for t in templates)
            if progress: progress(f"{name}: {index}/10 {item['file']} -> {result['predicted_label']}")
        metrics = summarize_results(rows)
        metrics.update(variant=name, dimensions=variant['dimensions'], endpoint_applied=variant['trim'],
                       delta=DELTA_CONFIG if variant['include_delta'] else None,
                       split_sha256=split_hash, n_templates=len(templates), dtw_grid_cells=grid_cells)
        write_csv(directory / 'results.csv', rows, list(rows[0]))
        write_csv(directory / 'template_scores.csv', template_rows, list(template_rows[0]))
        write_csv(directory / 'label_scores.csv', label_rows, list(label_rows[0]))
        write_csv(directory / 'feature_summary.csv', feature_rows, list(feature_rows[0]))
        write_csv(directory / 'per_label_metrics.csv', metrics['per_label'], list(metrics['per_label'][0]))
        for filename, key in [('confusion_matrix.csv', 'confusion_matrix'),
                              ('confusion_matrix_normalized.csv', 'confusion_matrix_row_normalized')]:
            cm_rows = [{'true_label': label, **dict(zip(LABELS, values))}
                       for label, values in zip(LABELS, metrics[key])]
            write_csv(directory / filename, cm_rows, ['true_label', *LABELS])
        _json_write(directory / 'metrics.json', metrics)
        summary.append({'variant': name, 'trim': variant['trim'], 'dimensions': variant['dimensions'],
                        'n_templates': 15, 'n_test': 10, 'n_correct': metrics['n_correct'],
                        'accuracy': metrics['accuracy'], 'top2_accuracy': metrics['top_k_accuracy']['2'],
                        'top3_accuracy': metrics['top_k_accuracy']['3'], 'macro_f1': metrics['macro_f1'],
                        'total_feature_frames': sum(r['n_frames'] for r in feature_rows),
                        'dtw_grid_cells': grid_cells})
        all_predictions.extend(rows)
        all_feature_rows.extend(feature_rows)
        runs[name] = {'config': config, 'rows': rows, 'metrics': metrics,
                      'features': features, 'feature_rows': feature_rows}
        if progress: progress(f"{name}: accuracy={metrics['accuracy']:.1%}")
    # Fresh control must reproduce Phase 8; do not silently replace the baseline.
    baseline = json.loads((root / 'outputs/phase8_metrics.json').read_text(encoding='utf-8'))
    control = runs['trim_mfcc13']
    if control['metrics']['confusion_matrix'] != baseline['confusion_matrix']:
        raise ValueError('Fresh control does not reproduce Phase 8 confusion matrix')
    with (root / 'results.csv').open(encoding='utf-8-sig', newline='') as handle:
        old = {r['file']: r for r in csv.DictReader(handle)}
    for row in control['rows']:
        previous = old[row['file']]
        for i in (1, 2, 3):
            assert row[f'top{i}_label'] == previous[f'top{i}_label']
            assert np.isclose(row[f'top{i}_score'], float(previous[f'top{i}_score']), rtol=1e-12, atol=1e-12)
    write_csv(root / 'outputs/phase9_experiment_summary.csv', summary, list(summary[0]))
    write_csv(root / 'outputs/phase9_all_predictions.csv', all_predictions, list(all_predictions[0]))
    write_csv(root / 'outputs/phase9_feature_summary.csv', all_feature_rows, list(all_feature_rows[0]))
    _json_write(root / 'outputs/phase9_experiment_config.json', {'variants': VARIANTS, 'delta': DELTA_CONFIG,
                'mfcc': metadata, 'dtw': dtw_config, 'split_sha256': split_hash,
                'source_hashes': {r['file']: r['audio_hash'] for r in split},
                'policy': 'one changed factor per E1/E2; fresh features on train and test; no test tuning',
                'code_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                for name in ['lab2_experiments.py', 'lab2_dtw.py', 'lab2_mfcc.py',
                                             'lab2_endpoint.py', 'lab2_evaluation.py']}})
    assert before == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    return runs, summary


def comparison_changes(runs):
    rows = []
    baseline = {r['file']: r for r in runs['trim_mfcc13']['rows']}
    for name in ['no_trim_mfcc13', 'trim_mfcc_delta26']:
        for row in runs[name]['rows']:
            original = baseline[row['file']]
            status = ('fixed' if row['correct'] and not original['correct'] else
                      'new_error' if original['correct'] and not row['correct'] else
                      'still_correct' if row['correct'] else 'still_wrong')
            rows.append({'variant': name, 'file': row['file'], 'true_label': row['true_label'],
                         'baseline_prediction': original['predicted_label'],
                         'variant_prediction': row['predicted_label'], 'status': status,
                         'baseline_true_rank': original['true_label_rank'],
                         'variant_true_rank': row['true_label_rank']})
    return rows


def path_case(runs, variant_name, query_file, template_file):
    """Same recordings under each pipeline; endpoint bounds only annotate full paths."""
    run = runs[variant_name]
    query = run['features'][query_file]
    template = run['features'][template_file]
    details = dtw_details(query['features'], template['features'])
    indices = np.array(details['path'])
    # Express frame centers in original-WAV seconds for comparable retained-region masks.
    qt = query['times'] + query['start_sample']/16000
    tt = template['times'] + template['start_sample']/16000
    qb = runs['trim_mfcc13']['features'][query_file]
    tb = runs['trim_mfcc13']['features'][template_file]
    outside_q = (qt < qb['start_sample']/16000) | (qt >= qb['end_sample']/16000)
    outside_t = (tt < tb['start_sample']/16000) | (tt >= tb['end_sample']/16000)
    q_mask, t_mask = outside_q[indices[:,0]], outside_t[indices[:,1]]
    row = {'variant': variant_name, 'query_file': query_file, 'template_file': template_file,
           'query_frames': len(query['features']), 'template_frames': len(template['features']),
           'dimensions': query['features'].shape[1], 'dtw_norm': details['normalized_cost'],
           'total_cost': details['total_cost'], 'path_length': details['path_length'],
           **path_statistics(details['path'], len(query['features']), len(template['features'])),
           'path_fraction_either_outside_endpoint': float(np.mean(q_mask | t_mask)),
           'path_fraction_both_outside_endpoint': float(np.mean(q_mask & t_mask))}
    return details, row


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lab 2 Phase 9: controlled endpoint and delta experiments')
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    runs, summary = run_experiments(args.project_root, progress=lambda value: print(value, flush=True))
    for row in summary:
        print(f"{row['variant']}: {row['n_correct']}/{row['n_test']} = {row['accuracy']:.1%}")
