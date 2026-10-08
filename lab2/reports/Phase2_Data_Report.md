# Báo cáo dữ liệu Lab 2

### Kết quả kiểm tra Phase 2

- Đủ 25 WAV: 5 nhãn × 5 bản ghi; tất cả PCM mono 16 kHz.
- Split đã chốt: 15 train/template, 10 test; không trùng đường dẫn hoặc nội dung âm thanh.
- Thời lượng: 1.656–4.248 s, trung bình 2.549 s.
- 0 file có mẫu gần full-scale (ngưỡng |x| ≥ 0,999).
- 22 file RMS < 0,005: cần nghe lại mức âm lượng; chưa tăng gain ở Phase 2.
- Ước lượng RMS: 24 file có khoảng yên đầu/cuối < 0,2 s; 20 file có khoảng yên đầu/cuối > 0,5 s. Có thể trùng cả hai nhóm. Đây là cảnh báo sơ bộ, không khẳng định mất âm.
- Đã lưu waveform của 5 từ.
- Cần người thu nghe lại để xác nhận nhãn và chỉ một từ/file; phân tích biên speech chi tiết ở Phase 3–4.

Nguồn: 25 MP3 mono 48 kHz. Giữ nguyên MP3; chuyển PCM_16 mono 16 kHz, không cắt silence hoặc tăng gain. Đổi định dạng không khôi phục thông tin đã mất do nén MP3. Chi tiết trong outputs/audio_conversion.csv, outputs/dataset_audit.csv và data_split.csv.
