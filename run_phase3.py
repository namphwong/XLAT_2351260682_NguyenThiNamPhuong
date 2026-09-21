# -*- coding: utf-8 -*-
"""
Phase 3: Phân tích miền tần số & Miền thời gian - tần số (Khối C, D, E)
Sinh viên: Nguyễn Thị Nam Phương - MSSV: 2351260682
Học phần: CSE457 - Xử lý âm thanh và tiếng nói
"""

import os
import soundfile as sf
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
os.makedirs("audio", exist_ok=True)

# Đọc dữ liệu âm nhạc và tiếng nói đã chuẩn hóa
music_data, sr = sf.read("audio/music_input.wav", dtype='float64')
music_mono = (music_data[:, 0] + music_data[:, 1]) / 2.0
if np.max(np.abs(music_mono)) > 1.0:
    music_mono = music_mono / np.max(np.abs(music_mono))

speech_data, sr_sp = sf.read("audio/speech_input.wav", dtype='float64')
speech_mono = (speech_data[:, 0] + speech_data[:, 1]) / 2.0
if np.max(np.abs(speech_mono)) > 1.0:
    speech_mono = speech_mono / np.max(np.abs(speech_mono))

print("=" * 70)
print("KHỐI C: PHÂN TÍCH MIỀN TẦN SỐ BẰNG FFT")
print("=" * 70)

# Chọn đoạn ổn định 0.8s của âm nhạc: 37.8s đến 38.6s (cao trào hòa tấu)
s_idx = int(37.8 * sr)
e_idx = int(38.6 * sr)
seg = music_mono[s_idx:e_idx]
N_samples = len(seg)

# Áp dụng cửa sổ Hamming
w_hamm = np.hamming(N_samples)
seg_hamm = seg * w_hamm

# Thử nghiệm 2 giá trị NFFT: NFFT1 = 2048 và NFFT2 = 65536
NFFT1 = 2048
NFFT2 = 65536

df1 = sr / NFFT1
df2 = sr / NFFT2

print(f"Số mẫu phân đoạn (N): {N_samples} mẫu ({N_samples/sr:.4f} s)")
print(f"Cấu hình NFFT 1: {NFFT1:,} -> Bước tần số Δf1 = {df1:.4f} Hz")
print(f"Cấu hình NFFT 2: {NFFT2:,} -> Bước tần số Δf2 = {df2:.4f} Hz")

# Tính FFT
X1 = np.fft.rfft(seg_hamm, n=NFFT1)
f1 = np.fft.rfftfreq(NFFT1, 1 / sr)
mag1_db = 20 * np.log10(np.maximum(np.abs(X1) / np.max(np.abs(X1)), 1e-12))

X2 = np.fft.rfft(seg_hamm, n=NFFT2)
f2 = np.fft.rfftfreq(NFFT2, 1 / sr)
mag2_db = 20 * np.log10(np.maximum(np.abs(X2) / np.max(np.abs(X2)), 1e-12))

# Tìm các đỉnh phổ nổi bật trên NFFT2 (trong dải 0 - 3000 Hz)
mask_search = (f2 >= 100) & (f2 <= 3000)
peaks_idx, props = signal.find_peaks(mag2_db[mask_search], height=-25, distance=int(30 / df2), prominence=4)
# Chuyển về index thực trên f2
search_indices = np.where(mask_search)[0]
actual_peak_indices = search_indices[peaks_idx]

# Lấy 5 đỉnh cao nhất để đánh dấu
sorted_peaks = sorted(actual_peak_indices, key=lambda idx: mag2_db[idx], reverse=True)[:5]
sorted_peaks = sorted(sorted_peaks, key=lambda idx: f2[idx])

print("\nCác đỉnh phổ nổi bật tìm được trên đoạn âm nhạc (37.8s - 38.6s):")
for i, idx in enumerate(sorted_peaks[:5], 1):
    print(f"  - Đỉnh {i}: Tần số f = {f2[idx]:.2f} Hz | Biên độ tương đối = {mag2_db[idx]:.2f} dB")

# Vẽ đồ thị FFT (figures/fft.png)
fig, axes = plt.subplots(2, 1, figsize=(14, 8), constrained_layout=True)

# Panel 1: Toàn cảnh phổ 0 - 6000 Hz
ax1 = axes[0]
ax1.plot(f1, mag1_db, color='#ff7f0e', alpha=0.75, linewidth=0.9, label=f'NFFT = {NFFT1} (Δf = {df1:.2f} Hz)')
ax1.plot(f2, mag2_db, color='#1f77b4', alpha=0.85, linewidth=0.8, label=f'NFFT = {NFFT2} (Δf = {df2:.3f} Hz)')
for idx in sorted_peaks:
    ax1.plot(f2[idx], mag2_db[idx], 'ro', markersize=6)
    ax1.annotate(f"{f2[idx]:.1f} Hz\n({mag2_db[idx]:.1f} dB)",
                 xy=(f2[idx], mag2_db[idx]),
                 xytext=(f2[idx] + 40, mag2_db[idx] + 3),
                 fontsize=8, fontweight='bold',
                 arrowprops=dict(facecolor='red', arrowstyle='->', lw=0.8))

ax1.set_title(f"1. Phổ biên độ FFT đoạn âm nhạc (37.8s - 38.6s, Hamming) - Dải tần 0 đến 6000 Hz", fontsize=11, fontweight='bold')
ax1.set_xlabel("Tần số (Hz)")
ax1.set_ylabel("Biên độ tương đối (dB)")
ax1.set_xlim(0, 6000)
ax1.set_ylim(-70, 5)
ax1.legend(loc='upper right', framealpha=0.9)

# Panel 2: Zoom cận cảnh dải tần số thấp 200 - 1000 Hz để thấy rõ ảnh hưởng của NFFT
ax2 = axes[1]
ax2.plot(f1, mag1_db, 'o-', color='#ff7f0e', markersize=4, linewidth=1.0, label=f'NFFT = {NFFT1} (Điểm phổ thưa, Δf = {df1:.2f} Hz)')
ax2.plot(f2, mag2_db, color='#1f77b4', linewidth=1.2, label=f'NFFT = {NFFT2} (Nội suy phổ mịn màng, Δf = {df2:.3f} Hz)')
for idx in sorted_peaks:
    if 200 <= f2[idx] <= 1000:
        ax2.plot(f2[idx], mag2_db[idx], 'ro', markersize=7)
        ax2.annotate(f"{f2[idx]:.1f} Hz",
                     xy=(f2[idx], mag2_db[idx]),
                     xytext=(f2[idx] + 15, mag2_db[idx] + 2),
                     fontsize=9, fontweight='bold', color='darkred',
                     arrowprops=dict(facecolor='darkred', arrowstyle='->', lw=1))

ax2.set_title("2. Zoom cận cảnh dải tần 200 - 1000 Hz: So sánh bước tần số (Bin Spacing) và độ phân giải", fontsize=11, fontweight='bold')
ax2.set_xlabel("Tần số (Hz)")
ax2.set_ylabel("Biên độ tương đối (dB)")
ax2.set_xlim(200, 1000)
ax2.set_ylim(-50, 5)
ax2.legend(loc='upper right', framealpha=0.9)

output_fft = "figures/fft.png"
plt.savefig(output_fft, dpi=300)
plt.close()
print(f"-> Đã xuất đồ thị FFT tại: {output_fft}")

print("\n" + "=" * 70)
print("KHỐI D: STFT VÀ SPECTROGRAM (TIME-FREQUENCY RESOLUTION)")
print("=" * 70)

# Đoạn âm nhạc từ 35.0s đến 45.0s (10 giây) bao gồm đoạn bình ổn và cao trào
t_start = 35.0
t_end = 45.0
x_stft = music_mono[int(t_start * sr):int(t_end * sr)]

# 3 độ dài khung thời gian: 10 ms, 25 ms, 50 ms
frame_lens_ms = [10, 25, 50]
hop_ms = 10  # Hop size cố định 10 ms để so sánh đồng nhất
hop_samples = int(round(0.010 * sr))

fig, axes = plt.subplots(3, 1, figsize=(14, 10), constrained_layout=True, sharex=True)

for i, f_ms in enumerate(frame_lens_ms):
    nperseg = int(round((f_ms / 1000.0) * sr))
    noverlap = nperseg - hop_samples if nperseg > hop_samples else 0
    nfft = 4096
    
    f_stft, t_rel, Sxx = signal.spectrogram(
        x_stft, fs=sr, window='hamming',
        nperseg=nperseg, noverlap=noverlap, nfft=nfft,
        mode='magnitude'
    )
    
    # Chuẩn hóa về dB với dynamic range [-80, 0] dB
    S_dB = 20 * np.log10(np.maximum(Sxx / np.max(Sxx), 1e-8))
    
    t_abs = t_rel + t_start
    ax = axes[i]
    im = ax.pcolormesh(t_abs, f_stft, S_dB, shading='gouraud', cmap='viridis', vmin=-80, vmax=0)
    ax.set_ylim(0, 8000)
    ax.set_ylabel("Tần số (Hz)", fontsize=10)
    
    delta_t_ms = f_ms
    delta_f_hz = sr / nperseg
    ax.set_title(f"Spectrogram Frame Length = {f_ms} ms ({nperseg} mẫu, Δf_window ≈ {delta_f_hz:.1f} Hz, Hop = 10 ms) "
                 f"| {'Độ phân giải thời gian cao, tần số thô' if f_ms == 10 else ('Cân bằng chuẩn (Standard)' if f_ms == 25 else 'Độ phân giải tần số sắc nét, thời gian bị nhòe')}",
                 fontsize=10, fontweight='bold')

axes[-1].set_xlabel("Thời gian (giây)", fontsize=10)
cbar = fig.colorbar(im, ax=axes, orientation='vertical', fraction=0.02, pad=0.02)
cbar.set_label("Biên độ phổ chuẩn hóa (dB)", fontsize=10)

output_spec = "figures/spectrogram.png"
plt.savefig(output_spec, dpi=300)
plt.close()
print(f"-> Đã xuất đồ thị Spectrogram tại: {output_spec}")

print("\n" + "=" * 70)
print("KHỐI E: THÍ NGHIỆM CỬA SỔ (WINDOWING COMPARISON)")
print("=" * 70)

# Cắt 1 khung tín hiệu 25 ms (1102 mẫu) từ đoạn ổn định
L_win = int(round(0.025 * sr))
frame_signal = music_mono[int(38.0 * sr) : int(38.0 * sr) + L_win]

# Hai loại cửa sổ: Rectangular và Hamming
w_rect = np.ones(L_win)
w_hamm = np.hamming(L_win)

# Zero-padding lên NFFT = 16384 để quan sát chính xác cấu trúc búp sóng
NFFT_WIN = 16384
f_win = np.fft.rfftfreq(NFFT_WIN, 1 / sr)

# 1. Đáp ứng tần số của chính cửa sổ (Window Frequency Response)
W_rect = np.fft.rfft(w_rect / np.sum(w_rect), n=NFFT_WIN)
W_hamm = np.fft.rfft(w_hamm / np.sum(w_hamm), n=NFFT_WIN)

W_rect_db = 20 * np.log10(np.maximum(np.abs(W_rect), 1e-8))
W_hamm_db = 20 * np.log10(np.maximum(np.abs(W_hamm), 1e-8))

# 2. Phổ của khung tín hiệu thực khi nhân 2 loại cửa sổ
X_rect = np.fft.rfft(frame_signal * w_rect, n=NFFT_WIN)
X_hamm = np.fft.rfft(frame_signal * w_hamm, n=NFFT_WIN)

X_rect_db = 20 * np.log10(np.maximum(np.abs(X_rect) / np.max(np.abs(X_rect)), 1e-8))
X_hamm_db = 20 * np.log10(np.maximum(np.abs(X_hamm) / np.max(np.abs(X_hamm)), 1e-8))

fig, axes = plt.subplots(2, 1, figsize=(14, 8), constrained_layout=True)

# Panel 1: Đáp ứng tần số lý thuyết của 2 cửa sổ
ax1 = axes[0]
ax1.plot(f_win, W_rect_db, color='#d62728', linewidth=1.2, label='Cửa sổ Chữ nhật (Rectangular) - Búp chính hẹp, Búp phụ cao (-13 dB)')
ax1.plot(f_win, W_hamm_db, color='#1f77b4', linewidth=1.4, label='Cửa sổ Hamming - Búp chính rộng hơn, Búp phụ suy hao mạnh (-43 dB)')
ax1.set_title("1. Đáp ứng phổ lý thuyết của Cửa sổ Rectangular vs Hamming (L = 25 ms, NFFT = 16,384)", fontsize=11, fontweight='bold')
ax1.set_xlabel("Tần số (Hz)")
ax1.set_ylabel("Biên độ tương đối (dB)")
ax1.set_xlim(0, 1500)
ax1.set_ylim(-90, 5)
ax1.axhline(-13.3, color='#d62728', linestyle=':', label='Đỉnh búp phụ Rectangular: -13.3 dB')
ax1.axhline(-42.7, color='#1f77b4', linestyle=':', label='Đỉnh búp phụ Hamming: -42.7 dB')
ax1.legend(loc='upper right', framealpha=0.9)

# Panel 2: Phổ tín hiệu âm thanh thực tế khi áp dụng 2 cửa sổ
ax2 = axes[1]
ax2.plot(f_win, X_rect_db, color='#d62728', alpha=0.75, linewidth=1.0, label='Tín hiệu + Rectangular (Rò rỉ phổ mạnh, nền nhiễu cao)')
ax2.plot(f_win, X_hamm_db, color='#1f77b4', alpha=0.85, linewidth=1.2, label='Tín hiệu + Hamming (Bảo toàn hài âm, nền phổ sạch - giảm leakage)')
ax2.set_title("2. Phổ thực tế trên cùng một khung âm thanh (25 ms): Minh họa hiện tượng rò rỉ phổ (Spectral Leakage)", fontsize=11, fontweight='bold')
ax2.set_xlabel("Tần số (Hz)")
ax2.set_ylabel("Biên độ tương đối (dB)")
ax2.set_xlim(0, 3000)
ax2.set_ylim(-80, 5)
ax2.legend(loc='upper right', framealpha=0.9)

output_win = "figures/window_comparison.png"
plt.savefig(output_win, dpi=300)
plt.close()
print(f"-> Đã xuất đồ thị Cửa sổ tại: {output_win}")
