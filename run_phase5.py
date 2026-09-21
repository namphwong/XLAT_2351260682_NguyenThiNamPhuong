# -*- coding: utf-8 -*-
"""
Phase 5: Lượng tử hóa, Resampling & Mã hóa nén (Khối G)
Sinh viên: Nguyễn Thị Nam Phương - MSSV: 2351260682 - Lớp: 65TTNT
Học phần: CSE457 - Xử lý âm thanh và tiếng nói
"""

import os
import soundfile as sf
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
os.makedirs("audio", exist_ok=True)

# Đọc tệp tiếng nói và âm nhạc gốc
speech_data, sr = sf.read("audio/speech_input.wav", dtype='float64')
speech_mono = (speech_data[:, 0] + speech_data[:, 1]) / 2.0
if np.max(np.abs(speech_mono)) > 1.0:
    speech_mono = speech_mono / np.max(np.abs(speech_mono))

music_data, _ = sf.read("audio/music_input.wav", dtype='float64')
music_mono = (music_data[:, 0] + music_data[:, 1]) / 2.0
if np.max(np.abs(music_mono)) > 1.0:
    music_mono = music_mono / np.max(np.abs(music_mono))

print("=" * 75)
print("KHỐI G - PHẦN 1: LƯỢNG TỬ HÓA VÀ ĐO ĐẠC SNR")
print("=" * 75)

def quantize(x, B):
    """Lượng tử hóa đều đối xứng B-bit trong khoảng [-1, 1]"""
    qmax = 2**(B - 1) - 1
    return np.round(np.clip(x, -1.0, 1.0) * qmax) / qmax

def snr_db(x, xq):
    """Tính tỷ số tín hiệu trên nhiễu lượng tử (SNR đo được bằng dB)"""
    e = xq - x
    p_signal = np.sum(x**2)
    p_noise = np.sum(e**2)
    if p_noise == 0:
        return np.inf
    return 10.0 * np.log10(p_signal / p_noise)

bits_list = [4, 6, 8, 12, 16]
rms_speech = np.sqrt(np.mean(speech_mono**2))
rms_music = np.sqrt(np.mean(music_mono**2))

snr_speech_meas = []
snr_speech_theo = []
snr_music_meas = []
snr_music_theo = []

print(f"Mức RMS tín hiệu tiếng nói: {rms_speech:.5f} ({20*np.log10(rms_speech):.2f} dBFS)")
print(f"Mức RMS tín hiệu âm nhạc:   {rms_music:.5f} ({20*np.log10(rms_music):.2f} dBFS)\n")
print(f"{'Bit depth (B)':<15} | {'Mức L':<8} | {'SNR Speech Đo (dB)':<20} | {'SNR Speech LT (dB)':<20} | {'SNR Music Đo (dB)':<20}")
print("-" * 92)

for B in bits_list:
    L = 2**B
    # Lượng tử hóa tiếng nói
    xq_sp = quantize(speech_mono, B)
    snr_sp_m = snr_db(speech_mono, xq_sp)
    # Công thức lý thuyết Rabiner-Schafer: SNR = 6B + 4.77 - 20*log10(Xmax / sigma_x)
    snr_sp_t = 6.02 * B + 4.77 - 20.0 * np.log10(1.0 / rms_speech)
    
    # Lượng tử hóa âm nhạc
    xq_mu = quantize(music_mono, B)
    snr_mu_m = snr_db(music_mono, xq_mu)
    snr_mu_t = 6.02 * B + 4.77 - 20.0 * np.log10(1.0 / rms_music)
    
    snr_speech_meas.append(snr_sp_m)
    snr_speech_theo.append(snr_sp_t)
    snr_music_meas.append(snr_mu_m)
    snr_music_theo.append(snr_mu_t)
    
    print(f"{B:<15} | {L:<8} | {snr_sp_m:<20.2f} | {snr_sp_t:<20.2f} | {snr_mu_m:<20.2f}")

    # Xuất file âm thanh lượng tử hóa yêu cầu cho bài nộp (4-bit, 8-bit, 16-bit)
    if B in [4, 8, 16]:
        # Lưu file WAV tiếng nói lượng tử hóa
        out_sp_path = f"audio/quantized_speech_{B}bit.wav"
        sf.write(out_sp_path, np.column_stack([xq_sp, xq_sp]), sr, subtype='PCM_16')
        print(f"   -> Đã lưu: {out_sp_path}")

# Vẽ đồ thị SNR theo số bit (figures/quantization_snr.png)
fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)

ax.plot(bits_list, snr_speech_meas, 'o-', color='#1f77b4', linewidth=2, markersize=8, label='Tiếng nói (Speech) - Đo đạc thực tế')
ax.plot(bits_list, snr_speech_theo, '--', color='#1f77b4', alpha=0.7, linewidth=1.5, label='Tiếng nói (Speech) - Lý thuyết (6B + 4.77 - 20log(1/σ))')
ax.plot(bits_list, snr_music_meas, 's-', color='#d62728', linewidth=2, markersize=8, label='Âm nhạc (Music) - Đo đạc thực tế')
ax.plot(bits_list, snr_music_theo, '--', color='#d62728', alpha=0.7, linewidth=1.5, label='Âm nhạc (Music) - Lý thuyết')

for i, B in enumerate(bits_list):
    ax.annotate(f"{snr_speech_meas[i]:.1f} dB", (B, snr_speech_meas[i]),
                textcoords="offset points", xytext=(-10, 10), fontsize=9, fontweight='bold', color='#1f77b4')
    ax.annotate(f"{snr_music_meas[i]:.1f} dB", (B, snr_music_meas[i]),
                textcoords="offset points", xytext=(-10, -15), fontsize=9, fontweight='bold', color='#d62728')

ax.set_title("1. Tỷ số tín hiệu trên nhiễu lượng tử SNR theo độ phân giải số bit (4, 6, 8, 12, 16 bit)", fontsize=11, fontweight='bold')
ax.set_xlabel("Độ phân giải lượng tử B (bit/mẫu)", fontsize=10)
ax.set_ylabel("SNR đo được (dB)", fontsize=10)
ax.set_xticks(bits_list)
ax.set_ylim(0, 110)
ax.legend(loc='upper left', framealpha=0.9, fontsize=9)
ax.grid(True, linestyle='--', alpha=0.6)

output_snr = "figures/quantization_snr.png"
plt.savefig(output_snr, dpi=300)
plt.close()
print(f"\n-> Đã lưu biểu đồ SNR lượng tử hóa tại: {output_snr}")

print("\n" + "=" * 75)
print("KHỐI G - PHẦN 2: LẤY MẪU LẠI (RESAMPLING VỀ 16 KHZ VÀ 8 KHZ)")
print("=" * 75)

# Lấy mẫu lại tiếng nói về 16 kHz và 8 kHz (sử dụng scipy.signal.resample_poly có lọc anti-aliasing)
sr_16k = 16000
sr_8k = 8000

# resample_poly: up/down sao cho up/down = sr_target / sr_orig
# 44100 -> 16000: tỉ số 160 / 441
# 44100 -> 8000: tỉ số 80 / 441
y_sp_16k = signal.resample_poly(speech_mono, 160, 441)
y_sp_8k = signal.resample_poly(speech_mono, 80, 441)

# Lưu các file âm thanh resample
sf.write("audio/resampled_speech_16k.wav", np.column_stack([y_sp_16k, y_sp_16k]), sr_16k, subtype='PCM_16')
sf.write("audio/resampled_speech_8k.wav", np.column_stack([y_sp_8k, y_sp_8k]), sr_8k, subtype='PCM_16')
print("-> Đã xuất tệp lấy mẫu lại:")
print("   + audio/resampled_speech_16k.wav (Fs = 16,000 Hz, Nyquist = 8 kHz)")
print("   + audio/resampled_speech_8k.wav  (Fs = 8,000 Hz, Nyquist = 4 kHz)")

# So sánh phổ trên cùng 1 đoạn nguyên âm hữu thanh (3.4s - 4.2s = 0.8s)
# Trích xuất đoạn tương ứng trên từng tín hiệu
seg_orig = speech_mono[int(3.4 * sr) : int(4.2 * sr)] * np.hamming(int(0.8 * sr))
seg_16k = y_sp_16k[int(3.4 * sr_16k) : int(4.2 * sr_16k)] * np.hamming(int(0.8 * sr_16k))
seg_8k = y_sp_8k[int(3.4 * sr_8k) : int(4.2 * sr_8k)] * np.hamming(int(0.8 * sr_8k))

NFFT_RES = 16384
f_orig = np.fft.rfftfreq(NFFT_RES, 1 / sr)
f_16k = np.fft.rfftfreq(NFFT_RES, 1 / sr_16k)
f_8k = np.fft.rfftfreq(NFFT_RES, 1 / sr_8k)

X_sp_orig = 20 * np.log10(np.maximum(np.abs(np.fft.rfft(seg_orig, n=NFFT_RES)) / np.max(np.abs(np.fft.rfft(seg_orig, n=NFFT_RES))), 1e-6))
X_sp_16k = 20 * np.log10(np.maximum(np.abs(np.fft.rfft(seg_16k, n=NFFT_RES)) / np.max(np.abs(np.fft.rfft(seg_16k, n=NFFT_RES))), 1e-6))
X_sp_8k = 20 * np.log10(np.maximum(np.abs(np.fft.rfft(seg_8k, n=NFFT_RES)) / np.max(np.abs(np.fft.rfft(seg_8k, n=NFFT_RES))), 1e-6))

fig, axes = plt.subplots(3, 1, figsize=(14, 9), constrained_layout=True, sharex=True)

axes[0].plot(f_orig, X_sp_orig, color='#1f77b4', linewidth=1.2, label='Gốc: Fs = 44.1 kHz (Nyquist = 22.05 kHz)')
axes[0].axvline(22050, color='blue', linestyle='--', alpha=0.7)
axes[0].set_title("1. Phổ tín hiệu tiếng nói gốc (Fs = 44,100 Hz, dải tần đầy đủ)", fontsize=10, fontweight='bold')
axes[0].set_ylabel("Biên độ (dB)")
axes[0].set_ylim(-70, 5)
axes[0].legend(loc='upper right')

axes[1].plot(f_16k, X_sp_16k, color='#2ca02c', linewidth=1.2, label='Resample 16 kHz (Nyquist = 8 kHz - Chuẩn thoại băng rộng HD Voice)')
axes[1].axvline(8000, color='green', linestyle='--', linewidth=1.5, label='Giới hạn Nyquist 8 kHz')
axes[1].set_title("2. Phổ sau khi lấy mẫu lại về 16 kHz (Cắt bỏ toàn bộ dải tần > 8 kHz chống Aliasing)", fontsize=10, fontweight='bold')
axes[1].set_ylabel("Biên độ (dB)")
axes[1].set_ylim(-70, 5)
axes[1].legend(loc='upper right')

axes[2].plot(f_8k, X_sp_8k, color='#d62728', linewidth=1.2, label='Resample 8 kHz (Nyquist = 4 kHz - Chuẩn thoại truyền thống PSTN)')
axes[2].axvline(4000, color='red', linestyle='--', linewidth=1.5, label='Giới hạn Nyquist 4 kHz')
axes[2].set_title("3. Phổ sau khi lấy mẫu lại về 8 kHz (Cắt bỏ toàn bộ dải tần > 4 kHz)", fontsize=10, fontweight='bold')
axes[2].set_xlabel("Tần số (Hz)")
axes[2].set_ylabel("Biên độ (dB)")
axes[2].set_xlim(0, 15000)
axes[2].set_ylim(-70, 5)
axes[2].legend(loc='upper right')

output_res = "figures/resampling_comparison.png"
plt.savefig(output_res, dpi=300)
plt.close()
print(f"-> Đã lưu biểu đồ so sánh phổ Resampling tại: {output_res}")

print("\n" + "=" * 75)
print("KHỐI G - PHẦN 3: TỐC ĐỘ BIT, KÍCH THƯỚC VÀ MỨC NÉN (PCM VS MP3)")
print("=" * 75)

# Bảng so sánh dung lượng thực tế giữa WAV PCM 16-bit và MP3
# Công thức lý thuyết:
# R_PCM = Fs * B * C [bit/s]
# Size_theo = R_PCM * Duration / 8 [bytes]
# Compression Ratio = R_PCM / R_MP3 = Size_WAV / Size_MP3
# Saving(%) = (1 - Size_MP3 / Size_WAV) * 100%

files_comp = [
    {
        "name": "Tiếng nói (Speech)",
        "wav": "audio/speech_input.wav",
        "mp3": "audio/speech_input.mp3",
        "bitrate_mp3_kbps": 128
    },
    {
        "name": "Âm nhạc (Music)",
        "wav": "audio/music_input.wav",
        "mp3": "audio/music_input.mp3",
        "bitrate_mp3_kbps": 256
    }
]

print(f"{'Tên tệp':<20} | {'Thời lượng':<10} | {'Bitrate PCM':<15} | {'Bitrate MP3':<15} | {'Size WAV (MB)':<14} | {'Size MP3 (MB)':<14} | {'Tỷ số nén (CR)':<15} | {'Tiết kiệm (%)':<15}")
print("-" * 135)

comp_results = []

for item in files_comp:
    info = sf.info(item["wav"])
    duration = info.duration
    fs = info.samplerate
    channels = info.channels
    b = 16
    
    r_pcm = fs * b * channels  # bit/s
    size_pcm_theo = r_pcm * duration / 8.0  # bytes
    size_wav_real = os.path.getsize(item["wav"])
    size_mp3_real = os.path.getsize(item["mp3"])
    
    cr_real = size_wav_real / size_mp3_real
    saving_pct = (1.0 - size_mp3_real / size_wav_real) * 100.0
    
    res = {
        "name": item["name"],
        "duration": duration,
        "r_pcm_kbps": r_pcm / 1000.0,
        "r_mp3_kbps": item["bitrate_mp3_kbps"],
        "size_wav_mb": size_wav_real / (1024 * 1024),
        "size_mp3_mb": size_mp3_real / (1024 * 1024),
        "cr": cr_real,
        "saving": saving_pct
    }
    comp_results.append(res)
    
    print(f"{res['name']:<20} | {res['duration']:<10.2f} | {res['r_pcm_kbps']:<15.1f} | {res['r_mp3_kbps']:<15.1f} | {res['size_wav_mb']:<14.3f} | {res['size_mp3_mb']:<14.3f} | {res['cr']:<15.2f}: 1 | {res['saving']:<15.2f}%")

print("\nĐã hoàn thành toàn bộ tính toán Khối G!")
