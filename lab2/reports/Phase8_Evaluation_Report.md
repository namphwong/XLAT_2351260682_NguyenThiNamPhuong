# Phase 8 — Đánh giá baseline

**Accuracy: 8/10 = 80.0%.** Top-2: 90.0%; top-3: 100.0%.

## Giao thức

15 template training (3/nhãn), 10 test (2/nhãn), split cố định. WAV gốc → endpoint margin 80 ms → MFCC 13 + CMN → DTW Euclidean chuẩn hóa/path length → min theo nhãn.
Không thay tham số hoặc chọn ngưỡng reject từ kết quả test. CLI tính lại từ WAV gốc và cho cùng chỉ số; Run All dùng kết quả vừa tính ở Phase 7. Hash WAV/split và provenance đã được kiểm tra.

## Confusion matrix

Hàng = nhãn thật; cột = nhãn dự đoán. Đơn vị số file.

| Thật / dự đoán | không | một | hai | ba | bốn |
|---|---|---|---|---|---|
| không | 0 | 0 | 2 | 0 | 0 |
| một | 0 | 2 | 0 | 0 | 0 |
| hai | 0 | 0 | 2 | 0 | 0 |
| ba | 0 | 0 | 0 | 2 | 0 |
| bốn | 0 | 0 | 0 | 0 | 2 |

## Theo nhãn

| Nhãn | Test | Đúng | Precision | Recall | F1 |
|---|---|---|---|---|---|
| không | 2 | 0 | 0.000 | 0.000 | 0.000 |
| một | 2 | 2 | 1.000 | 1.000 | 1.000 |
| hai | 2 | 2 | 0.500 | 1.000 | 0.667 |
| ba | 2 | 2 | 1.000 | 1.000 | 1.000 |
| bốn | 2 | 2 | 1.000 | 1.000 | 1.000 |

Macro precision=0.700; recall=0.800; F1=0.733. Precision nhãn không không có dự đoán được ghi 0 theo zero_division=0.

## Phân tích mọi lỗi top-1

- `khong/khong_04.wav`: thật **không**, dự đoán **hai**; template thắng `hai/hai_02.wav` score=6.342908; template nhãn thật tốt nhất `khong/khong_02.wav` score=7.104658; nhãn thật rank=3. True-minus-pred=0.761750; top2-minus-top1=0.755130. Query trim=0.425s/41 frame.
- `khong/khong_05.wav`: thật **không**, dự đoán **hai**; template thắng `hai/hai_02.wav` score=6.734468; template nhãn thật tốt nhất `khong/khong_02.wav` score=6.819653; nhãn thật rank=2. True-minus-pred=0.085185; top2-minus-top1=0.085185. Query trim=0.695s/68 frame.
- Đối chiếu khong/khong_04.wav / hai/hai_02.wav (predicted): 41×65 frame; template trim=0.665s; path=65; chéo/dọc/ngang=40/0/24; mean lệch chéo chuẩn hóa=0.0389.
- Đối chiếu khong/khong_04.wav / khong/khong_02.wav (true_label): 41×88 frame; template trim=0.895s; path=88; chéo/dọc/ngang=40/0/47; mean lệch chéo chuẩn hóa=0.0400.
- Đối chiếu khong/khong_05.wav / hai/hai_02.wav (predicted): 68×65 frame; template trim=0.665s; path=76; chéo/dọc/ngang=56/11/8; mean lệch chéo chuẩn hóa=0.0846.
- Đối chiếu khong/khong_05.wav / khong/khong_02.wav (true_label): 68×88 frame; template trim=0.895s; path=92; chéo/dọc/ngang=63/4/24; mean lệch chéo chuẩn hóa=0.0921.

## Nhận xét dựa trên số liệu

- Hai lỗi hiện tại đều không → hai; recall không=0/2, precision hai=2/4. Bốn nhãn còn lại có recall 2/2.
- khong_04: nhãn thật chỉ đứng thứ 3; top-2 là bốn. Vì vậy top2-minus-top1 khác chênh giữa nhãn thật và dự đoán. khong_05: nhãn thật đứng thứ 2, chênh khoảng 0.085; điểm gần nhau không đủ căn cứ để đặt ngưỡng reject.
- Waveform cho biết vùng được giữ và thời lượng; MFCC của query/template có số frame khác nhau. DTW đối chiếu xác nhận chi phí chuẩn hóa của hai thấp hơn template không tốt nhất, nhưng shape/path không chứng minh hai bản ghi cùng từ.
- Ở waveform trim, khong_04 có một cụm biên độ mạnh ngắn, còn khong_02 có hai cụm rõ hơn. Query khong_04 dài 0.425s, khong_05 dài 0.695s, so với hai_02 0.665s và khong_02 0.895s. Thời lượng và hình dạng bao biên độ khác nhau, chưa đủ gán nguyên nhân ngữ âm.
- Trên heatmap cùng thang màu, C0/C1 biến thiên nổi bật hơn nhiều hệ số cao; CMN vẫn giữ biến thiên theo thời gian. Các dải màu được DTW căn chỉnh, không chỉ so hai hình tại cùng thời điểm tuyệt đối.
- Mean độ lệch chéo của khong_04 với hai_02/khong_02 là 0.0389/0.0400; khong_05 là 0.0846/0.0921. Cả path của nhãn sai lẫn nhãn thật đều có thể gần chéo; quyết định ở đây dựa trên DTW_norm.
- Giả thuyết cần kiểm tra: biến thiên phát âm/tốc độ/nền và đoạn phụ âm yếu bị endpoint bỏ qua có thể làm feature kém phân biệt. Chưa xác nhận cắt phụ âm hoặc sai nhãn bằng nghe. CMN loại bỏ trung bình mỗi utterance; không khắc phục mọi khác biệt.
- E1 trim vs không trim và E2 MFCC vs MFCC+delta ở Phase 9 sẽ kiểm tra ảnh hưởng pipeline theo cùng split; chưa thực hiện ở Phase 8.
- Kết quả 80% chỉ của 10 test; 2 test/nhãn. Chưa có kiểm tra người nói mới, microphone khác hay unknown words. Có 7 file endpoint cần nghe từ Phase 4; không loại khỏi đánh giá.

## Sản phẩm và kiểm tra

- results.csv: 10 dòng, nhãn thật/dự đoán, đúng/sai, top-1/top-2/top-3, template, rank nhãn thật và cảnh báo.
- outputs/phase8_metrics.json; outputs/phase8_confusion_matrix.csv; outputs/phase8_confusion_matrix_normalized.csv; outputs/phase8_per_label_metrics.csv.
- outputs/phase8_evaluation_provenance.json; outputs/phase8_error_comparison.csv; 4 CSV path; features/errors/ (4 NPZ).
- figures/phase8_confusion_matrix.png; 6 hình lỗi waveform/MFCC/DTW cho 2 query.
- lab2_evaluation.py; tests/test_lab2_evaluation.py (3 kiểm thử đạt); phần G1–G4 notebook.
