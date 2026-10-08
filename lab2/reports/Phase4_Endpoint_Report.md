# Phase 4 — Endpoint detection

Đã trim và kiểm tra sample của 25 WAV; giữ split 15 train + 10 test.
Tổng thời lượng 63.720 → 18.525 s; giảm 70.93%.
Trung bình 2.549 → 0.741 s/file.

## Cấu hình và phương pháp

Frame 25 ms, hop 10 ms, Hamming; median log-energy 5 frame; nền median ở 200 ms đầu/cuối (bỏ frame zero số). Ngưỡng cao=max(peak-18,noise+12), thấp=max(peak-30,noise+6) dB; nối gap 40 ms, vùng chính ít nhất 120 ms, mở rộng tối đa 150 ms/phía, ZCR>=0.10 chỉ hỗ trợ khi đủ energy; margin 80 ms/phía. Có fallback theo peak khi nền đầu/cuối chứa âm mạnh; xem warning từng file.

## Kiểm tra và nhận xét

- Có 7 file cảnh báo, cần nghe để kiểm tra vùng bị loại/fallback.
- khong_01.wav: frame onset ứng viên t=2.032 s được giữ trọn với margin 80 ms (True). Đây là kiểm tra vị trí frame, chưa xác nhận ngữ âm bằng nghe.
- Các hình hai_01/bon_01 cho thấy xung cuối rời khỏi vùng tiếng nói chính; trim chọn đoạn liên tục chính thay vì giữ mọi peak.
- Cả margin 0/50/80/120 ms đều giữ frame onset ứng viên; chọn 80 ms để có vùng đệm, chưa chứng minh tối ưu bằng nhãn biên hoặc accuracy.
- Chọn vùng dài nhất là heuristic cho từ đơn, có thể bỏ nhầm phụ âm/vùng speech tách xa; không áp dụng trực tiếp cho nhiều từ.
- Đầu ra là lát cắt nguyên mẫu WAV nguồn, không tăng gain; PCM_16 mono 16 kHz. Biên sample end exclusive; frame cuối inclusive.
- Chưa xác nhận bằng nghe: cần dùng listen_endpoint_comparison cho các file cảnh báo và onset năng lượng thấp.

## Sản phẩm

- trimmed/<label>/*.wav: 25 WAV đã trim.
- endpoint_config.json: cấu hình dùng chung cho train/test.
- outputs/phase4_trim_results.csv: biên, thời lượng, ngưỡng, hash và warning.
- outputs/phase4_margin_comparison.csv: margin 0/50/80/120 ms trên khong_01.
- figures/phase4_endpoint_<label>.png: 5 hình kiểm tra biên.
- figures/phase4_duration_comparison.png và phase4_weak_onset_margin.png.

## Các file cần ưu tiên nghe

- hai/hai_04.wav: Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói
- hai/hai_05.wav: Nền đầu/cuối có thể chứa âm mạnh; dùng ngưỡng tương đối theo peak; Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói
- ba/ba_01.wav: Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói
- ba/ba_02.wav: Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói
- bon/bon_01.wav: Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói
- bon/bon_04.wav: Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói
- bon/bon_05.wav: Có vùng năng lượng khác ngoài vùng chính; cần nghe để xác nhận không phải tiếng nói
