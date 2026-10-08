# Phase 7 — Nearest-template recognizer

Đã tạo 15 template training (3/nhãn), chạy 10 query test từ WAV gốc và xuất top-3 nhãn khác nhau.

## Phương pháp và tính nhất quán

- WAV PCM_16 mono 16 kHz → endpoint margin 80 ms → MFCC 13 + CMN → Euclidean DTW_norm.
- Điểm một nhãn là min điểm của 3 template training; top-1 là nhãn có min thấp nhất.
- Tie: score, thứ tự chữ cái nhãn, tên template. Có đủ ranking 15 template và 5 nhãn.
- Không đưa test vào template; kiểm tra hash nguồn, split, cấu hình, trim và cache feature.
- Feature của cả 10 query tính từ WAV gốc đã đối chiếu cache Phase 5 thành công.
- WAV training/bản sao cùng âm thanh bị từ chối trong API WAV demo.

## Top-3 query test

| File | Nhãn thật | Top 1 (score) | Top 2 (score) | Top 3 (score) | Template thắng |
|---|---|---|---|---|---|
| khong/khong_04.wav | không | hai (6.343) | bốn (7.098) | không (7.105) | hai/hai_02.wav |
| khong/khong_05.wav | không | hai (6.734) | không (6.820) | bốn (7.777) | hai/hai_02.wav |
| mot/mot_04.wav | một | một (4.742) | bốn (6.488) | ba (7.944) | mot/mot_01.wav |
| mot/mot_05.wav | một | một (4.973) | bốn (6.326) | ba (6.927) | mot/mot_03.wav |
| hai/hai_04.wav | hai | hai (5.884) | ba (8.567) | không (8.657) | hai/hai_01.wav |
| hai/hai_05.wav | hai | hai (6.146) | ba (8.224) | không (8.379) | hai/hai_03.wav |
| ba/ba_04.wav | ba | ba (5.651) | không (6.791) | hai (7.393) | ba/ba_01.wav |
| ba/ba_05.wav | ba | ba (6.895) | một (6.990) | không (7.816) | ba/ba_02.wav |
| bon/bon_04.wav | bốn | bốn (4.154) | một (7.050) | không (9.083) | bon/bon_01.wav |
| bon/bon_05.wav | bốn | bốn (8.818) | không (10.632) | một (11.102) | bon/bon_02.wav |

## Demo và nhận xét

- Demo `khong/khong_04.wav` là WAV test, không nằm trong template và không phải bản ghi mới. Dự đoán hai với score 6.342908.
- Các file có top-1 khác nhãn thật: khong/khong_04.wav, khong/khong_05.wav.
- Query có cảnh báo endpoint: hai/hai_04.wav, hai/hai_05.wav, bon/bon_04.wav, bon/bon_05.wav.
- Giữ nguyên kết quả nhận nhầm và baseline; chưa thay cấu hình theo dự đoán test.
- Score/gap không phải xác suất hoặc confidence; phân bố cùng/khác từ có chồng lấn ở Phase 6.
- Chưa reject unknown: âm ngoài 5 từ vẫn có thể bị gán một nhãn nếu endpoint chấp nhận.
- Có 7 WAV cần kiểm tra nghe từ Phase 4 (gồm cả training/test). Player không thay thế xác nhận bằng nghe.
- Phase 8 sẽ tính accuracy/confusion matrix và xuất results.csv; Phase 9 thực hiện E1/E2.

## Kiểm tra và sản phẩm

6 unittest đạt: min theo nhãn/top-3 riêng biệt, tie/input lỗi, train-only, query/cache nhất quán, từ chối training và bản sao, WAV sai định dạng/silence/cấu hình cũ.

- lab2_recognizer.py; tests/test_lab2_recognizer.py; phần F notebook.
- recognizer_config.json; outputs/phase7_template_index.csv.
- outputs/phase7_predictions.csv; outputs/phase7_template_scores.csv (150 dòng); outputs/phase7_label_scores.csv (50 dòng).
- outputs/phase7_recognition_details.json; figures/phase7_label_scores.png.
