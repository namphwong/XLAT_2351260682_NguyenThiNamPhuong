# Phase 3 — Phân tích đặc trưng miền thời gian

Đã phân tích 25 WAV, tổng 6324 frame đầy đủ.
Cấu hình: 16 kHz; frame 400 mẫu (25 ms); hop 160 mẫu (10 ms); Hamming cho energy/RMS/magnitude, frame gốc cho ZCR; epsilon=1e-9.

## Quan sát từ dữ liệu thật

- khong/khong_01.wav: 423 frame; vùng năng lượng liên tục chính khoảng 2.052–2.592 s (ước lượng minh họa, chưa trim). Frame hữu thanh ứng viên t=2.222 s, ZCR=0.128, F₀ ứng viên 254.0 Hz, ρ=0.787.
- mot/mot_01.wav: 219 frame; vùng năng lượng liên tục chính khoảng 0.982–1.352 s (ước lượng minh họa, chưa trim). Frame hữu thanh ứng viên t=1.052 s, ZCR=0.030, F₀ ứng viên 262.3 Hz, ρ=0.861.
- hai/hai_01.wav: 207 frame; vùng năng lượng liên tục chính khoảng 0.732–1.332 s (ước lượng minh họa, chưa trim). Frame hữu thanh ứng viên t=0.762 s, ZCR=0.037, F₀ ứng viên 246.2 Hz, ρ=0.859.
- ba/ba_01.wav: 197 frame; vùng năng lượng liên tục chính khoảng 0.722–1.252 s (ước lượng minh họa, chưa trim). Frame hữu thanh ứng viên t=0.742 s, ZCR=0.030, F₀ ứng viên 235.3 Hz, ρ=0.824.
- bon/bon_01.wav: 168 frame; vùng năng lượng liên tục chính khoảng 0.562–0.932 s (ước lượng minh họa, chưa trim). Frame hữu thanh ứng viên t=0.592 s, ZCR=0.028, F₀ ứng viên 219.2 Hz, ρ=0.824.

## Diễn giải và giới hạn

Energy/RMS/magnitude tăng ở vùng tiếng nói; nền bằng 0 đạt sàn log-energy -90 dB. Các ví dụ hữu thanh có đỉnh autocorrelation rõ, nhưng không phải nhãn ngữ âm đã xác nhận bằng nghe. Frame ZCR cao vẫn có thể tuần hoàn: không dùng riêng ZCR để khẳng định unvoiced.
Các xung rời cuối bản ghi (đặc biệt hai_01/bon_01) cũng tạo peak energy; cần phân biệt với tiếng nói khi làm endpoint ở Phase 4.
RMS frame Hamming khác RMS toàn file. Log-energy không phải SPL/dBFS. Pitch là minh họa từ frame 25 ms, có thể sai octave hoặc thiếu chu kỳ ở pitch thấp; không dùng làm feature bắt buộc cho DTW.

## Sản phẩm

- outputs/phase3_frame_features.csv: từng frame của 25 WAV.
- outputs/phase3_summary.csv: thống kê từng file.
- outputs/phase3_frame_examples.csv: frame nền/hữu thanh/ZCR cao/vô thanh hoặc nhiễu ứng viên.
- figures/phase3_time_features_<label>.png: 5 hình waveform + log-energy + RMS + magnitude + ZCR.
- figures/phase3_autocorrelation.png: minh họa periodicity và pitch.
