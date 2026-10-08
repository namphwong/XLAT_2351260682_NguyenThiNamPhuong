# Phase 6 — DTW tự cài đặt

Euclidean local distance; dynamic programming 3 bước; backtracking 0-based; cost chuẩn hóa theo số cặp frame trên path. Không gọi thư viện DTW. Khi tổng cost hòa, chọn path ngắn hơn rồi chéo/dọc/ngang; tối ưu tổng trước, chuẩn hóa sau.

## Kiểm tra

- Đối sánh tự thân của 25 MFCC đều có DTW_norm=0 và path chéo.
- Minh họa feature lặp frame 2 lần: 80 → 160 frame; DTW_norm=0.000000. Đây là feature mô phỏng, không phải bản ghi tốc độ khác.
- Kiểm tra path: hai đầu, bước đơn điệu hợp lệ, path length và tổng local cost bằng accumulated cost.
- Bộ unittest độc lập đối chiếu với mọi path trên các ma trận nhỏ; kiểm tra Euclidean ví dụ, chuỗi lặp và input lỗi.

## Hai cặp minh họa thật

- same_word: khong/khong_01.wav / khong/khong_02.wav; shape (80,13) / (88,13); total=914.053879; |P|=94; DTW_norm=9.723977; chéo/dọc/ngang=73/6/14; mean lệch chéo chuẩn hóa=0.0250.
- different_word: khong/khong_01.wav / mot/mot_01.wav; shape (80,13) / (61,13); total=981.791985; |P|=80; DTW_norm=12.272400; chéo/dọc/ngang=60/19/0; mean lệch chéo chuẩn hóa=0.0656.
- Cặp khác từ có DTW_norm chênh 2.548422 (26.21%) so với cặp cùng từ đã chọn.
- Cặp cùng từ có đường đi gần chéo tham chiếu hơn theo mean độ lệch; các bước ngang/dọc thể hiện kéo giãn thời gian. Đường đi khác từ vẫn tồn tại và không chứng minh hai từ giống nhau.

## 105 cặp training

- Cùng từ: 15 cặp; min=5.086, median=6.052, mean=6.765, max=12.191.
- Khác từ: 90 cặp; min=4.900, median=9.201, mean=9.156, max=13.361.
- Khoảng min–max của hai nhóm có chồng lấn. Không chọn ngưỡng reject từ hai ví dụ; phần này chưa phải accuracy/confusion matrix.

## Giới hạn và bước tiếp theo

DTW tối ưu tổng cost rồi chia path length, không tối ưu trực tiếp trung bình cost. Không band hoặc ràng buộc độ dốc; các cost phụ thuộc pipeline MFCC và endpoint. Có 7 file endpoint cần nghe lại. Phase 7 sẽ xây nearest-template với train/test đã chốt; Phase 8 mới đánh giá accuracy.

## Sản phẩm

- lab2_dtw.py; tests/test_lab2_dtw.py.
- dtw_config.json; outputs/phase6_identity_checks.csv; outputs/phase6_dtw_comparison.csv; outputs/phase6_training_pairs.csv.
- outputs/phase6_path_same_word.csv / outputs/phase6_path_different_word.csv.
- features/dtw/same_word.npz và different_word.npz chứa C, D, path và cấu hình.
- figures/phase6_dtw_same_word.png, phase6_dtw_different_word.png, phase6_training_distance_distribution.png.
