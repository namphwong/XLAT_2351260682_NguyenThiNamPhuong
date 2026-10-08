# Lab 2 — Đặc trưng tiếng nói và nhận dạng bằng DTW

Nguyễn Thị Nam Phương · MSSV 2351260682 · Lớp 65TTNT.

Đã hoàn thành Phase 1–10: 25 bản ghi cho 5 từ, framing/energy/ZCR, endpoint, MFCC tự triển khai từng bước, DTW tự cài DP/backtracking, nearest-template, đánh giá và E1–E2. Báo cáo đầy đủ nằm trong [Lab2_Report.md](Lab2_Report.md) và Markdown cuối [notebook](Lab2_2351260682.ipynb).

| Cấu hình | Top-1 | Top-2 | Top-3 |
|---|---|---|---|
| Trim + MFCC13/CMN | 80% | 90% | 100% |
| Không trim + MFCC13/CMN | 70% | 70% | 70% |
| Trim + MFCC + Δ26 | 80% | 100% | 100% |

Split cố định trong `data_split.csv`: 3 template/từ (`_01`–`_03`) và 2 test/từ (`_04`–`_05`). `results.csv` là kết quả baseline của toàn bộ 10 test. Không dùng test làm template hoặc chỉnh tham số theo lỗi test.

## Môi trường và chạy lại

Các lệnh sau chạy trong thư mục `lab2/`, với Python 3.11:

```powershell
cd lab2
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --user --name lab2-2351260682 --display-name "Lab 2 (Python 3.11)"
```

Mở notebook, chọn kernel **Lab 2 (Python 3.11)**, Restart Kernel → Run All. Notebook tạo lại các bảng, hình, feature và báo cáo từ dữ liệu đã chốt. Các module `lab2_*.py` cần nằm cùng thư mục với notebook.

Sau Run All, kiểm tra sản phẩm nộp:

```powershell
.\.venv\Scripts\python.exe -X utf8 lab2_submission_check.py
```

Chạy riêng kiểm thử:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p 'test_lab2_*.py' -v
```

Máy hiện tại đã có môi trường ở `../.venv-lab2/`; có thể dùng `..\.venv-lab2\Scripts\python.exe` thay cho `.\.venv\Scripts\python.exe`. Môi trường này không được commit; máy khác cần cài từ `requirements.txt`. scikit-learn được cố định 1.7.2 theo phiên bản đã chạy thành công.

## Thư mục

| Đường dẫn | Nội dung |
|---|---|
| `dataset/` | 25 WAV PCM16 mono 16 kHz; giữ MP3 gốc |
| `trimmed/` | 25 WAV sau endpoint, margin 80 ms |
| `figures/` | Waveform, energy/ZCR, MFCC, DTW, confusion matrix và E1–E2 |
| `outputs/` | CSV/JSON từng phase, metrics, provenance và manifest |
| `reports/` | Báo cáo từng phase và [ghi chú quá trình](reports/README_Phases.md) |
| `features/` | MFCC và ma trận/path DTW, cache đối chứng |
| `experiments/phase9/` | Kết quả riêng của 3 cấu hình, 30 dự đoán |
| `tests/` | 18 kiểm thử của các thuật toán và pipeline |
| `tools/` | Công cụ thu âm chạy tại máy |

Cấu hình thuật toán lưu ở `endpoint_config.json`, `mfcc_config.json`, `dtw_config.json`, `recognizer_config.json`; giữ tại gốc Lab 2 để dễ kiểm tra cùng notebook. Baseline giữ ở `results.csv`, các bảng trung gian nằm trong `outputs/`.

## Công cụ ghi âm

Trong thư mục `lab2/`:

```powershell
powershell -ExecutionPolicy Bypass -File tools/start_recording_lab2.ps1
```

Mở `http://localhost:8765/tools/record_lab2.html`, chọn thư mục `lab2/dataset` và cấp quyền micro. Script chọn môi trường `.venv/`, môi trường cũ `../.venv-lab2/`, hoặc Python trên PATH. Ctrl+C để dừng server. Không ghi đè tập test đã chốt để cải thiện kết quả báo cáo.

## Kiểm tra trước nộp

[reports/Phase10_Submission_Check.md](reports/Phase10_Submission_Check.md) lưu kết quả kiểm tra tự động; `outputs/phase10_submission_manifest.csv` lưu đường dẫn, dung lượng và SHA-256. Manifest không liệt kê chính nó hoặc các bản tóm tắt thay đổi sau khi lập manifest.

Vẫn cần **nghe đối chiếu gốc/trim** để xác nhận đúng từ và không mất phụ âm. Ưu tiên hai file lỗi `khong_04.wav`, `khong_05.wav` và bảy cảnh báo endpoint nêu trong báo cáo. Chưa xác nhận khả năng nhận dạng người nói mới; không có metadata phân nhóm người nói. Chưa xuất PDF/ZIP; phần Markdown cuối notebook đáp ứng lựa chọn báo cáo của đề.
