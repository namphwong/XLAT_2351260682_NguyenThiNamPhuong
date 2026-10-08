# Lab 2 — MFCC và DTW

Nguyễn Thị Nam Phương — MSSV 2351260682 — Lớp 65TTNT.

## Trạng thái

Đã hoàn thành Phase 1–10: chuẩn bị 25 bản ghi (5 từ × 5 lần), phân tích miền thời gian, endpoint, MFCC, DTW tự cài, nhận dạng, đánh giá và đối chứng E1–E2. Split cố định 15 train + 10 test. Baseline có trim đạt 80%; không trim 70%; MFCC + Δ 80%. Phase 10 bổ sung bảng tham số, kết quả E1–E2, 9 câu trả lời và kết luận trong Markdown cuối notebook và Lab2_Report.md. Kiểm tra tự động lưu trong reports/Phase10_Submission_Check.md; bước nghe xác nhận biên còn cần thực hiện.

Bản gốc là MP3 mono 48 kHz; đã giữ nguyên và chuyển thành WAV PCM 16-bit mono 16 kHz. Cần nghe lại các file cảnh báo để xác nhận đúng một từ và biên đầu/cuối.

## Cách chạy Phase 1

1. Mở `Lab2_2351260682.ipynb` bằng VS Code hoặc Jupyter.
2. Chọn kernel **Lab 2 (Python 3.11)** đã đăng ký. Nếu VS Code chưa hiện kernel, chọn interpreter `.venv-lab2/Scripts/python.exe`. Đường dẫn Python đang chạy sẽ hiện trong ô import.
3. Môi trường `.venv-lab2` hiện kế thừa các thư viện Python 3.11 có sẵn và dùng scikit-learn 1.7.2 riêng. Phiên bản scikit-learn 1.9.1 trên máy gặp lỗi DLL bị Windows Application Control chặn khi import metrics; phiên bản 1.7.2 đã import thành công. Khi thiết lập trên máy khác, tạo môi trường và cài đầy đủ requirements:

   ```powershell
   python -m venv .venv-lab2
   .\.venv-lab2\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv-lab2\Scripts\python.exe -m ipykernel install --user --name lab2-2351260682 --display-name "Lab 2 (Python 3.11)"
   ```

4. Chọn Restart Kernel → Run All. Ô cuối Phase 1 phải báo kiểm tra thành công.

## Cấu trúc

```text
Lab2_2351260682.ipynb    Notebook thiết lập và khung A–G/báo cáo
requirements.txt   Phiên bản thư viện đã kiểm tra
dataset/                WAV gốc, mỗi nhãn một thư mục
  khong/  mot/  hai/  ba/  bon/
trimmed/                WAV cắt silence, mỗi nhãn một thư mục
figures/           Hình của Lab 2
results.csv             Kết quả baseline của 10 file test (Phase 8)
```

## Cấu hình baseline

16 kHz; frame 25 ms (400 mẫu); hop 10 ms (160 mẫu); Hamming; tiền nhấn 0,97; NFFT 512; 24 Mel filters; 13 MFCC; center=False; CMN bật; Euclidean distance; DTW chuẩn hóa theo path length.

Ngưỡng top_db=35, margin=50 ms là tham khảo của baseline thư viện trong đề. Endpoint tự cài ở Phase 4 dùng hai mức tương đối 18/30 dB, ngưỡng nền và margin=80 ms. Pipeline train và test phải nhất quán.

## Phase 3 — Đặc trưng miền thời gian

Phần B của notebook tự tính energy, RMS, magnitude và ZCR bằng NumPy trên 25 WAV (6.324 frame). Frame 400 mẫu, hop 160 mẫu; energy/RMS/magnitude dùng Hamming, ZCR dùng frame gốc với mẫu bằng 0 được xem là không âm. Chỉ lấy frame đầy đủ và ghi số mẫu đuôi bỏ qua. Log-energy dùng epsilon=1e-9; không phải SPL/dBFS.

Sản phẩm:

- `outputs/phase3_frame_features.csv`: giá trị từng frame.
- `outputs/phase3_summary.csv`: thống kê 25 file.
- `outputs/phase3_frame_examples.csv`: frame minh họa nền, hữu thanh, ZCR cao và vô thanh/nhiễu ứng viên.
- `figures/phase3_time_features_<label>.png`: 5 đồ thị đồng bộ waveform/log-energy/RMS/magnitude/ZCR.
- `figures/phase3_autocorrelation.png`: minh họa tuần hoàn và pitch ứng viên.
- `reports/Phase3_Time_Features_Report.md`: số liệu và nhận xét thực tế.

Hàm phân tích nằm trong `lab2_time_features.py`. Pitch 70–400 Hz và các frame hữu thanh/vô thanh chỉ là minh họa, chưa phải nhãn đã xác nhận bằng nghe. ZCR cao vẫn có thể xuất hiện ở frame tuần hoàn; không dùng riêng ZCR để gán unvoiced. Phase 4 sẽ triển khai endpoint có margin, chú ý các xung rời cuối bản ghi.

## Phase 4 — Endpoint detection

Phần C tự phát hiện biên bằng log-energy Hamming, lọc median 5 frame, ngưỡng cao/thấp theo peak và nền; ZCR hỗ trợ mở rộng phụ âm yếu khi vẫn đủ năng lượng. Chọn vùng liên tục chính cho một từ, nối gap 40 ms, vùng tối thiểu 120 ms, mở rộng tối đa 150 ms/phía và margin 80 ms. Cấu hình giống nhau cho train/test, chưa dùng test accuracy để chọn tham số.

Đã xuất 25 WAV PCM_16 mono 16 kHz trong `trimmed/`; kiểm tra từng sample khớp lát cắt nguồn. Tổng thời lượng 63,720 → 18,525 s, trung bình 2,549 → 0,741 s/file. WAV gốc và split giữ nguyên.

Sản phẩm: `endpoint_config.json`, `outputs/phase4_trim_results.csv`, `outputs/phase4_margin_comparison.csv`, `reports/Phase4_Endpoint_Report.md` và 7 hình `figures/phase4_*.png`. Hàm nằm trong `lab2_endpoint.py`.

Có 7 file cảnh báo cần nghe, được liệt kê trong báo cáo. Phần C5 có player gốc/trim cho khong_01, hai_01, bon_01 và hàm `listen_endpoint_comparison` để nghe file khác. Frame onset ứng viên của khong_01 được giữ ở cả margin 0/50/80/120 ms; chọn 80 ms là vùng đệm thận trọng, chưa chứng minh tối ưu bằng nhãn biên hoặc accuracy. Chưa xác nhận bằng nghe rằng mọi phụ âm được giữ nguyên.

## Phase 5 — MFCC

Phần D trích MFCC của 25 WAV trim, tổng 1.815 frame. Tất cả feature có shape `(T, 13)`, T từ 41 đến 176. Tiền nhấn alpha=0,97; frame400/hop160, Hamming đối xứng; FFT zero-pad512; power/NFFT; 24 Mel filters theo công thức 1125ln(1+f/700); log tự nhiên; DCT-II orthonormal giữ C0–C12; CMN theo từng utterance. Cùng cấu hình cho train/test.

Triển khai theo công thức phần lý thuyết của đề, không dùng các mặc định Slaney/log-dB/framing512 của baseline Librosa. Tham số được lưu tường minh để giữ nhất quán ở các phase tiếp theo. Số frame tính từ frame400, không phải n_fft512; không center hoặc pad đầu/cuối tín hiệu.

Sản phẩm:

- `features/mfcc/<label>/*.npz`: 25 ma trận MFCC, raw MFCC, log-Mel, thời gian, cấu hình và hash WAV trim.
- `mfcc_config.json` và `outputs/phase5_mfcc_summary.csv`.
- `figures/phase5_mfcc_<label>.png`: 5 heatmap cùng thang màu.
- `phase5_mel_filterbank.png` và `phase5_cmn_comparison.png` trong thư mục hình.
- `reports/Phase5_MFCC_Report.md`: công thức, cấu hình, số liệu và nhận xét.

Hàm `mfcc_feature` trong `lab2_mfcc.py` trả về `(T,13)` cho DTW Phase 6. Kiểm tra công thức Mel ngược, DCT bằng tổng cosine độc lập, CMN, tiền nhấn, signal zero và số frame đã đạt. MFCC không tự khắc phục các biên trim cần nghe ở Phase 4.

## Phase 6 — DTW tự cài đặt

Phần E dùng `lab2_dtw.py` để tính khoảng cách Euclidean, quy hoạch động với bước chéo/dọc/ngang và truy vết đường đi. DTW tối ưu tổng cost rồi chia cho số cặp frame trên path. Khi tổng cost bằng nhau, ưu tiên path ngắn hơn rồi bước chéo/dọc/ngang. Không dùng thư viện DTW hoặc giới hạn warping band.

Đã kiểm tra 25 MFCC đối sánh với chính nó đều cho DTW=0. Hai cặp minh họa training: không/không có score 9,724; không/một có score 12,272. Thống kê 105 cặp training có median cùng từ 6,052 và khác từ 9,201; phân bố vẫn chồng lấn, chưa phải kết quả accuracy.

Sản phẩm:

- `dtw_config.json`, `outputs/phase6_identity_checks.csv`, `outputs/phase6_dtw_comparison.csv`, `outputs/phase6_training_pairs.csv`.
- `outputs/phase6_path_same_word.csv`, `outputs/phase6_path_different_word.csv`: từng cặp frame trên đường đi.
- `features/dtw/*.npz`: local distance C, accumulated cost D, path và cấu hình cho hai cặp minh họa.
- `figures/phase6_*.png`: 2 hình ma trận/đường đi và 1 hình phân bố khoảng cách.
- `reports/Phase6_DTW_Report.md`: kết quả và nhận xét.

5 unittest đã đạt, gồm đối chiếu quy hoạch động với mọi path trên các ma trận nhỏ, tổng cost trên path, chuỗi giống/lặp frame và input lỗi. Chạy lại bằng:

```powershell
.\.venv-lab2\Scripts\python.exe -m unittest discover -s tests -p 'test_lab2_dtw.py' -v
```

Notebook đã chạy Run All thành công. Phase 7 sẽ dùng DTW này để nhận dạng nearest-template theo split đã chốt.

## Phase 7 — Nhận dạng nearest-template

Phần F dùng `lab2_recognizer.py` tạo 15 template từ train split (3/nhãn). Nhận WAV gốc → endpoint → MFCC 13 + CMN → DTW với đủ 15 template → lấy min theo mỗi nhãn → xếp hạng 5 nhãn. Top-3 gồm 3 nhãn khác nhau và template tốt nhất tương ứng. Nhãn thật chỉ dùng khi trình bày kết quả.

Đã chạy 10 file test từ WAV gốc và đối chiếu feature với cache Phase 5. Demo `khong/khong_04.wav` chưa nằm trong template; chưa phải bản ghi mới. API từ chối WAV training và bản sao cùng nội dung. Hash nguồn/trim/split, cấu hình và feature training được kiểm tra khi tạo bộ nhận dạng.

Trong notebook:

```python
result = recognize_lab2("dataset/hai/hai_05.wav")
result["prediction"], result["top_k"]
```

Hoặc dùng CLI, có thể thay đối số bằng đường dẫn tuyệt đối tới WAV mới:

```powershell
.\.venv-lab2\Scripts\python.exe -X utf8 lab2_recognizer.py dataset/hai/hai_05.wav
```

Truyền WAV **gốc chưa trim**, PCM_16 mono 16 kHz, một từ/file. CLI trả JSON chứa dự đoán, score, winning template, top-3 nhãn, đủ thứ hạng template/nhãn và thông tin endpoint. Có thể chuyển định dạng trước bằng `convert_recording`; không có chuyển định dạng ngầm trong bộ nhận dạng.

Sản phẩm: `recognizer_config.json`, `outputs/phase7_template_index.csv`, `outputs/phase7_predictions.csv`, `outputs/phase7_template_scores.csv`, `outputs/phase7_label_scores.csv`, `outputs/phase7_recognition_details.json`, `figures/phase7_label_scores.png` và `reports/Phase7_Recognizer_Report.md`.

6 unittest trong `tests/test_lab2_recognizer.py` đã đạt. Chạy bằng:

```powershell
.\.venv-lab2\Scripts\python.exe -m unittest discover -s tests -p 'test_lab2_recognizer.py' -v
```

Score càng thấp càng gần; score/gap không phải xác suất hoặc confidence. Chưa reject unknown: tín hiệu qua endpoint được gán một trong 5 nhãn. Giữ nguyên kết quả nhận nhầm và cấu hình baseline; kết quả đánh giá nằm ở Phase 8 bên dưới. Các cảnh báo cần nghe lại ở Phase 4 vẫn còn.

## Phase 8 — Đánh giá baseline

Phần G1–G4 đánh giá đủ 10 file test với 15 template training, giữ nguyên split và pipeline Phase 7. **Accuracy 80% (8/10)**; top-2 90%; top-3 100%. Cả hai lỗi là `khong_04.wav` và `khong_05.wav`, nhận nhầm không → hai. Recall không=0/2; các nhãn khác=2/2. Precision hai=2/4 do nhận thêm hai file không.

Confusion matrix có hàng là nhãn thật, cột là nhãn dự đoán theo thứ tự không/một/hai/ba/bốn. Lưu cả số file và phiên bản chuẩn hóa theo hàng. Precision của nhãn không khi không có dự đoán được ghi 0 theo `zero_division=0`.

Sản phẩm:

- `results.csv`: 10 dòng, nhãn thật/dự đoán, đúng/sai, top-1/top-2/top-3 và điểm, template, rank nhãn thật, cảnh báo endpoint.
- `outputs/phase8_metrics.json`, `outputs/phase8_confusion_matrix.csv`, `outputs/phase8_confusion_matrix_normalized.csv`, `outputs/phase8_per_label_metrics.csv`.
- `outputs/phase8_evaluation_provenance.json`: hash dữ liệu, cấu hình và mã dùng để đánh giá.
- `outputs/phase8_error_comparison.csv`, 4 CSV đường đi và 4 NPZ trong `features/errors/`.
- `figures/phase8_confusion_matrix.png`, 6 hình waveform/MFCC/DTW cho cả hai file nhận nhầm.
- `reports/Phase8_Evaluation_Report.md`: kết quả, phân tích lỗi và giới hạn.

Chạy đánh giá độc lập từ WAV gốc:

```powershell
.\.venv-lab2\Scripts\python.exe -X utf8 lab2_evaluation.py
```

CLI xuất bảng/chỉ số; Run All notebook tạo thêm hình và báo cáo. Ba kiểm thử trong `tests/test_lab2_evaluation.py` đã đạt, kiểm tra confusion matrix/top-k bằng số đếm biết trước, input lỗi, đầy đủ test và provenance. Notebook đối chiếu matrix thêm bằng vòng lặp đếm độc lập.

Kết quả chỉ mô tả 10 test của split hiện tại, chưa kiểm tra người nói/micro mới. Không loại file có cảnh báo hoặc sửa tham số theo test. Giả thuyết về mất phụ âm cần nghe kiểm tra và thí nghiệm E1–E2 ở Phase 9; chưa kết luận nguyên nhân từ hình đơn lẻ.

## Phase 9 — Đối chứng E1–E2

Phần G5–G8 và `lab2_experiments.py` chạy ba cấu hình cố định trên cùng 15 train/10 test, ba template mỗi nhãn. Mỗi cấu hình tính mới feature cho cả 25 file, không dùng template trim cho query full WAV. Kết quả baseline `results.csv` và các cấu hình Phase 8 được giữ nguyên.

| Cấu hình | Feature | Accuracy | Top-2 | Top-3 |
|---|---|---|---|---|
| Có trim | 13 MFCC + CMN | 80% (8/10) | 90% | 100% |
| Không trim | 13 MFCC + CMN | 70% (7/10) | 70% | 70% |
| Có trim | MFCC + Δ, 26 chiều | 80% (8/10) | 100% | 100% |

E1 chỉ bật/tắt endpoint ở cả train/test. Trim tăng 10 điểm phần trăm và sửa lỗi của `ba_05.wav`; hai file không vẫn sai (full WAV nhận thành một, trim nhận thành hai). Full WAV có 6.324 frame, trim 1.815; số ô DP của 150 phép đối sánh full tăng khoảng 12,54 lần. Đây là số ô tính toán, không phải thời gian CPU đã đo.

E2 chỉ ghép thêm Δ: bậc 1, N=2 mỗi phía, lặp frame biên, trọng số 1. Công thức `sum[n*(c[t+n]-c[t-n])]/(2*sum[n*n])`, n=1..2. Tính trên MFCC đã CMN; không CMN block Δ thêm, không ΔΔ. Các 13 cột tĩnh và số frame của cả 25 file không đổi. Top-1 giữ nguyên; Δ đưa nhãn thật của `khong_04.wav` từ hạng 3 lên hạng 2. Score của 13/26 chiều không có ngưỡng so sánh trực tiếp.

Sản phẩm:

- `experiments/phase9/<variant>/`: cấu hình, results, metrics, confusion matrices, per-label và mọi điểm template/nhãn.
- `features/experiments/`: 75 NPZ feature; `features/experiment_paths/`: 12 NPZ C/D/path.
- `outputs/phase9_experiment_summary.csv`, `outputs/phase9_experiment_config.json`, `outputs/phase9_all_predictions.csv`, `outputs/phase9_feature_summary.csv`.
- `outputs/phase9_prediction_changes.csv`, `outputs/phase9_query_comparison.csv`, `outputs/phase9_path_comparison.csv` và 12 path CSV trong thư mục thí nghiệm.
- `figures/phase9_*.png`: 6 hình accuracy, confusion matrices, Δ và path đối chứng E1/E2.
- `reports/Phase9_Experiments_Report.md`: nhận xét và giới hạn dựa trên kết quả.

Chạy lại bảng/chỉ số và feature từ WAV gốc:

```powershell
.\.venv-lab2\Scripts\python.exe -X utf8 lab2_experiments.py
```

Run All notebook tạo thêm hình, path và báo cáo. Bốn kiểm thử trong `tests/test_lab2_experiments.py` đã đạt, kiểm tra Δ bằng ramp có đáp án biết trước, xử lý biên, bất biến khi trừ trung bình, input lỗi, cấu hình chỉ đổi một yếu tố và xếp hạng 26 chiều. Đối chứng tính mới tái lập đúng Phase 8.

Path full WAV có nhiều bước ngoài vùng giữ lại của endpoint tham chiếu; vùng này chưa được gán nhãn silence/ngữ âm. Chưa xác nhận mất phụ âm bằng nghe. Không chọn lại split, cửa sổ Δ hay trọng số theo test. E3 là tùy chọn; E4 chưa thực hiện vì chưa có metadata người nói cho hai nhóm.

## Thu dữ liệu — Phase 2

### Thu âm tại máy

Trong terminal PowerShell tại thư mục dự án:

```powershell
.\.venv-lab2\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1
```

Mở Chrome/Edge ở `http://localhost:8765/tools/record_lab2.html`, chọn đúng thư mục `dataset` của dự án và cấp quyền micro khi trình duyệt hỏi. Chờ 0,3 giây, nói từ hiển thị, giữ yên 0,3 giây rồi dừng. Nghe lại và bấm lưu; trang tự chuyển từ khi đủ 5 lần. Giữ terminal mở khi thu âm, Ctrl+C để dừng server sau khi xong.

Trang thu âm chạy tại máy, xuất WAV PCM 16-bit mono 16 kHz, không gửi âm thanh tới dịch vụ bên ngoài. File đã có được giữ nguyên. Nếu ghi âm bằng công cụ khác, đặt file vào các thư mục nhãn và dùng hàm `convert_recording` trong notebook khi cần đổi định dạng; file nguồn được giữ nguyên.

- Thu các từ “không, một, hai, ba, bốn”, mỗi từ ít nhất 5 lần riêng biệt.
- WAV PCM mono 16 kHz; giữ khoảng 0,2–0,5 giây im lặng trước/sau từ.
- Đặt tên `dataset/khong/khong_01.wav` ... `khong_05.wav`, tương tự cho nhãn khác.
- Kiểm tra chất lượng, lập bảng thông tin và vẽ waveform ít nhất 3 từ.
- Chốt 3 file/từ làm template và 2 file/từ làm test, không trùng file.

Các file `.gitkeep` chỉ giúp Git lưu thư mục rỗng; không phải dữ liệu ghi âm.

### Chạy kiểm tra sau thu âm

Mở notebook, chọn kernel **Lab 2 (Python 3.11)** và Run All. Phần A tạo:

- `outputs/dataset_audit.csv`: định dạng, thời lượng, mức biên độ, khoảng yên sơ bộ và cảnh báo chất lượng.
- `outputs/audio_conversion.csv`: ánh xạ MP3 gốc sang WAV, định dạng và hash để kiểm tra chuyển đổi khi chạy lại.
- `data_split.csv`: split cố định, 3 file đầu/từ cho train, các file còn lại cho test; chỉ tạo khi đủ dữ liệu hợp lệ, không có bản ghi trùng.
- `figures/phase2_waveforms.png`: waveform ít nhất 3 từ khi dữ liệu có sẵn.
- `reports/Phase2_Data_Report.md`: tóm tắt kết quả kiểm tra bộ dữ liệu thật và các cảnh báo cần nghe lại.

Nếu dữ liệu thay đổi sau khi chốt, notebook yêu cầu kiểm tra manifest cũ trước khi chốt lại. Hash dựa trên âm thanh giải mã để phát hiện bản ghi bị sao chép. Khoảng silence chỉ được ước lượng theo RMS để hỗ trợ kiểm tra, chưa phải endpoint detection của Phase 4. Người thu cần nghe lại để xác nhận đúng từ, chỉ một từ/file và không mất âm.

## Báo cáo và kiểm tra cuối — Phase 10

- `Lab2_Report.md`: báo cáo tổng hợp, cũng có trong phần Markdown cuối notebook.
- `lab2_report.py`: sinh báo cáo từ bảng kết quả cố định.
- `lab2_submission_check.py`: kiểm tra notebook đã chạy, format/hash/split, template, kết quả và toàn bộ unittest; chạy sau Run All.
- `reports/Phase10_Submission_Check.md`, `outputs/phase10_submission_check.json`, `outputs/phase10_submission_manifest.csv`, `outputs/phase10_test_results.txt`: bằng chứng kiểm tra và danh sách tệp có SHA-256.

Chạy kiểm tra cuối bằng `.\.venv-lab2\Scripts\python.exe -X utf8 lab2_submission_check.py`. Notebook và các module Python cần được giữ cùng thư mục khi nộp để tái lập. Không nộp môi trường ảo hoặc cache Python. Báo cáo Markdown đáp ứng lựa chọn của đề; chưa xuất PDF/ZIP. Nghe đối chiếu gốc/trim vẫn cần kiểm tra thủ công.
