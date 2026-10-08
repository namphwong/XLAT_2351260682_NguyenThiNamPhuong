"""Check the saved submission after a clean notebook Run All."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
import sys
import nbformat
from lab2_report import build_report, rows
from lab2_recognizer import read_wav, decoded_audio_hash, NearestTemplateRecognizer
from lab2_evaluation import summarize_results


def check_submission(root):
    root = Path(root).resolve()
    checks = []

    def require(condition, description):
        if not condition:
            raise ValueError(description)
        checks.append(description)

    nb = nbformat.read(root / 'Lab2_2351260682.ipynb', as_version=4)
    nbformat.validate(nb)
    codes = [c for c in nb.cells if c.cell_type == 'code']
    require(all(c.execution_count is not None for c in codes), 'Mọi code cell đã được thực thi.')
    require(not any(o.output_type == 'error' for c in codes for o in c.outputs), 'Notebook không có output lỗi.')
    report = build_report(root)
    require(re.findall(r'^### Câu (\d+)\.', report, flags=re.MULTILINE)
            == [str(i) for i in range(1, 10)], 'Có đủ câu trả lời 1–9 theo đề Lab 2.')
    require(nb.cells[-1].cell_type == 'markdown' and nb.cells[-1].source == report,
            'Markdown cuối notebook khớp báo cáo sinh từ kết quả hiện tại.')
    require((root / 'Lab2_Report.md').read_text(encoding='utf-8') == report,
            'Bản báo cáo riêng khớp notebook và có đủ 9 câu trả lời.')
    for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', report):
        require((root / target).is_file(), f'Hình báo cáo tồn tại: {target}.')
    split = rows(root / 'data_split.csv')
    require(len(split) == 25 and len({r['audio_hash'] for r in split}) == 25,
            'Có 25 bản ghi khác nhau theo hash âm thanh.')
    for label in ['khong', 'mot', 'hai', 'ba', 'bon']:
        require(sum(r['label'] == label and r['split'] == 'train' for r in split) == 3
                and sum(r['label'] == label and r['split'] == 'test' for r in split) == 2,
                f'{label}: 3 train và 2 test, không dùng lại utterance.')
    for row in split:
        y, sr = read_wav(root / 'dataset' / row['file'])
        require(decoded_audio_hash(y, sr) == row['audio_hash'],
                f'WAV đúng PCM16/mono/16k và hash giữ nguyên: {row["file"]}.')
    recognizer = NearestTemplateRecognizer.from_project(root)
    require(len(recognizer.templates) == 15, '15 template và cấu hình/cache train đúng provenance.')
    results = rows(root / 'results.csv')
    expected = {r['file'] for r in split if r['split'] == 'test'}
    require(len(results) == 10 and {r['file'] for r in results} == expected,
            'results.csv chứa đúng đủ 10 test đã giữ lại.')
    calculated = summarize_results(results)
    saved = json.loads((root / 'outputs/phase8_metrics.json').read_text(encoding='utf-8'))
    require(calculated['confusion_matrix'] == saved['confusion_matrix']
            and calculated['accuracy'] == saved['accuracy'],
            'Accuracy và confusion matrix tái tính khớp bảng kết quả.')
    require(len(rows(root / 'outputs/phase9_all_predictions.csv')) == 30
            and len(list((root / 'features/experiments').rglob('*.npz'))) == 75,
            'E1–E2 có đủ 3 cấu hình × 10 test và 75 feature cache.')
    tests = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover',
                            '-s', 'tests', '-p', 'test_lab2_*.py', '-v'],
                           cwd=root, capture_output=True, text=True, encoding='utf-8')
    (root / 'outputs/phase10_test_results.txt').write_text(tests.stdout + tests.stderr, encoding='utf-8')
    require(tests.returncode == 0, 'Toàn bộ kiểm thử unittest đạt; log ở outputs/phase10_test_results.txt.')
    paths = set()
    for pattern in ['Lab2_*.ipynb', 'Lab 2.pdf', 'Lab2_Report.md', 'README.md', 'requirements.txt',
                    'lab2_*.py', '*config.json', 'data_split.csv', 'results.csv', 'outputs/**/*',
                    'reports/**/*', 'dataset/**/*', 'trimmed/**/*.wav', 'tools/*',
                    'figures/*.png', 'features/**/*.npz', 'experiments/**/*', 'tests/test_lab2_*.py']:
        paths.update(p for p in root.glob(pattern) if p.is_file())
    paths.difference_update({root / 'outputs/phase10_submission_manifest.csv',
                             root / 'outputs/phase10_submission_check.json',
                             root / 'reports/Phase10_Submission_Check.md'})
    manifest = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size,
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
    with (root / 'outputs/phase10_submission_manifest.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['path', 'bytes', 'sha256'])
        writer.writeheader()
        writer.writerows(manifest)
    outcome = {'automatic_checks': 'PASS', 'notebook_cells': len(nb.cells),
               'code_cells': len(codes), 'checks': checks, 'manifest_files': len(manifest),
               'manual_listening': 'PENDING: endpoint boundaries and correct word content',
               'pdf_exported': False}
    (root / 'outputs/phase10_submission_check.json').write_text(
        json.dumps(outcome, ensure_ascii=False, indent=2), encoding='utf-8')
    text = '# Phase 10 — Kiểm tra sản phẩm nộp\n\n'
    text += f'Kiểm tra tự động: **PASS**. Notebook {len(nb.cells)} cell, {len(codes)} code cell đã chạy, không lỗi.\n\n'
    text += '\n'.join('- [x] ' + check for check in checks)
    text += '\n\n- [ ] Nghe WAV gốc/trim để xác nhận đúng từ và không mất phụ âm. Ưu tiên hai file lỗi và bảy cảnh báo trong báo cáo.\n'
    text += f'\nManifest: {len(manifest)} tệp với dung lượng và SHA-256 trong `outputs/phase10_submission_manifest.csv`. '
    text += 'Notebook có Markdown báo cáo cuối; bản riêng `Lab2_Report.md`. Chưa xuất PDF hoặc ZIP.\n'
    (root / 'reports/Phase10_Submission_Check.md').write_text(text, encoding='utf-8')
    return outcome


if __name__ == '__main__':
    result = check_submission(Path(__file__).resolve().parent)
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, ensure_ascii=False, indent=2))
