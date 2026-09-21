# -*- coding: utf-8 -*-
"""
Phase 4: Thiết kế bộ lọc số FIR & Lọc tín hiệu âm thanh (Khối F)
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

# Đọc tín hiệu âm thanh gốc
speech_data, sr_sp = sf.read("audio/speech_input.wav", dtype='float64')
speech_mono = (speech_data[:, 0] + speech_data[:, 1]) / 2.0
if np.max(np.abs(speech_mono)) > 1.0:
    speech_mono = speech_mono / np.max(np.abs(speech_mono))

music_data, sr_mu = sf.read("audio/music_input.wav", dtype='float64')
music_mono = (music_data[:, 0] + music_data[:, 1]) / 2.0
if np.max(np.abs(music_mono)) > 1.0:
    music_mono = music_mono / np.max(np.abs(music_mono))

sr = sr_mu  # Fs = 44,100 Hz

print("=" * 70)
print("KHỐI F: THIẾT KẾ BỘ LỌC SỐ FIR VÀ LỌC ÂM THANH")
print("=" * 70)

# 1. Thiết kế bộ lọc FIR Low-pass và High-pass
numtaps = 201
cutoff_lpf = 2000.0   # 2 kHz
cutoff_hpf = 2000.0   # 2 kHz

# Bộ lọc 1: FIR Low-pass
b_lpf = signal.firwin(numtaps=numtaps, cutoff=cutoff_lpf, fs=sr, window='hamming')

# Bộ lọc 2: FIR High-pass
b_hpf = signal.firwin(numtaps=numtaps, cutoff=cutoff_hpf, fs=sr, pass_zero=False, window='hamming')

# Tính độ trễ nhóm lý thuyết (Group delay)
group_delay_samples = (numtaps - 1) / 2
group_delay_ms = (group_delay_samples / sr) * 1000.0

print(f"Bậc bộ lọc (M): {numtaps - 1} | Số hệ số taps (L): {numtaps}")
print(f"Tần số cắt (Cutoff): {cutoff_lpf:,.0f} Hz | Cửa sổ: Hamming")
print(f"Độ trễ nhóm (Group Delay): {group_delay_samples:.1f} mẫu = {group_delay_ms:.4f} ms")

# Tính đáp ứng tần số H(f)
worN = 8192
w_lpf, H_lpf = signal.freqz(b_lpf, [1.0], worN=worN, fs=sr)
w_hpf, H_hpf = signal.freqz(b_hpf, [1.0], worN=worN, fs=sr)

H_lpf_db = 20 * np.log10(np.maximum(np.abs(H_lpf), 1e-6))
H_hpf_db = 20 * np.log10(np.maximum(np.abs(H_hpf), 1e-6))

# Vẽ đồ thị đáp ứng tần số (figures/filter_response.png)
fig, axes = plt.subplots(2, 1, figsize=(14, 8), constrained_layout=True)

# Magnitude Response
ax1 = axes[0]
ax1.plot(w_lpf, H_lpf_db, color='#1f77b4', linewidth=1.5, label=f'FIR Low-pass (Cutoff = {cutoff_lpf:.0f} Hz)')
ax1.plot(w_hpf, H_hpf_db, color='#d62728', linewidth=1.5, label=f'FIR High-pass (Cutoff = {cutoff_hpf:.0f} Hz)')
ax1.axvline(2000, color='gray', linestyle='--', alpha=0.7, label='Tần số cắt fc = 2000 Hz')
ax1.axhline(-6.0, color='black', linestyle=':', alpha=0.6, label='Ngưỡng suy hao tại fc (-6 dB)')
ax1.axhline(-53.0, color='green', linestyle=':', alpha=0.6, label='Độ suy hao dải chặn (Stopband ≈ -53 dB)')
ax1.set_title("1. Đáp ứng biên độ |H(f)| của bộ lọc FIR Low-pass & High-pass (201 taps, Hamming, Fs = 44.1 kHz)", fontsize=11, fontweight='bold')
ax1.set_xlabel("Tần số (Hz)")
ax1.set_ylabel("Biên độ (dB)")
ax1.set_xlim(0, 8000)
ax1.set_ylim(-90, 5)
ax1.legend(loc='lower left', framealpha=0.9)

# Phase & Group Delay Response
ax2 = axes[1]
phase_lpf = np.unwrap(np.angle(H_lpf))
ax2.plot(w_lpf, phase_lpf, color='#1f77b4', linewidth=1.2, label='Góc pha FIR Low-pass (Đường thẳng tuyến tính hoàn hảo)')
ax2.set_title(f"2. Đáp ứng pha (Phase Response) - Thể hiện tính chất Pha tuyến tính (Linear Phase, Group Delay = {group_delay_ms:.2f} ms)", fontsize=11, fontweight='bold')
ax2.set_xlabel("Tần số (Hz)")
ax2.set_ylabel("Pha (Radian)")
ax2.set_xlim(0, 8000)
ax2.legend(loc='lower left', framealpha=0.9)

output_resp = "figures/filter_response.png"
plt.savefig(output_resp, dpi=300)
plt.close()
print(f"-> Đã lưu biểu đồ đáp ứng tần số tại: {output_resp}")

# 2. Áp dụng bộ lọc lên tín hiệu và xuất file âm thanh
print("\nĐang áp dụng bộ lọc lên các tệp âm thanh...")
# Lọc tiếng nói bằng LPF
y_speech_lpf = signal.lfilter(b_lpf, [1.0], speech_mono)
y_speech_lpf = y_speech_lpf / np.max(np.abs(y_speech_lpf)) * 0.85  # Chuẩn hóa an toàn

# Lọc âm nhạc bằng LPF
y_music_lpf = signal.lfilter(b_lpf, [1.0], music_mono)
y_music_lpf = y_music_lpf / np.max(np.abs(y_music_lpf)) * 0.85

# Lọc âm nhạc bằng HPF
y_music_hpf = signal.lfilter(b_hpf, [1.0], music_mono)
y_music_hpf = y_music_hpf / np.max(np.abs(y_music_hpf)) * 0.85

# Xuất các file WAV đã lọc (chuyển sang stereo 2 kênh để nhất quán)
sf.write("audio/filtered_speech_lpf.wav", np.column_stack([y_speech_lpf, y_speech_lpf]), sr, subtype='PCM_16')
sf.write("audio/filtered_music_lpf.wav", np.column_stack([y_music_lpf, y_music_lpf]), sr, subtype='PCM_16')
sf.write("audio/filtered_music_hpf.wav", np.column_stack([y_music_hpf, y_music_hpf]), sr, subtype='PCM_16')

print("-> Đã xuất tệp âm thanh:")
print("   + audio/filtered_speech_lpf.wav")
print("   + audio/filtered_music_lpf.wav")
print("   + audio/filtered_music_hpf.wav")

# 3. So sánh phổ trước và sau khi lọc
# Lấy đoạn 37.8s - 38.6s của âm nhạc để so sánh phổ
s_idx, e_idx = int(37.8 * sr), int(38.6 * sr)
seg_orig = music_mono[s_idx:e_idx] * np.hamming(e_idx - s_idx)
seg_lpf = y_music_lpf[s_idx:e_idx] * np.hamming(e_idx - s_idx)
seg_hpf = y_music_hpf[s_idx:e_idx] * np.hamming(e_idx - s_idx)

NFFT_EFF = 16384
f_eff = np.fft.rfftfreq(NFFT_EFF, 1 / sr)

X_orig = 20 * np.log10(np.maximum(np.abs(np.fft.rfft(seg_orig, n=NFFT_EFF)) / np.max(np.abs(np.fft.rfft(seg_orig, n=NFFT_EFF))), 1e-6))
X_lpf = 20 * np.log10(np.maximum(np.abs(np.fft.rfft(seg_lpf, n=NFFT_EFF)) / np.max(np.abs(np.fft.rfft(seg_lpf, n=NFFT_EFF))), 1e-6))
X_hpf = 20 * np.log10(np.maximum(np.abs(np.fft.rfft(seg_hpf, n=NFFT_EFF)) / np.max(np.abs(np.fft.rfft(seg_hpf, n=NFFT_EFF))), 1e-6))

fig, axes = plt.subplots(2, 1, figsize=(14, 8), constrained_layout=True)

# So sánh Low-pass
axes[0].plot(f_eff, X_orig, color='gray', alpha=0.6, linewidth=1.0, label='Phổ tín hiệu gốc (Trước khi lọc)')
axes[0].plot(f_eff, X_lpf, color='#1f77b4', linewidth=1.2, label='Phổ sau khi lọc FIR Low-pass (fc = 2 kHz)')
axes[0].axvline(2000, color='red', linestyle='--', label='Tần số cắt fc = 2000 Hz')
axes[0].set_title("1. So sánh phổ biên độ trước và sau khi lọc Low-pass 2 kHz (Đoạn âm nhạc 37.8s - 38.6s)", fontsize=11, fontweight='bold')
axes[0].set_xlabel("Tần số (Hz)")
axes[0].set_ylabel("Biên độ tương đối (dB)")
axes[0].set_xlim(0, 6000)
axes[0].set_ylim(-80, 5)
axes[0].legend(loc='upper right', framealpha=0.9)

# So sánh High-pass
axes[1].plot(f_eff, X_orig, color='gray', alpha=0.6, linewidth=1.0, label='Phổ tín hiệu gốc (Trước khi lọc)')
axes[1].plot(f_eff, X_hpf, color='#d62728', linewidth=1.2, label='Phổ sau khi lọc FIR High-pass (fc = 2 kHz)')
axes[1].axvline(2000, color='red', linestyle='--', label='Tần số cắt fc = 2000 Hz')
axes[1].set_title("2. So sánh phổ biên độ trước và sau khi lọc High-pass 2 kHz (Đoạn âm nhạc 37.8s - 38.6s)", fontsize=11, fontweight='bold')
axes[1].set_xlabel("Tần số (Hz)")
axes[1].set_ylabel("Biên độ tương đối (dB)")
axes[1].set_xlim(0, 6000)
axes[1].set_ylim(-80, 5)
axes[1].legend(loc='upper right', framealpha=0.9)

output_eff = "figures/filter_effect.png"
plt.savefig(output_eff, dpi=300)
plt.close()
print(f"-> Đã lưu biểu đồ hiệu ứng lọc tại: {output_eff}")
