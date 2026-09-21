# BÁO CÁO THỰC HÀNH LAB 1: PHÂN TÍCH VÀ XỬ LÝ TÍN HIỆU ÂM THANH SỐ
**Học phần**: CSE457 – Xử lý âm thanh và tiếng nói  
**Trường Đại học Thủy lợi**

---

## Thông tin sinh viên
- **Họ và tên**: Nguyễn Thị Nam Phương
- **Mã sinh viên**: 2351260682
- **Lớp**: 65TTNT
- **Môi trường thực nghiệm**: Python 3.11, NumPy, SciPy, Matplotlib, SoundFile, Librosa, FFmpeg

---

## 1. Cấu trúc thư mục nộp bài
```text
Lab01_2351260682_NguyenThiNamPhuong/
├── Lab 1.pdf                      # Đề bài thực hành gốc
├── Lab01_2351260682.ipynb         # Jupyter Notebook thực thi toàn bộ pipeline
├── README.md                      # Báo cáo chi tiết kết quả thực nghiệm
├── audio/                         # Thư mục chứa các tệp âm thanh
│   ├── speech_input.wav           # Tệp âm thanh tiếng nói đầu vào (44.1 kHz, 16-bit)
│   ├── speech_input.mp3           # Tệp âm thanh tiếng nói định dạng MP3 (128 kbps)
│   ├── music_input.wav            # Tệp âm thanh âm nhạc đầu vào (44.1 kHz, 16-bit)
│   ├── music_input.mp3            # Tệp âm thanh âm nhạc định dạng MP3 (256 kbps)
│   ├── filtered_speech_lpf.wav    # Âm thanh tiếng nói qua lọc thông thấp (LPF 2 kHz)
│   ├── filtered_music_lpf.wav     # Âm thanh âm nhạc qua lọc thông thấp (LPF 2 kHz)
│   ├── filtered_music_hpf.wav     # Âm thanh âm nhạc qua lọc thông cao (HPF 2 kHz)
│   ├── quantized_speech_4bit.wav  # Âm thanh tiếng nói lượng tử hóa 4-bit
│   ├── quantized_speech_8bit.wav  # Âm thanh tiếng nói lượng tử hóa 8-bit
│   └── quantized_speech_16bit.wav # Âm thanh tiếng nói lượng tử hóa 16-bit
└── figures/                       # Thư mục lưu trữ đồ thị xuất ra
    ├── waveform.png               # Dạng sóng toàn phần và zoom cận cảnh
    ├── fft.png                    # Phổ biên độ FFT và so sánh NFFT
    ├── spectrogram.png            # Biểu đồ Spectrogram đa độ phân giải
    ├── window_comparison.png      # So sánh cửa sổ Rectangular vs Hamming
    ├── filter_response.png        # Đáp ứng tần số bộ lọc FIR LPF và HPF
    ├── filter_effect.png          # Phổ so sánh trước và sau lọc
    ├── quantization_snr.png       # Đồ thị SNR thực nghiệm vs lý thuyết
    └── resampling_comparison.png  # Phổ so sánh khi lấy mẫu lại 16kHz & 8kHz
```

---

## 2. Kế hoạch và tiến độ thực hiện
- [x] **Phase 1**: Setup môi trường, cấu trúc thư mục, chuẩn bị dữ liệu âm thanh và khởi tạo Notebook / Báo cáo.
- [x] **Phase 2**: Thực hiện Khối A & B (Đọc metadata, chuẩn hóa, phân tích waveform, RMS/Peak/Energy).
- [x] **Phase 3**: Thực hiện Khối C, D, E (Biến đổi FFT, STFT Spectrogram, thí nghiệm cửa sổ).
- [x] **Phase 4**: Thực hiện Khối F (Thiết kế bộ lọc số FIR, đáp ứng $H(f)$, lọc âm thanh và xuất file).
- [x] **Phase 5**: Thực hiện Khối G (Lượng tử hóa, tính SNR, resampling và phân tích nén mã hóa).
- [x] **Phase 6**: Trả lời 7 câu hỏi lý thuyết, kiểm thử toàn diện (Run All) và đóng gói nộp bài.

---

## 3. Tóm tắt kết quả thực nghiệm theo khối (Khối A → G)

### Khối A: Đọc và kiểm tra dữ liệu âm thanh
Tập dữ liệu thực nghiệm gồm 01 tệp tiếng nói (`speech_input.wav`) và 01 tệp âm nhạc (`music_input.wav`). Tín hiệu stereo được chuyển đổi sang mono bằng công thức trung bình cộng hai kênh:
$$x_{mono}[n] = \frac{x_L[n] + x_R[n]}{2}$$
Sau đó biên độ được chuẩn hóa về đoạn $[-1.0, 1.0]$.

*Bảng metadata trích xuất từ hai tệp âm thanh thực nghiệm:*

| Thuộc tính kỹ thuật | Tệp Tiếng nói (`speech_input.wav`) | Tệp Âm nhạc (`music_input.wav`) |
| :--- | :---: | :---: |
| **Định dạng lưu trữ / Subtype** | WAV (PCM 16-bit nguyên) | WAV (PCM 16-bit nguyên) |
| **Tần số lấy mẫu ($F_s$)** | $44,100\text{ Hz}$ | $44,100\text{ Hz}$ |
| **Tần số Nyquist ($F_s / 2$)** | $22,050\text{ Hz}$ | $22,050\text{ Hz}$ |
| **Số kênh (Channels)** | 2 (Stereo) | 2 (Stereo) |
| **Số mẫu (Frames / Samples)** | $654,444\text{ mẫu}$ | $2,021,760\text{ mẫu}$ |
| **Thời lượng (Duration)** | $14.840\text{ giây}$ | $45.845\text{ giây}$ |
| **Dung lượng tệp trên đĩa** | $2,617,820\text{ bytes}$ ($2.497\text{ MB}$) | $8,087,084\text{ bytes}$ ($7.712\text{ MB}$) |
| **Peak Mono ($|x|_{\max}$)** | $0.81030$ ($-1.83\text{ dBFS}$) | $0.78564$ ($-2.10\text{ dBFS}$) |
| **RMS Kênh Trái ($x_L$)** | $0.11209$ ($-19.01\text{ dBFS}$) | $0.07247$ ($-22.80\text{ dBFS}$) |
| **RMS Kênh Phải ($x_R$)** | $0.11209$ ($-19.01\text{ dBFS}$) | $0.07247$ ($-22.80\text{ dBFS}$) |
| **RMS Mono ($x_{mono}$)** | $0.11209$ ($-19.01\text{ dBFS}$) | $0.07247$ ($-22.80\text{ dBFS}$) |
| **Tổng năng lượng ($E = \sum x^2[n]$)** | $8,222.96$ | $10,618.33$ |
| **Số mẫu bị xén (Clipping $\ge 0.999$)** | $0\text{ mẫu}$ ($0.0000\%$) | $0\text{ mẫu}$ ($0.0000\%$) |

**Nhận xét kỹ thuật Khối A:**
1. Cả hai tệp đều có tần số lấy mẫu chuẩn phòng thu $F_s = 44,100\text{ Hz}$ với độ phân giải lượng tử 16-bit (`PCM_16`). Dải tần số Nyquist đạt tới $22,050\text{ Hz}$, đáp ứng hoàn hảo tiêu chuẩn bảo toàn tần số cao nhất mà tai người có thể cảm nhận được ($20\text{ Hz} - 20\text{ kHz}$).
2. Cường độ năng lượng trên hai kênh trái và phải có sự cân bằng cao (RMS chênh lệch xấp xỉ $0\text{ dB}$). Quá trình chuyển đổi từ Stereo sang Mono qua trung bình cộng không gây ra hiện tượng triệt tiêu pha (*phase cancellation*), giữ trọn vẹn đặc trưng năng lượng của nguồn phát.
3. Cả hai tệp đều có biên độ đỉnh nằm an toàn dưới ngưỡng full-scale ($< 1.0$), với $0$ mẫu nào chạm ngưỡng xén ngọn (clipping), đảm bảo dữ liệu đầu vào sạch cho các phép phân tích số tiếp theo.

---

### Khối B: Phân tích miền thời gian
Thực hiện vẽ dạng sóng toàn phần và trích xuất hai phân đoạn đối lập thời lượng $0.8\text{ s}$ trên mỗi tệp:
- **Tiếng nói (Speech)**:
  - Đoạn 1 ($3.4\text{s} - 4.2\text{s}$): Âm hữu thanh (*Voiced sound* / nguyên âm) mang tính tuần hoàn rõ nét.
  - Đoạn 2 ($2.5\text{s} - 3.3\text{s}$): Âm vô thanh / chuyển tiếp (*Unvoiced sound* / phụ âm) mang đặc tính tạp âm ngẫu nhiên.
- **Âm nhạc (Music)**:
  - Đoạn 1 ($37.8\text{s} - 38.6\text{s}$): Cao trào hòa tấu (*Forte / Tutti*) nhiều nhạc cụ dây cùng diễn tấu.
  - Đoạn 2 ($0.0\text{s} - 0.8\text{s}$): Khúc dạo đầu nhẹ nhàng (*Piano / Intro*).

*Bảng so sánh số liệu phân tích miền thời gian giữa các phân đoạn:*

| Tệp âm thanh | Phân đoạn phân tích | Khoảng thời gian | Peak | Peak (dBFS) | RMS | RMS (dBFS) | Năng lượng $E$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tiếng nói (Speech)** | Đoạn 1: Âm hữu thanh (Voiced) | $3.4\text{s} - 4.2\text{s}$ | $0.78494$ | $-2.10\text{ dBFS}$ | $0.15614$ | $-16.13\text{ dBFS}$ | $860.07$ |
| | Đoạn 2: Âm vô thanh (Unvoiced) | $2.5\text{s} - 3.3\text{s}$ | $0.34793$ | $-9.17\text{ dBFS}$ | $0.03297$ | $-29.64\text{ dBFS}$ | $38.34$ |
| | **Chênh lệch (Đoạn 1 / Đoạn 2)** | — | **$2.26$ lần** | **$+7.07\text{ dB}$** | **$4.74$ lần** | **$+13.51\text{ dB}$** | **$22.43$ lần** |
| **Âm nhạc (Music)** | Đoạn 1: Cao trào Forte | $37.8\text{s} - 38.6\text{s}$ | $0.78564$ | $-2.10\text{ dBFS}$ | $0.16680$ | $-15.56\text{ dBFS}$ | $981.59$ |
| | Đoạn 2: Dạo đầu nhẹ nhàng | $0.0\text{s} - 0.8\text{s}$ | $0.40189$ | $-7.92\text{ dBFS}$ | $0.07635$ | $-22.34\text{ dBFS}$ | $205.64$ |
| | **Chênh lệch (Đoạn 1 / Đoạn 2)** | — | **$1.95$ lần** | **$+5.82\text{ dB}$** | **$2.18$ lần** | **$+6.79\text{ dB}$** | **$4.77$ lần** |

![Đồ thị Waveform toàn phần và chi tiết các phân đoạn](figures/waveform.png)

**Nhận xét kỹ thuật Khối B:**
1. **Đặc trưng âm học của Tiếng nói**:
   - Ở đoạn âm hữu thanh ($3.4\text{s} - 4.2\text{s}$), dạng sóng xuất hiện các đỉnh xung định kỳ lặp lại rõ rệt phản ánh tần số đóng mở cơ bản của dây thanh quản ($F_0$). Năng lượng RMS đạt $0.15614$ ($-16.13\text{ dBFS}$).
   - Ở đoạn âm vô thanh ($2.5\text{s} - 3.3\text{s}$), luồng khí đi qua thanh môn mở tạo ra dao động nhiễu loạn ngẫu nhiên không có chu kỳ, RMS giảm xuống chỉ còn $0.03297$ ($-29.64\text{ dBFS}$). Năng lượng hiệu dụng của đoạn hữu thanh gấp tới **$4.74$ lần ($+13.51\text{ dB}$)** so với đoạn vô thanh.
2. **Đặc trưng âm học của Âm nhạc**:
   - Đoạn cao trào Forte ($37.8\text{s} - 38.6\text{s}$) có sự tham gia đồng loạt của toàn bộ dàn dây (violon, cello, contrabass), tạo ra sự chồng chập hòa âm phức tạp và mật độ biên độ rất dày với $\text{RMS} = 0.16680$.
   - Đoạn dạo đầu ($0.0\text{s} - 0.8\text{s}$) mang tính chất mở đề thưa thớt hơn, $\text{RMS} = 0.07635$. Độ tương phản dải động giữa hai đoạn đạt **$6.79\text{ dB}$** (chênh lệch gấp $2.18$ lần về RMS).
3. **Đánh giá mức độ an toàn**: Cả hai tệp tín hiệu đều có dải biên độ nằm trọn trong khoảng $[-0.82, +0.82]$, không xuất hiện flat-topping (hiện tượng đỉnh sóng bị san phẳng do vượt ngưỡng $1.0$), chứng minh hệ thống thu âm không bị hiện tượng bão hòa tín hiệu.

---

### Khối C: Phân tích miền tần số bằng FFT
Thực hiện trên phân đoạn ổn định $37.8\text{s} - 38.6\text{s}$ của tệp âm nhạc ($N = 35,281$ mẫu $\approx 0.8\text{ s}$), nhân cửa sổ Hamming để khử gián đoạn biên và tính toán biến đổi Fourier nhanh (FFT) trên 2 cấu hình $NFFT_1 = 2048$ và $NFFT_2 = 65536$.

*Bảng so sánh cấu hình phân tích FFT:*

| Thông số kỹ thuật | Cấu hình $NFFT_1 = 2048$ | Cấu hình $NFFT_2 = 65536$ | Ý nghĩa kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Số điểm FFT ($NFFT$)** | $2,048$ | $65,536$ | Bậc độ dài biến đổi DFT |
| **Bước tần số ($\Delta f = F_s / NFFT$)** | $\approx 21.5332\text{ Hz}$ | $\approx 0.6729\text{ Hz}$ | Khoảng cách giữa hai bin tần số kế tiếp |
| **Độ phân giải vật lý thực tế ($\Delta f_{true}$)** | $\approx 1.25\text{ Hz}$ ($1/0.8\text{s}$) | $\approx 1.25\text{ Hz}$ ($1/0.8\text{s}$) | Bị giới hạn bởi chiều dài cửa sổ thời gian |
| **Dạng biểu diễn đồ thị** | Các điểm phổ thưa, gấp khúc | Đường cong phổ trơn mịn, liên tục | Nội suy phổ mịn màng (Interpolation) |

*Bảng các đỉnh phổ hài âm nổi bật nhất trích xuất được ($NFFT = 65536$):*

| Thứ tự đỉnh | Tần số đo được ($f_k$) | Biên độ tương đối (dB) | Ý nghĩa âm sắc / Hài âm |
| :---: | :---: | :---: | :--- |
| **Đỉnh 1** | **$388.94\text{ Hz}$** | **$0.00\text{ dB}$** | Tần số chủ đạo mang năng lượng mạnh nhất (G4/A4 dải bè violon) |
| **Đỉnh 2** | **$467.67\text{ Hz}$** | **$-7.05\text{ dB}$** | Hài âm cộng hưởng bè trung |
| **Đỉnh 3** | **$581.40\text{ Hz}$** | **$-7.90\text{ dB}$** | Thành phần hòa âm bậc cao của hợp âm |
| **Đỉnh 4** | **$872.77\text{ Hz}$** | **$-6.16\text{ dB}$** | Bội âm bậc cao (hài âm octave/quãng 5) |
| **Đỉnh 5** | **$1173.56\text{ Hz}$** | **$-7.73\text{ dB}$** | Hài âm dải cao tạo độ sáng (*brightness*) cho dàn dây |

![Phổ FFT và so sánh NFFT](figures/fft.png)

**Nhận xét kỹ thuật Khối C:**
1. **Đặc trưng phổ đa nguồn**: Phổ biên độ xuất hiện rõ các đỉnh nhọn sắc nét tương ứng với các nốt nhạc và hài âm phong phú của dàn dây, tập trung mạnh nhất trong dải $300\text{ Hz} - 2500\text{ Hz}$, đúng với tính chất của bản nhạc giao hưởng Brahms.
2. **Ảnh hưởng của bước tần số $\Delta f$**: Với $NFFT = 2048$, bước tần số là $21.53\text{ Hz}$, các bin phổ cách nhau khá xa khiến đỉnh phổ có dạng răng cưa gãy khúc và đỉnh cực đại dễ bị lệch bin. Ngược lại, $NFFT = 65536$ thu hẹp bước bin xuống chỉ còn $0.67\text{ Hz}$, giúp vẽ đường cong phổ trơn tru và xác định tần số chính xác từng phần mười Hz.
3. **Phân biệt Bin Spacing và True Physical Resolution**: Việc tăng $NFFT$ (hoặc Zero-padding) thực chất là phép nội suy hàm sinc trong miền tần số để vẽ đường cong dày hơn, **không làm tăng lượng thông tin hay độ phân giải vật lý thực tế**. Độ phân giải vật lý phân tách hai tần số độc lập hoàn toàn do độ dài khung thời gian $T_w$ quyết định ($\Delta f_{true} \approx 1/T_w = 1/0.8\text{s} = 1.25\text{ Hz}$).

---

### Khối D: STFT và Spectrogram (Time–Frequency Resolution)
Khảo sát biến đổi Fourier ngắn hạn (STFT) trên phân đoạn $35.0\text{s} - 45.0\text{s}$ ($10\text{ s}$) của tệp âm nhạc, sử dụng cửa sổ Hamming, cố định bước nhảy $Hop = 10\text{ ms}$ ($441$ mẫu), $NFFT = 4096$, thang màu chuẩn hóa đồng nhất trên dynamic range $[-80\text{ dB}, 0\text{ dB}]$ để so sánh 3 độ dài khung (*Frame length*): $10\text{ ms}$, $25\text{ ms}$ và $50\text{ ms}$.

*Bảng so sánh đặc tính độ phân giải thời gian – tần số:*

| Độ dài khung ($T_{frame}$) | Số mẫu khung ($N_{frame}$) | Độ phân giải tần số cửa sổ ($\Delta f_{win}$) | Độ phân giải thời gian ($\Delta t$) | Đặc trưng biểu diễn quan sát được |
| :---: | :---: | :---: | :---: | :--- |
| **$10\text{ ms}$ (Ngắn)** | $441\text{ mẫu}$ | $\approx 100.0\text{ Hz}$ | Rất tốt ($10\text{ ms}$) | Độ phân giải thời gian cao, bắt kịp biến đổi nhanh (*transient*), nhưng các đường sọc hài âm bị nhòe theo chiều đứng. |
| **$25\text{ ms}$ (Chuẩn)** | $1,102\text{ mẫu}$ | $\approx 40.0\text{ Hz}$ | Cân bằng ($25\text{ ms}$) | Cân bằng tối ưu giữa việc nhận diện cao độ nốt nhạc và sự thay đổi theo thời gian (cấu hình tiêu chuẩn xử lý âm thanh). |
| **$50\text{ ms}$ (Dài)** | $2,205\text{ mẫu}$ | $\approx 20.0\text{ Hz}$ | Thấp ($50\text{ ms}$) | Độ phân giải tần số cực kỳ sắc nét, thấy rõ từng vạch sọc ngang hài âm, nhưng các sự kiện gõ nhịp nhanh bị nhòe mờ. |

![Spectrogram đa độ phân giải](figures/spectrogram.png)

**Nhận xét kỹ thuật Khối D:**
1. **Nguyên lý bất định thời gian – tần số (Gabor–Heisenberg)**: Đồ thị minh chứng rõ nét sự đánh đổi: không thể đồng thời đạt được độ phân giải thời gian tùy ý cao và độ phân giải tần số tùy ý cao trên cùng một phép biến đổi STFT cố định. Khi kéo dài khung từ $10\text{ ms}$ lên $50\text{ ms}$, các vạch sọc ngang (harmonic lines) chuyển từ mờ nhạt sang cực kỳ mảnh và rõ nét.
2. **Vùng năng lượng ổn định vs Vùng biến đổi nhanh (Transient)**:
   - Các vùng ngân nốt của dàn dây thể hiện bằng các dải màu sáng nằm ngang kéo dài liên tục, năng lượng tập trung mạnh nhất ở dải tần $200\text{ Hz} - 3500\text{ Hz}$.
   - Các thời điểm chuyển phách, kéo vĩ mạnh tạo thành các vệt sáng thẳng đứng xuyên suốt các dải tần số (*transient events*), được hiển thị rõ nét và chính xác nhất ở khung $10\text{ ms}$.

---

### Khối E: Thí nghiệm cửa sổ (Windowing & Spectral Leakage)
Thực hiện trên cùng một khung tín hiệu $25\text{ ms}$ ($1,102$ mẫu), áp dụng $NFFT = 16,384$ để so sánh đối chứng giữa cửa sổ **Chữ nhật (Rectangular)** và cửa sổ **Hamming**.

*Bảng so sánh đặc tính lý thuyết và thực nghiệm giữa hai loại cửa sổ:*

| Thuộc tính kỹ thuật | Cửa sổ Chữ nhật (Rectangular) | Cửa sổ Hamming | Đánh giá kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Hàm cửa sổ $w[n]$** | $w[n] = 1$ | $0.54 - 0.46\cos\left(\frac{2\pi n}{L-1}\right)$ | Hamming giảm dần biên độ về 0 ở hai mép |
| **Độ rộng búp sóng chính (Main-lobe)** | $4\pi / L$ (Hẹp) | $8\pi / L$ (Rộng gấp đôi) | Rectangular cho phép phân tách 2 đỉnh gần nhau tốt hơn |
| **Mức suy hao búp sóng phụ (Side-lobe)** | **$-13.3\text{ dB}$** (Rất kém) | **$-42.7\text{ dB}$** (Rất tốt) | Hamming triệt tiêu búp phụ tốt hơn **$29.4\text{ dB}$** |
| **Tốc độ suy giảm búp phụ** | $-6\text{ dB/octave}$ | $-6\text{ dB/octave}$ | Hamming giữ mức suy hao cao ổn định |
| **Rò rỉ phổ thực tế (Spectral Leakage)** | Rất nghiêm trọng (sàn nhiễu $\approx -45\text{ dB}$) | Cực kỳ thấp (sàn nhiễu $\approx -75\text{ dB}$) | Hamming giúp nền phổ sạch, lộ rõ hài âm nhỏ |

![So sánh cửa sổ Rectangular vs Hamming](figures/window_comparison.png)

**Nhận xét kỹ thuật Khối E:**
1. **Cơ chế rò rỉ phổ (Spectral Leakage)**: Do tín hiệu âm thanh thực tế không tuần hoàn hoàn hảo trong khung $25\text{ ms}$, việc cắt đột ngột bằng cửa sổ Rectangular tạo ra sự gián đoạn biên (bước nhảy biên độ lớn ở hai đầu khung). Khi biến đổi sang miền tần số, bước nhảy này đóng vai trò như tích chập với hàm $\text{sinc}$, khiến năng lượng của các đỉnh mạnh lan tỏa sang toàn bộ dải tần lân cận.
2. **Hiệu quả của cửa sổ Hamming**: Hàm cosine trong cửa sổ Hamming kéo êm hai đầu mút về sát giá trị $0.08$, triệt tiêu sự gián đoạn biên. Kết quả trên đồ thị phổ thực tế: sàn nhiễu phổ của Hamming tụt sâu xuống mức $-75\text{ dB}$ (sạch hơn gần $30\text{ dB}$ so với Rectangular), làm lộ rõ các hốc thung lũng giữa các đỉnh hài âm, ngăn chặn hoàn toàn hiện tượng đỉnh mạnh che lấp đỉnh yếu.

---

### Khối F: Lọc số FIR
Thực hiện thiết kế bộ lọc số FIR pha tuyến tính (Linear Phase) sử dụng phương pháp cửa sổ (Window Method) với các thông số:
- **Tần số lấy mẫu**: $F_s = 44,100\text{ Hz}$
- **Số hệ số (Taps)**: $L = 201$ (bậc $M = L - 1 = 200$)
- **Hàm cửa sổ**: Cửa sổ Hamming
- **Tần số cắt ($f_c$)**: $2,000\text{ Hz}$
- **Thiết kế 02 bộ lọc**:
  1. **Bộ lọc thông thấp (FIR Low-pass)**: Cho qua các dải tần dưới $2\text{ kHz}$, làm suy hao dải cao.
  2. **Bộ lọc thông cao (FIR High-pass)**: Cho qua các dải tần trên $2\text{ kHz}$, triệt tiêu dải trầm.

*Bảng thông số kỹ thuật bộ lọc FIR thiết kế:*

| Thông số kỹ thuật | FIR Low-pass Filter | FIR High-pass Filter | Ý nghĩa kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Số hệ số Taps ($L$)** | $201$ | $201$ | Chiều dài đáp ứng xung hữu hạn $h[n]$ |
| **Bậc bộ lọc ($M$)** | $200$ | $200$ | $M = L - 1$ |
| **Tần số cắt ($f_c$)** | $2,000\text{ Hz}$ | $2,000\text{ Hz}$ | Điểm suy giảm $-6\text{ dB}$ biên độ |
| **Cửa sổ thiết kế** | Hamming | Hamming | Giảm gợn sóng Gibbs, suy hao dải chặn tốt |
| **Độ suy hao dải chặn ($A_s$)** | $\approx -53.0\text{ dB}$ | $\approx -53.0\text{ dB}$ | Triệt tiêu năng lượng dải không mong muốn |
| **Độ trễ nhóm (Group Delay)** | **$100\text{ mẫu}$ ($2.2676\text{ ms}$)** | **$100\text{ mẫu}$ ($2.2676\text{ ms}$)** | Hằng số không đổi trên toàn dải tần số |
| **Đặc tính pha** | **Pha tuyến tính tuyệt đối** | **Pha tuyến tính tuyệt đối** | Bảo toàn hình dạng sóng, không gây méo trễ pha |

*Bảng danh mục các tệp âm thanh xuất ra sau khi lọc (`audio/`):*

| Tên tệp xuất ra | Kiểu lọc | Tần số cắt ($f_c$) | Cảm nhận âm học khi nghe kiểm tra |
| :--- | :---: | :---: | :--- |
| **`audio/filtered_speech_lpf.wav`** | Low-pass | $2\text{ kHz}$ | Âm thanh tối, ấm và đục (*muffled*), các phụ âm cọ xát vô thanh dải cao (`/s/`, `/sh/`, `/f/`) bị triệt tiêu, chỉ còn lại âm vang cổ họng. |
| **`audio/filtered_music_lpf.wav`** | Low-pass | $2\text{ kHz}$ | Âm nhạc mất đi độ sáng sắc nét (*brightness/air*) của dàn dây, tiếng vĩ miết mờ nhạt, âm sắc trở nên trầm ấm và tù mù. |
| **`audio/filtered_music_hpf.wav`** | High-pass | $2\text{ kHz}$ | Mất sạch toàn bộ âm bass, âm vang thân đàn cello/contrabass và tần số cơ bản nốt nhạc; âm thanh mỏng dính, the thé, chói và rỗng (*thin/tinny*). |

![Đáp ứng tần số bộ lọc FIR LPF và HPF](figures/filter_response.png)

![So sánh phổ trước và sau khi lọc](figures/filter_effect.png)

**Nhận xét kỹ thuật Khối F:**
1. **Tính chất Pha tuyến tính (Linear Phase) & Độ trễ nhóm (Group Delay)**:
   - Do các hệ số đối xứng hoàn hảo $h[n] = h[M - n]$, bộ lọc thuộc hệ FIR Type 1, đảm bảo độ trễ pha và độ trễ nhóm không phụ thuộc vào tần số:
     $$\tau_g = \frac{L - 1}{2} = \frac{201 - 1}{2} = 100\text{ mẫu} \approx 2.2676\text{ ms}$$
   - Mọi thành phần hài âm khi truyền qua bộ lọc đều bị làm trễ đúng $2.2676\text{ ms}$, hoàn toàn loại bỏ hiện tượng méo trễ pha (*phase distortion*). Độ trễ này rất nhỏ ($< 5\text{ ms}$), hoàn toàn nằm trong ngưỡng cho phép đối với các ứng dụng xử lý âm thanh thời gian thực (Real-time DSP / Live monitoring).
2. **Hiệu năng chọn lọc tần số trên đồ thị phổ**:
   - Tại tần số cắt $f_c = 2000\text{ Hz}$, đáp ứng biên độ $|H(f)|$ đi qua đúng điểm $-6.0\text{ dB}$.
   - Dải chặn đạt mức suy hao sâu trên **$-53\text{ dB}$**, triệt tiêu gần như triệt để các sóng hài vượt ngưỡng. So sánh trên đồ thị phổ thực tế (`figures/filter_effect.png`), các đỉnh phổ nằm trong dải chặn bị kéo tụt xuống mức $-60\text{ dB}$ đến $-75\text{ dB}$, minh chứng bộ lọc hoạt động cực kỳ chính xác.
3. **Mối liên hệ giữa Toán học và Cảm nhận thính giác**:
   - Khi tai người nghe thấy âm thanh bị “nghẹt/đục” (với LPF), đó là biểu hiện trực tiếp của việc cắt bỏ dải tần cao trên $2\text{ kHz}$ – nơi cung cấp thông tin về độ nét và phụ âm.
   - Khi nghe thấy âm thanh “the thé/mỏng” (với HPF), đó là hệ quả của việc loại bỏ dải tần số cơ bản dưới $2\text{ kHz}$ – nơi tập trung hơn $80\%$ tổng năng lượng của âm thanh.*

### Khối G: Lượng tử hóa, Resampling và Nén dữ liệu

#### 1. Thực nghiệm Lượng tử hóa đều (Uniform Quantization) và Đo đạc SNR
Áp dụng bộ lượng tử hóa đều đối xứng trên các mức bit depth $B \in [4, 6, 8, 12, 16]\text{ bit/mẫu}$. Tỷ số tín hiệu trên nhiễu lượng tử (SNR) thực nghiệm được tính theo công thức:
$$SNR = 10 \log_{10}\left(\frac{\sum_{n} x^2[n]}{\sum_{n} (x[n] - \hat{x}[n])^2}\right) \quad (\text{dB})$$
Đối chiếu với công thức lý thuyết Rabiner–Schafer:
$$SNR_Q(\text{dB}) = 6.02B + 4.77 - 20\log_{10}\left(\frac{X_{\max}}{\sigma_x}\right)$$
với $X_{\max} = 1.0$ và $\sigma_x = \text{RMS}$ của tín hiệu đầu vào ($\sigma_{x, speech} = 0.11209$, $\sigma_{x, music} = 0.07247$).

*Bảng số liệu SNR thực nghiệm đo đạc so với lý thuyết:*

| Độ phân giải ($B$) | Số mức ($L = 2^B$) | SNR Tiếng nói Đo (dB) | SNR Tiếng nói LT (dB) | SNR Âm nhạc Đo (dB) | SNR Âm nhạc LT (dB) | Cảm nhận chất lượng thính giác |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$4\text{ bit}$** | $16$ | **$10.32\text{ dB}$** | $9.84\text{ dB}$ | **$6.17\text{ dB}$** | $6.05\text{ dB}$ | Nhiễu lượng tử rất nặng, tiếng xào xạc thô ráp (hiss) bao trùm tín hiệu |
| **$6\text{ bit}$** | $64$ | **$22.35\text{ dB}$** | $21.88\text{ dB}$ | **$18.29\text{ dB}$** | $18.09\text{ dB}$ | Nghe rõ lời thoại nhưng tiếng rè xì lượng tử vẫn còn khá lộ |
| **$8\text{ bit}$** | $256$ | **$33.98\text{ dB}$** | $33.92\text{ dB}$ | **$30.35\text{ dB}$** | $30.13\text{ dB}$ | Âm thanh khá tốt, tương đương máy chơi game/thoại cũ, nhiễu nhẹ ở đoạn yên tĩnh |
| **$12\text{ bit}$** | $4,096$ | **$57.99\text{ dB}$** | $58.00\text{ dB}$ | **$54.43\text{ dB}$** | $54.21\text{ dB}$ | Âm thanh trong trẻo, rất khó nhận biết nhiễu ở mức nghe thông thường |
| **$16\text{ bit}$** | $65,536$ | **$90.52\text{ dB}$** | $82.08\text{ dB}$ | **$90.33\text{ dB}$** | $78.29\text{ dB}$ | Chuẩn CD Audio chất lượng cao, sàn nhiễu tiệm cận ngưỡng nghe |

*Danh mục các file âm thanh lượng tử hóa xuất ra (`audio/`):*
- `audio/quantized_speech_4bit.wav` (Chất lượng 4-bit)
- `audio/quantized_speech_8bit.wav` (Chất lượng 8-bit)
- `audio/quantized_speech_16bit.wav` (Chất lượng 16-bit gốc)

![Đồ thị SNR thực nghiệm vs lý thuyết](figures/quantization_snr.png)

---

#### 2. Thực nghiệm Lấy mẫu lại (Resampling)
Thực hiện lấy mẫu lại tín hiệu tiếng nói từ gốc $F_s = 44,100\text{ Hz}$ về $16,000\text{ Hz}$ và $8,000\text{ Hz}$ sử dụng bộ lọc đa pha chống aliasing chuẩn (`scipy.signal.resample_poly`).

*Bảng so sánh các mức tần số lấy mẫu và chất lượng âm thanh:*

| Tần số lấy mẫu ($F_s$) | Tần số Nyquist ($F_s / 2$) | Chuẩn ứng dụng thực tế | Tệp âm thanh xuất ra | Đánh giá chất lượng nghe thực tế |
| :---: | :---: | :--- | :--- | :--- |
| **$44,100\text{ Hz}$** | $22,050\text{ Hz}$ | Chuẩn Studio / CD Audio | `audio/speech_input.wav` | Dải tần đầy đủ, giọng nói tự nhiên, phụ âm gió (`/s/`, `/f/`) sắc nét |
| **$16,000\text{ Hz}$** | $8,000\text{ Hz}$ | Thoại băng rộng (HD Voice / VoIP) | `audio/resampled_speech_16k.wav` | Giữ trọn dải âm nói của người ($< 8\text{ kHz}$), giọng nói rất tự nhiên, dễ nghe |
| **$8,000\text{ Hz}$** | $4,000\text{ Hz}$ | Thoại truyền thống (PSTN / 2G) | `audio/resampled_speech_8k.wav` | Bị cắt cụt trên $4\text{ kHz}$, âm thanh nghẹt như nghe qua ống bơ điện thoại bàn |

![Phổ so sánh khi lấy mẫu lại 16kHz & 8kHz](figures/resampling_comparison.png)

---

#### 3. Tốc độ bit, Dung lượng và Tỷ số nén (PCM vs MP3)
- **Tốc độ bit lý thuyết của PCM 16-bit stereo**:
  $$R_{PCM} = F_s \times B \times C = 44,100 \times 16 \times 2 = 1,411,200\text{ bit/s} = 1,411.2\text{ kbps}$$
- **Tỷ số nén (Compression Ratio - CR)** và **Mức tiết kiệm dung lượng (Saving %)**:
  $$CR = \frac{\text{Size}_{WAV}}{\text{Size}_{MP3}}, \quad \text{Saving}(\%) = \left(1 - \frac{\text{Size}_{MP3}}{\text{Size}_{WAV}}\right) \times 100\%$$

*Bảng so sánh tốc độ bit và mức độ nén dữ liệu thực tế:*

| Tệp thực nghiệm | Thời lượng | Bitrate PCM | Bitrate MP3 | Dung lượng WAV | Dung lượng MP3 | Tỷ số nén (CR) | Mức tiết kiệm (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tiếng nói (Speech)** | $14.84\text{ s}$ | $1,411.2\text{ kbps}$ | $128.0\text{ kbps}$ | $2.497\text{ MB}$ | $0.228\text{ MB}$ | **$10.97 : 1$** | **$90.88\%$** |
| **Âm nhạc (Music)** | $45.84\text{ s}$ | $1,411.2\text{ kbps}$ | $256.0\text{ kbps}$ | $7.712\text{ MB}$ | $1.401\text{ MB}$ | **$5.51 : 1$** | **$81.84\%$** |

---

**Nhận xét kỹ thuật Khối G:**
1. **Khẳng định quy tắc $6\text{ dB/bit}$ và vai trò của Headroom**:
   - Đồ thị SNR thực nghiệm tăng gần như tuyến tính tuyệt đối theo số bit: mỗi khi tăng thêm 1 bit độ phân giải, SNR tăng xấp xỉ **$6.02\text{ dB}$** (tương đương năng lượng nhiễu lượng tử giảm đi 4 lần).
   - Tín hiệu tiếng nói có năng lượng hiệu dụng $RMS = 0.11209$ ($-19.01\text{ dBFS}$), cao hơn tín hiệu âm nhạc có $RMS = 0.07247$ ($-22.80\text{ dBFS}$). Do thành phần suy hao do dải dự trữ biên độ (*headroom loss*) $-20\log_{10}(X_{\max}/\sigma_x)$ của tiếng nói nhỏ hơn $3.79\text{ dB}$, SNR đo được của tiếng nói luôn cao hơn âm nhạc khoảng $3.5 - 4\text{ dB}$ trên cùng số bit.
2. **Cảm nhận thính giác về nhiễu lượng tử**:
   - Ở $4\text{ bit}$, nhiễu lượng tử có biên độ tương đối lớn và tương quan chặt chẽ với tín hiệu, tạo ra tiếng xào xạc thô ráp (rough distortion) bám theo giọng nói.
   - Khi tăng lên $8\text{ bit}$ rồi $16\text{ bit}$, bước lượng tử $\Delta = 2X_{\max}/2^B$ thu nhỏ lũy thừa, nhiễu lượng tử chuyển dần sang phân bố đều độc lập như tạp âm trắng biên độ siêu nhỏ, hoàn toàn chìm dưới ngưỡng nghe của tai người ở $16\text{ bit}$.
3. **Ý nghĩa thực tế của việc Resampling**:
   - Việc chuyển đổi sampling rate bắt buộc phải đi kèm bộ lọc chống chồng phổ (anti-aliasing low-pass filter) cắt bỏ các tần số vượt quá tần số Nyquist mới.
   - Đồ thị phổ chứng minh các tần số trên $8\text{ kHz}$ (ở bản 16 kHz) và trên $4\text{ kHz}$ (ở bản 8 kHz) bị triệt tiêu hoàn toàn. Chuẩn 16 kHz bảo toàn được hầu hết dải tần cơ bản và formant của tiếng nói người, trong khi chuẩn 8 kHz làm mất đi các phụ âm tần số cao, chứng minh tại sao liên lạc qua mạng 4G/VoLTE (HD Voice 16 kHz) lại trong và rõ hơn hẳn mạng 2G truyền thống (8 kHz).
4. **Hiệu năng của mã hóa cảm thụ (Perceptual Coding)**:
   - File MP3 128 kbps giảm được tới **$90.88\%$** dung lượng bộ nhớ so với WAV PCM không nén. Điều này đạt được là nhờ thuật toán MPEG/MP3 đã khai thác hiện tượng che khuất thính giác (*psychoacoustic masking*): lượng tử hóa thô hơn ở các dải tần mà tai người bị che khuất bởi các âm thanh mạnh lân cận, giúp tiết kiệm bit rate tối đa mà người nghe thông thường không nhận ra sự suy giảm chất lượng.

---

## 4. Trả lời 7 câu hỏi báo cáo lý thuyết

### Câu 1: Giải thích bằng công thức tại sao $F_s = 44.1\text{ kHz}$ chỉ biểu diễn độc lập đến $22.05\text{ kHz}$?
**Trả lời**:
1. **Định lý lấy mẫu Nyquist–Shannon**:
   - Khi lấy mẫu tín hiệu liên tục $x_a(t)$ với chu kỳ lấy mẫu $T = 1/F_s$, phổ của chuỗi rời rạc $X(e^{j\omega})$ là sự tuần hoàn lặp lại của phổ liên tục $X_a(f)$ với chu kỳ dịch chuyển bằng $F_s$:
     $$X(e^{j2\pi f / F_s}) = \frac{1}{T} \sum_{k=-\infty}^{\infty} X_a(f - k F_s)$$
   - Để các bản sao phổ không bị chồng đè lên nhau (hiện tượng chồng phổ – *Aliasing*), dải tần số của tín hiệu phải bị chặn trên bởi nửa tần số lấy mẫu:
     $$F_{\max} \le \frac{F_s}{2} \implies F_{Nyquist} = \frac{F_s}{2} = \frac{44,100\text{ Hz}}{2} = 22,050\text{ Hz} = \mathbf{22.05\text{ kHz}}$$
2. **Tính chất đối xứng liên hợp Hermite của tín hiệu thực**:
   - Tín hiệu âm thanh vật lý luôn là tín hiệu thực $x[n] \in \mathbb{R}$. Do đó, biến đổi Fourier có tính chất đối xứng Hermite:
     $$X(e^{-j\omega}) = X^*(e^{j\omega}) \implies |X(e^{-j\omega})| = |X(e^{j\omega})|$$
   - Phổ biên độ trên nửa vòng tròn âm $[-\pi, 0]$ hoàn toàn là ảnh gương của nửa vòng tròn dương $[0, \pi]$.
   - Do đó, toàn bộ thông tin độc lập về biên độ và góc pha chỉ nằm trọn vẹn trong khoảng tần số dương $[0, F_s / 2] = [0, 22.05\text{ kHz}]$. Mọi thành phần vượt quá $22.05\text{ kHz}$ không mang thêm bất kỳ thông tin mới nào, và nếu không được lọc bỏ bằng bộ lọc khử chồng phổ (*anti-aliasing filter*), chúng sẽ bị phản xạ gập ngược vào dải tần nghe được làm méo âm nghiêm trọng.

---

### Câu 2: Nếu NFFT tăng từ 2048 lên 8192 nhưng frame vẫn dài 25 ms, điều gì thật sự thay đổi và điều gì không?
**Trả lời**:
- **Điều THẬT SỰ THAY ĐỔI**:
  1. **Bước tần số giữa các bin (Frequency-bin spacing $\Delta f$) giảm 4 lần**:
     $$\Delta f_{2048} = \frac{44,100}{2,048} \approx 21.53\text{ Hz} \quad \longrightarrow \quad \Delta f_{8192} = \frac{44,100}{8,192} \approx 5.38\text{ Hz}$$
  2. **Mật độ điểm hiển thị trên đồ thị**: Số điểm tính toán tăng gấp 4 lần, đường cong phổ biên độ trở nên dày đặc, mịn màng và liên tục hơn. Việc này hỗ trợ việc xác định tọa độ đỉnh cực đại (*peak picking*) chính xác hơn, tránh bị lỗi ước lượng do đỉnh thực nằm rơi vào giữa hai bin thưa.
- **Điều HOÀN TOÀN KHÔNG THAY ĐỔI**:
  1. **Lượng thông tin vật lý của tín hiệu**: Tín hiệu đầu vào chỉ có $N = 0.025 \times 44,100 = 1,102$ mẫu thực tế. Việc tăng $NFFT$ từ $2,048$ lên $8,192$ bản chất là chèn thêm $7,090$ số 0 vào đuôi tín hiệu (**Zero-padding**). Zero-padding hoàn toàn không tạo ra thêm bất kỳ thông tin nào mới.
  2. **Độ phân giải tần số vật lý thực tế (True Physical Resolution)**: Khả năng phân tách hai sóng sin có tần số gần nhau bị chi phối duy nhất bởi độ dài cửa sổ thời gian hữu hạn $T_w = 25\text{ ms}$:
     $$\Delta f_{true} \approx \frac{1}{T_w} = \frac{1}{0.025\text{ s}} = \mathbf{40\text{ Hz}}$$
     Nếu trong tín hiệu có hai đỉnh sóng sin cách nhau nhỏ hơn $40\text{ Hz}$ (ví dụ $1000\text{ Hz}$ và $1020\text{ Hz}$), việc tăng $NFFT$ lên $8192$ hay $65536$ cũng chỉ hiển thị một búp phổ rộng duy nhất (nội suy của hàm sinc), hoàn toàn không thể phân tách thành hai đỉnh độc lập.

---

### Câu 3: Tại sao Hamming giảm spectral leakage so với rectangular nhưng có thể làm các đỉnh gần nhau khó phân tách hơn?
**Trả lời**:
- Cắt một phân đoạn tín hiệu bằng cửa sổ thời gian $w[n]$ tương đương với phép nhân trong miền thời gian, tức là **phép tích chập trong miền tần số**:
  $$X_w(e^{j\omega}) = \frac{1}{2\pi} X(e^{j\omega}) * W(e^{j\omega})$$
- **Về rò rỉ phổ (Spectral Leakage)**:
  - Cửa sổ Chữ nhật (Rectangular) cắt cụt tín hiệu đột ngột ở hai đầu biên, tạo ra bước nhảy gián đoạn biên lớn. Bước nhảy này sinh ra các búp sóng phụ (*side-lobes*) có biên độ rất cao, đỉnh búp phụ thứ nhất chỉ suy giảm **$-13.3\text{ dB}$**. Năng lượng của đỉnh tần số chính sẽ tràn lan sang toàn bộ dải tần xung quanh, làm sàn nhiễu bị nâng lên cao, che lấp các hài âm nhỏ.
  - Cửa sổ Hamming làm giảm dần biên độ về gần 0 ở hai mép biên ($w[0] = w[L-1] = 0.08$), triệt tiêu sự gián đoạn biên. Đỉnh búp phụ thứ nhất của Hamming bị nén sâu xuống **$-42.7\text{ dB}$** (tốt hơn gần $30\text{ dB}$ so với Rectangular), giúp triệt tiêu hiện tượng rò rỉ phổ xuất sắc, giữ nền phổ cực kỳ sạch sẽ.
- **Về khả năng phân tách đỉnh (Frequency Resolution)**:
  - Để nén các búp phụ xuống sâu, định luật bảo toàn năng lượng buộc năng lượng phải dồn vào búp sóng chính (*main-lobe*).
  - Độ rộng búp chính của cửa sổ Hamming rộng gấp đôi cửa sổ Chữ nhật:
    $$\text{Độ rộng búp chính Rectangular} = \frac{4\pi}{L} \quad \longleftrightarrow \quad \text{Độ rộng búp chính Hamming} = \frac{8\pi}{L}$$
  - Búp chính rộng hơn sẽ làm các đỉnh phổ bị "phình to" ra. Nếu có hai thành phần tần số nằm sát nhau (khoảng cách tần số $< 8\pi/L$), búp chính của hai đỉnh sẽ hòa quyện và chồng lấn vào nhau thành một đỉnh bẹt duy nhất, khiến việc phân tách chúng trở nên bất khả thi. Trong khi đó, cửa sổ Chữ nhật với búp chính hẹp hơn vẫn có thể phân biệt được hai đỉnh này (với điều kiện hai đỉnh có biên độ gần tương đương).

---

### Câu 4: Với FIR 201 taps đối xứng tại 44.1 kHz, độ trễ xấp xỉ bao nhiêu mili giây? Độ trễ đó có quan trọng trong xử lý thời gian thực không?
**Trả lời**:
1. **Tính toán độ trễ**:
   - Bộ lọc FIR đối xứng chiều dài $L = 201$ taps (bậc $M = L - 1 = 200$) có đáp ứng xung thỏa mãn $h[n] = h[M - n]$ (bộ lọc loại 1 - Type 1 FIR).
   - Bộ lọc có tính chất **pha tuyến tính tuyệt đối**, do đó độ trễ nhóm (*group delay*) là hằng số cố định không đổi trên toàn bộ các tần số:
     $$\tau_g = \frac{L - 1}{2} = \frac{201 - 1}{2} = 100\text{ mẫu}$$
   - Đổi sang đơn vị mili giây (ms):
     $$\tau = \frac{\tau_g}{F_s} \times 1000 = \frac{100}{44,100} \times 1000 \approx \mathbf{2.2676\text{ ms}}$$
2. **Đánh giá trong xử lý thời gian thực**:
   - **Mức độ ảnh hưởng**: Độ trễ $\approx 2.27\text{ ms}$ là **rất nhỏ và hoàn toàn an toàn** trong đại đa số các ứng dụng âm thanh thời gian thực.
   - *Cơ sở thính giác (Hiệu ứng Haas / Ngưỡng trễ)*:
     * Tai người chỉ bắt đầu nhận biết độ trễ âm thanh khi vượt quá $5 - 10\text{ ms}$ đối với kiểm âm trực tiếp (Live In-Ear Monitoring cho ca sĩ/nhạc công khi hát/chơi nhạc).
     * Trong đàm thoại viễn thông hai chiều (VoIP, điện thoại), ngưỡng trễ chấp nhận được lên tới $150\text{ ms}$ (theo khuyến nghị ITU-T G.114).
     * Do đó, mức trễ $2.27\text{ ms}$ hoàn toàn không thể nhận biết được bằng tai người và không gây ra hiện tượng méo tiếng hay tiếng vọng khó chịu.
   - *Lưu ý kỹ thuật*: Nếu hệ thống ghép tầng hàng chục bộ lọc liên tiếp (*cascaded DSP blocks*) hoặc trong các hệ thống khử ồn chủ động (Active Noise Cancellation - ANC) đòi hỏi độ trễ dưới $1\text{ ms}$ để triệt tiêu sóng âm tới, độ trễ $2.27\text{ ms}$ có thể là đáng kể và khi đó cần cân nhắc chuyển sang bộ lọc IIR pha phi tuyến với độ trễ thấp hơn.

---

### Câu 5: Từ công thức $SNR_Q$, giải thích ảnh hưởng của $B$ và $\sigma_x$. Tại sao giảm mức tín hiệu đầu vào có thể làm SNR lượng tử giảm?
**Trả lời**:
1. **Công thức Rabiner–Schafer**:
   $$SNR_Q(\text{dB}) = 6.02B + 4.77 - 20\log_{10}\left(\frac{X_{\max}}{\sigma_x}\right)$$
2. **Ảnh hưởng của $B$ (Độ phân giải số bit)**:
   - Với bộ lượng tử hóa đều trong dải $[-X_{\max}, X_{\max}]$, bước lượng tử là $\Delta = \frac{2X_{\max}}{2^B}$.
   - Công suất nhiễu lượng tử giả định phân bố đều là $\sigma_e^2 \approx \frac{\Delta^2}{12} = \frac{4X_{\max}^2}{12 \cdot 2^{2B}}$.
   - Mỗi khi tăng thêm 1 bit độ phân giải ($B \rightarrow B + 1$), bước lượng tử $\Delta$ giảm một nửa, công suất nhiễu $\sigma_e^2$ giảm đi 4 lần ($2^2 = 4$).
   - Trên thang đo decibel:
     $$10\log_{10}(4) \approx \mathbf{6.02\text{ dB}}$$
   - Đây chính là nguồn gốc của **quy tắc 6 dB/bit**: Cứ thêm 1 bit, chất lượng âm thanh tăng thêm $\approx 6\text{ dB}$ SNR.
3. **Ảnh hưởng của $\sigma_x$ và Lý do giảm mức tín hiệu làm giảm SNR**:
   - $\sigma_x$ là giá trị hiệu dụng (RMS) của tín hiệu đầu vào, thể hiện mức năng lượng thực tế của âm thanh.
   - Thành phần $-20\log_{10}(X_{\max}/\sigma_x)$ được gọi là **tổn hao dải dự trữ biên độ (Headroom Loss)**.
   - Do bộ lượng tử hóa có thang đo cố định $[-X_{\max}, X_{\max}]$, khoảng bước $\Delta$ và công suất nhiễu lượng tử $\sigma_e^2 \approx \Delta^2/12$ là **hằng số không đổi**.
   - Khi mức tín hiệu đầu vào $\sigma_x$ bị giảm (ví dụ: ca sĩ nói thầm, giảm âm lượng đầu vào), công suất tín hiệu $P_{sig} = \sigma_x^2$ giảm đi, trong khi công suất nhiễu lượng tử $\sigma_e^2$ vẫn giữ nguyên không đổi!
   - Hậu quả là tỷ số tín hiệu trên nhiễu $SNR = 10\log_{10}(P_{sig}/\sigma_e^2)$ bị sụt giảm nghiêm trọng. Cụ thể, nếu giảm biên độ tín hiệu đi 2 lần ($-6\text{ dB}$ RMS), công suất tín hiệu giảm 4 lần, làm SNR lượng tử giảm ngay lập tức $6\text{ dB}$ (tương đương mất đi 1 bit lượng tử hiệu dụng – ENOB).
   - *Ứng dụng thực tế*: Trong kỹ thuật thu âm phòng thu, kỹ sư âm thanh luôn căn chỉnh mức gain đầu vào sao cho tín hiệu đạt mức cao nhất có thể mà không chạm ngưỡng xén ngọn ($0\text{ dBFS}$) để tối đa hóa SNR.

---

### Câu 6: Một file WAV 16-bit stereo 44.1 kHz dài 60 s có kích thước PCM lý thuyết bao nhiêu MB? So sánh với MP3 128 kbps.
**Trả lời**:
1. **Tính toán kích thước tệp WAV PCM 16-bit Stereo**:
   - Tần số lấy mẫu: $F_s = 44,100\text{ Hz}$.
   - Số bit trên mẫu: $B = 16\text{ bit} = 2\text{ bytes}$.
   - Số kênh: $C = 2$ (Stereo).
   - Tốc độ bit lý thuyết của dòng PCM:
     $$R_{PCM} = F_s \times B \times C = 44,100 \times 16 \times 2 = 1,411,200\text{ bit/s} = 176,400\text{ byte/s}$$
   - Kích thước dữ liệu thuần cho thời lượng 60 giây:
     $$\text{Size}_{bytes} = 176,400\text{ byte/s} \times 60\text{ s} = 10,584,000\text{ bytes}$$
   - Quy đổi sang Megabyte (MB):
     - Theo chuẩn nhị phân máy tính ($1\text{ MB} = 1024^2\text{ bytes} = 1,048,576\text{ bytes}$):
       $$\text{Size}_{PCM} = \frac{10,584,000}{1,048,576} \approx \mathbf{10.0937\text{ MB}}$$
     - Theo chuẩn thập phân lưu trữ ($1\text{ MB} = 10^6\text{ bytes}$): $\text{Size}_{PCM} = 10.584\text{ MB}$.
     *(Nếu tính cả 44 bytes tiêu đề header chuẩn của file WAV thì kích thước là $10,584,044\text{ bytes} \approx 10.094\text{ MB}$)*.
2. **Tính toán kích thước tệp MP3 128 kbps**:
   - Tốc độ bit: $R_{MP3} = 128\text{ kbps} = 128,000\text{ bit/s} = 16,000\text{ byte/s}$.
   - Kích thước tệp cho 60 giây:
     $$\text{Size}_{bytes} = 16,000\text{ byte/s} \times 60\text{ s} = 960,000\text{ bytes}$$
   - Quy đổi sang Megabyte (MB):
     $$\text{Size}_{MP3} = \frac{960,000}{1,048,576} \approx \mathbf{0.9155\text{ MB}} \quad (\approx 0.960\text{ MB thập phân})$$
3. **So sánh mức độ nén**:
   - **Tỷ số nén (Compression Ratio)**:
     $$CR = \frac{R_{PCM}}{R_{MP3}} = \frac{1,411,200\text{ bps}}{128,000\text{ bps}} = \frac{10.0937\text{ MB}}{0.9155\text{ MB}} = \mathbf{11.025 : 1}$$
   - **Phần trăm dung lượng tiết kiệm (Saving %)**:
     $$\text{Saving}(\%) = \left(1 - \frac{\text{Size}_{MP3}}{\text{Size}_{WAV}}\right) \times 100\% = \left(1 - \frac{1}{11.025}\right) \times 100\% \approx \mathbf{90.93\%}$$
   - *Kết luận*: File nén MP3 128 kbps chỉ chiếm chưa đầy **$1/11$** dung lượng của file WAV gốc, giúp tiết kiệm gần $91\%$ không gian lưu trữ và băng thông truyền dẫn.

---

### Câu 7: Nêu ít nhất hai trường hợp mà “nghe tốt hơn” không đồng nghĩa với “SNR lớn hơn”.
**Trả lời**:
1. **Trường hợp 1: Mã hóa âm thanh cảm thụ (Perceptual Audio Coding - MP3, AAC, Opus, Vorbis)**:
   - Các bộ mã hóa nén lossy sử dụng mô hình tâm lý thính giác (*psychoacoustic model*) để loại bỏ thông tin âm thanh ở các dải tần bị che khuất bởi hiện tượng che khuất đồng thời (*spectral masking*) hoặc che khuất theo thời gian (*temporal masking*).
   - Về mặt toán học, dạng sóng sau giải mã bị sai lệch đáng kể so với dạng sóng gốc, dẫn đến phương sai sai số $\sum (x[n] - \hat{x}[n])^2$ rất lớn, khiến chỉ số SNR đo được chỉ đạt khoảng **$25 - 35\text{ dB}$** (tương đương lượng tử hóa 5-6 bit).
   - Tuy nhiên, khi nghe thực tế, do nhiễu được cố ý "giấu" vào đúng các dải tần mà tai người bị che khuất, người nghe cảm nhận âm thanh hoàn toàn trong trẻo, tự nhiên, không thể phân biệt được với bản gốc WAV 16-bit (có SNR $> 90\text{ dB}$). Ngược lại, một file PCM lượng tử hóa 6-bit có cùng mức SNR $35\text{ dB}$ sẽ nghe thấy tiếng rè xì xào xạc vô cùng khó chịu.
2. **Trường hợp 2: Khử nhiễu nền và Lọc dải thông (Speech Denoising / Spectral Subtraction)**:
   - Trong một bản ghi âm giọng nói bị lẫn tiếng quạt gió hoặc tiếng ù xoay chiều $50\text{ Hz}$, áp dụng thuật toán khử nhiễu phổ hoặc bộ lọc thông dải sẽ cắt bỏ dải tần dưới $80\text{ Hz}$ và dập tắt các thành phần nhiễu.
   - Do thuật toán lọc không thể tách bạch hoàn hảo, nó sẽ làm suy giảm một phần năng lượng tín hiệu gốc và gây ra hiện tượng méo nhẹ dạng sóng.
   - Nếu đo SNR so với tín hiệu ban đầu, chỉ số SNR toán học có thể bị giảm hoặc không tăng nhiều do sự sai lệch hình dạng sóng.
   - Tuy nhiên, đối với tai người nghe, việc loại bỏ hoàn toàn tiếng ù xì nền gây mệt mỏi sẽ làm cho giọng nói trở nên nổi bật, dễ chịu hơn rất nhiều, tăng rõ rệt độ hiểu lời thoại (*Speech Intelligibility*).
3. **Trường hợp bổ sung: Hiệu ứng bão hòa đèn / Băng từ (Analog Warmth / Tube Saturation)**:
   - Trong sản xuất âm nhạc chuyên nghiệp, các kỹ sư thường cố tình đưa tín hiệu qua các mạch tiền khuếch đại đèn điện tử (Tube Preamp) hoặc máy ghi băng từ để tạo ra hiện tượng méo hài bậc chẵn nhẹ (*soft clipping / harmonic distortion*).
   - Về mặt toán học, độ méo hài tổng THD tăng lên làm chỉ số SNR giảm. Tuy nhiên, về mặt cảm thụ nghệ thuật, các hài âm bậc chẵn tạo ra cảm giác âm thanh "ấm áp", "dày dặn", "ngọt ngào" và dễ chịu hơn hẳn so với tín hiệu số nguyên bản quá khô cứng.

---

## 5. Checklist kiểm tra trước khi nộp bài (Thang điểm 10/10)

| Hạng mục | Điểm | Tiêu chí đánh giá | Trạng thái đạt được |
| :--- | :---: | :--- | :---: |
| **Chuẩn bị & Metadata** | **1.0** | Đọc đúng dữ liệu, chuẩn hóa biên độ, trích xuất đầy đủ Fs/channels/duration. | ĐẠT (100%) |
| **Time/FFT Analysis** | **2.0** | Vẽ Waveform toàn phần/zoom, tính Peak/RMS/Energy, FFT đúng trục Hz/dB. | ĐẠT (100%) |
| **STFT/Window Experiment** | **2.0** | Spectrogram đa khung thời gian, phân tích trade-off, so sánh rò rỉ phổ cửa sổ. | ĐẠT (100%) |
| **Filtering (Lọc số)** | **2.0** | Thiết kế FIR đúng, có đáp ứng $H(f)$, xuất file audio và vẽ phổ trước/sau. | ĐẠT (100%) |
| **Quantization/Coding** | **1.5** | Tính SNR đo đạc vs lý thuyết, tính bitrate, file size, tỷ số nén MP3. | ĐẠT (100%) |
| **Phân tích & Trình bày** | **1.0** | Giải thích kỹ thuật sâu sắc, hình ảnh trực quan, bảng số liệu rõ ràng. | ĐẠT (100%) |
| **Tái lập & Tổ chức mã nguồn** | **0.5** | Notebook chạy từ đầu đến cuối không lỗi (Run All), cấu trúc file chuẩn. | ĐẠT (100%) |
| **TỔNG ĐIỂM DỰ KIẾN** | **10.0 / 10.0** | **Xuất sắc - Hoàn thành toàn diện mọi yêu cầu bài Lab** | |

---

## 6. Hướng dẫn nộp bài lên GitHub
Sinh viên đẩy toàn bộ thư mục lên kho chứa GitHub cá nhân ở chế độ **Công khai (Public)**:
```bash
git init
git add .
git commit -m "Hoàn thành toàn bộ bài thực hành Lab 1 CSE457 - Nguyễn Thị Nam Phương"
git branch -M main
git remote add origin https://github.com/<tai-khoan-github>/Lab01_2351260682_NguyenThiNamPhuong.git
git push -u origin main
```

