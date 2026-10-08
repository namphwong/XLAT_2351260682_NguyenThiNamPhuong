# Phase 5 — MFCC

Đã trích MFCC của 25 WAV trim; tổng 1815 frame. Mỗi ma trận (T,13), T từ 41 đến 176; split 15 train + 10 test giữ nguyên.

## Cấu hình

16 kHz; tiền nhấn alpha=0.97; frame 400 mẫu, hop 160 mẫu; Hamming đối xứng; FFT zero-pad 512; power=abs(FFT)^2/512; 24 tam giác peak-1, Mel=1125*ln(1+f/700), không chuẩn hóa diện tích; log tự nhiên với epsilon=1e-9; DCT-II orthonormal, giữ C0-C12; CMN theo utterance; không liftering.

## Quan sát

- không (khong/khong_01.wav): shape (80, 13); mean sau CMN tối đa |μ|=4.210e-14.
- một (mot/mot_01.wav): shape (61, 13); mean sau CMN tối đa |μ|=2.097e-14.
- hai (hai/hai_01.wav): shape (76, 13); mean sau CMN tối đa |μ|=1.552e-14.
- ba (ba/ba_01.wav): shape (91, 13); mean sau CMN tối đa |μ|=1.421e-14.
- bốn (bon/bon_01.wav): shape (59, 13); mean sau CMN tối đa |μ|=1.252e-14.
- Sai số mean sau CMN lớn nhất trong 25 file: 4.210e-14.
- Số frame thay đổi do thời lượng trim khác nhau; mỗi frame luôn 13 hệ số vì giữ cùng n_mfcc. Heatmap khác nhau theo thời gian và hệ số; chưa dùng để khẳng định phân loại đúng hay sai.
- Các vùng margin năng lượng thấp cũng xuất hiện trên heatmap; chất lượng endpoint ảnh hưởng các frame feature.

## Giải thích pipeline

Mel tăng mật độ phân giải ở tần số thấp. Log nén dynamic range. DCT biểu diễn log-Mel trên cơ sở cosine; 13 hệ số bậc thấp tạo biểu diễn gọn. CMN trừ mean theo từng hệ số của chính utterance, không gộp train/test.

## Khác biệt với baseline Librosa và giới hạn

Triển khai theo công thức lý thuyết của đề, dùng log tự nhiên/Mel công thức 1125ln và frame400 trước FFT512. Không dùng mặc định Slaney/log-dB/framing512 của lời gọi Librosa. Giá trị số có thể khác baseline nhưng cấu hình nhất quán cho mọi file.
Pitch không được ghép vào MFCC. Chưa thêm delta (để dành E2). Có 7 file endpoint cần kiểm tra nghe ở Phase 4; MFCC không tự sửa biên trim hoặc âm bị mất.

## Sản phẩm

- features/mfcc/<label>/*.npz: 25 file gồm MFCC, raw MFCC, log-Mel, thời gian, cấu hình và hash WAV trim.
- mfcc_config.json; outputs/phase5_mfcc_summary.csv.
- figures/phase5_mfcc_<label>.png: 5 heatmap cùng thang màu.
- phase5_mel_filterbank.png; phase5_cmn_comparison.png.
- Hàm mfcc_feature trả (T,13), sẵn sàng dùng trong DTW Phase 6.
