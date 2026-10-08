# Phase 9 — Thí nghiệm đối chứng E1–E2

Cùng split 15 train + 10 test, 3 template/nhãn. Mỗi cấu hình tính mới feature của cả 25 file. Đối chứng trim + 13 MFCC tái lập Phase 8; không thay kết quả baseline results.csv.

## Thiết kế và Δ

- E1: no_trim_mfcc13 vs trim_mfcc13; chỉ bật/tắt endpoint cho cả train/test.
- E2: trim_mfcc13 vs trim_mfcc_delta26; giữ endpoint, chỉ ghép thêm 13 Δ.
- MFCC tĩnh: frame400/hop160, Hamming, alpha0.97, FFT512, 24 Mel, 13 hệ số C0–C12, CMN từng utterance.
- Δ bậc 1: sum[n*(c[t+n]-c[t-n])]/(2*sum[n²]), n=1..2; mẫu biên lặp; trọng số 1. Tính trên MFCC đã CMN, không CMN block Δ lần nữa, không ΔΔ; đơn vị thay đổi hệ số/frame.
- Tất cả dùng Euclidean + DTW tự cài tối ưu tổng rồi chia path length; min theo nhãn. Không thay trọng số/cửa sổ Δ, band hoặc ngưỡng theo test.

## Kết quả

| Cấu hình | Chiều | Đúng/test | Accuracy | Top-2 | Top-3 | Macro F1 | Tổng frame | Ô DP |
|---|---|---|---|---|---|---|---|---|
| trim_mfcc13 | 13 | 8/10 | 80% | 90% | 100% | 0.733 | 1815 | 777974 |
| no_trim_mfcc13 | 13 | 7/10 | 70% | 70% | 70% | 0.648 | 6324 | 9757163 |
| trim_mfcc_delta26 | 26 | 8/10 | 80% | 100% | 100% | 0.733 | 1815 | 777974 |

## E1 — Endpoint

Có trim đạt 80%, không trim 70%; chênh +10 điểm phần trăm khi bật endpoint.

- File được trim sửa lỗi so với no-trim: ba/ba_05.wav.
- Hai file không vẫn sai: không trim dự đoán một, có trim dự đoán hai. Trim cải thiện tổng thể nhưng chưa giải quyết nhãn không.
- Full WAV có 6324 frame so với 1815 sau trim. Số ô DP toàn bộ 150 phép đối sánh tăng 12.54 lần; đây là số ô lý thuyết, không phải đo thời gian CPU.
- Với cùng query/template, full path có nhiều bước ngoài vùng endpoint tham chiếu; score full có thể thấp hơn do nhiều frame nền/độ dài path và CMN toàn utterance. Score nhỏ hơn không tự bảo đảm nhận dạng tốt hơn.
- Ngoài vùng giữ lại không đồng nghĩa silence đã gán nhãn; có thể chứa nhiễu/click hoặc âm yếu. Chưa xác nhận bằng nghe rằng endpoint giữ mọi phụ âm.

## E2 — MFCC + Δ

MFCC + Δ đạt 80%, thay đổi +0 điểm phần trăm top-1 so với 13 MFCC.

- Lỗi được Δ sửa: không có; lỗi mới: không có.
- Top-2 tăng 90% → 100%; khong_04 chuyển nhãn thật từ hạng 3 lên hạng 2. Top-1 của cả 10 query không đổi; hai file không vẫn nhận thành hai.
- Block tĩnh 13 chiều và số frame giữ nguyên ở cả 25 file. Δ bổ sung biến thiên, không bảo đảm tăng accuracy; trong split này chỉ cải thiện thứ hạng bổ sung. Không so ngưỡng score 13/26 chiều trực tiếp.

## Path đối chứng

| Thí nghiệm | Cấu hình | Query / template | Shape | DTW_norm | Path | Ngoài vùng endpoint (ít nhất 1 phía) |
|---|---|---|---|---|---|---|
| E1_khong | no_trim_mfcc13 | khong_04.wav / khong_02.wav | 219×368×13 | 4.078 | 411 | 79.8% |
| E1_khong | no_trim_mfcc13 | khong_04.wav / hai_02.wav | 219×248×13 | 3.545 | 272 | 81.2% |
| E1_khong | trim_mfcc13 | khong_04.wav / khong_02.wav | 41×88×13 | 7.105 | 88 | 0.0% |
| E1_khong | trim_mfcc13 | khong_04.wav / hai_02.wav | 41×65×13 | 6.343 | 65 | 0.0% |
| E1_ba | no_trim_mfcc13 | ba_05.wav / ba_02.wav | 226×262×13 | 4.965 | 271 | 69.4% |
| E1_ba | no_trim_mfcc13 | ba_05.wav / mot_03.wav | 226×207×13 | 3.458 | 257 | 77.4% |
| E1_ba | trim_mfcc13 | ba_05.wav / ba_02.wav | 54×92×13 | 6.895 | 92 | 0.0% |
| E1_ba | trim_mfcc13 | ba_05.wav / mot_03.wav | 54×44×13 | 6.990 | 58 | 0.0% |
| E2_khong | trim_mfcc13 | khong_04.wav / khong_02.wav | 41×88×13 | 7.105 | 88 | 0.0% |
| E2_khong | trim_mfcc13 | khong_04.wav / hai_02.wav | 41×65×13 | 6.343 | 65 | 0.0% |
| E2_khong | trim_mfcc_delta26 | khong_04.wav / khong_02.wav | 41×88×26 | 7.450 | 88 | 0.0% |
| E2_khong | trim_mfcc_delta26 | khong_04.wav / hai_02.wav | 41×65×26 | 6.618 | 65 | 0.0% |

## Giới hạn và sản phẩm

10 test (2/nhãn), một lỗi tương ứng 10 điểm phần trăm accuracy; chưa đánh giá người nói/micro mới. E4 chưa thực hiện vì chưa có metadata người nói cho hai nhóm; E3 là tùy chọn. Các cảnh báo endpoint Phase 4 vẫn cần nghe. Không dùng kết quả này để chọn lại split hoặc tối ưu trên test.

- lab2_experiments.py; tests/test_lab2_experiments.py (4 kiểm thử đạt); phần G5–G8 notebook.
- experiments/phase9/<variant>/: config, results, metrics, confusion matrices, per-label, full template/label scores, feature summary.
- features/experiments/: 75 NPZ; features/experiment_paths/: 12 NPZ C/D/path; experiments/phase9/path_*.csv.
- outputs/phase9_experiment_summary.csv; outputs/phase9_experiment_config.json; outputs/phase9_all_predictions.csv; outputs/phase9_feature_summary.csv.
- outputs/phase9_prediction_changes.csv; outputs/phase9_query_comparison.csv; outputs/phase9_path_comparison.csv.
- figures/phase9_*.png: accuracy, 3 confusion matrices, Δ, E1 khong/E1 ba/E2 khong paths (6 hình).

Phase 10 sẽ tổng hợp báo cáo, trả lời 9 câu hỏi và kiểm tra sản phẩm nộp.
