# -*- coding: utf-8 -*-
"""
Phase 2: Xử lý nền tảng và Miền thời gian (Khối A & Khối B)
Sinh viên: Nguyễn Thị Nam Phương - MSSV: 2351260682
Học phần: CSE457 - Xử lý âm thanh và tiếng nói
"""

import os
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
os.makedirs("audio", exist_ok=True)

audio_files = {
    "speech": "audio/speech_input.wav",
    "music": "audio/music_input.wav"
}

results = {}

print("=" * 70)
print("KHỐI A: ĐỌC VÀ KIỂM TRA METADATA TỆP ÂM THANH")
print("=" * 70)

for key, path in audio_files.items():
    file_size = os.path.getsize(path)
    info = sf.info(path)
    data, sr = sf.read(path, dtype='float64')
    
    # Kênh trái, phải, mono
    if data.ndim > 1 and data.shape[1] == 2:
        left = data[:, 0]
        right = data[:, 1]
        mono = (left + right) / 2.0
    else:
        left = data
        right = data
        mono = data
        
    # Chuẩn hóa về [-1, 1] nếu vượt quá
    max_val = np.max(np.abs(mono))
    if max_val > 1.0:
        mono = mono / max_val
        left = left / np.max(np.abs(left))
        right = right / np.max(np.abs(right))
        
    # Tính toán các đại lượng miền thời gian
    peak = np.max(np.abs(mono))
    rms = np.sqrt(np.mean(mono**2))
    energy = np.sum(mono**2)
    clipping_samples = np.sum(np.abs(mono) >= 0.999)
    
    # RMS từng kênh
    rms_l = np.sqrt(np.mean(left**2))
    rms_r = np.sqrt(np.mean(right**2))
    
    results[key] = {
        "path": path,
        "size_bytes": file_size,
        "size_mb": file_size / (1024 * 1024),
        "sr": sr,
        "channels": info.channels,
        "duration": info.duration,
        "subtype": info.subtype,
        "data": mono,
        "left": left,
        "right": right,
        "peak": peak,
        "peak_dbfs": 20 * np.log10(peak) if peak > 0 else -np.inf,
        "rms": rms,
        "rms_dbfs": 20 * np.log10(rms) if rms > 0 else -np.inf,
        "rms_l": rms_l,
        "rms_l_dbfs": 20 * np.log10(rms_l) if rms_l > 0 else -np.inf,
        "rms_r": rms_r,
        "rms_r_dbfs": 20 * np.log10(rms_r) if rms_r > 0 else -np.inf,
        "energy": energy,
        "clipping_samples": clipping_samples
    }
    
    print(f"\n[+] Tệp: {path} ({'Tiếng nói (Speech)' if key == 'speech' else 'Âm nhạc (Music)'})")
    print(f"  - Dung lượng file: {file_size:,} bytes ({results[key]['size_mb']:.3f} MB)")
    print(f"  - Tần số lấy mẫu (Fs): {sr:,} Hz")
    print(f"  - Số kênh: {info.channels} (Stereo)")
    print(f"  - Thời lượng: {info.duration:.3f} giây ({len(mono):,} mẫu)")
    print(f"  - Độ rộng mẫu / Định dạng: {info.subtype}")
    print(f"  - Peak: {peak:.5f} ({results[key]['peak_dbfs']:.2f} dBFS)")
    print(f"  - RMS Kênh Trái (Left):  {rms_l:.5f} ({results[key]['rms_l_dbfs']:.2f} dBFS)")
    print(f"  - RMS Kênh Phải (Right): {rms_r:.5f} ({results[key]['rms_r_dbfs']:.2f} dBFS)")
    print(f"  - RMS Mono:              {rms:.5f} ({results[key]['rms_dbfs']:.2f} dBFS)")
    print(f"  - Năng lượng tổng (E):   {energy:,.2f}")
    print(f"  - Số mẫu clipping (>= 0.999): {clipping_samples} ({clipping_samples/len(mono)*100:.4f}%)")

print("\n" + "=" * 70)
print("KHỐI B: PHÂN TÍCH MIỀN THỜI GIAN VÀ SO SÁNH 2 PHÂN ĐOẠN ĐỐI LẬP")
print("=" * 70)

# Đối với Tiếng nói:
# Đoạn 1: Âm hữu thanh / Nguyên âm (Voiced sound) từ 3.4s đến 4.2s (dài 0.8s)
# Đoạn 2: Âm vô thanh / Chuyển tiếp (Unvoiced / Transition) từ 2.5s đến 3.3s (dài 0.8s)
sr_sp = results["speech"]["sr"]
x_sp = results["speech"]["data"]

seg1_sp = x_sp[int(3.4 * sr_sp) : int(4.2 * sr_sp)]
seg2_sp = x_sp[int(2.5 * sr_sp) : int(3.3 * sr_sp)]

rms_seg1_sp = np.sqrt(np.mean(seg1_sp**2))
rms_seg2_sp = np.sqrt(np.mean(seg2_sp**2))
peak_seg1_sp = np.max(np.abs(seg1_sp))
peak_seg2_sp = np.max(np.abs(seg2_sp))
e_seg1_sp = np.sum(seg1_sp**2)
e_seg2_sp = np.sum(seg2_sp**2)

print("\n[1. Phân tích Tiếng nói (Speech)]")
print(f"  * Đoạn 1 (3.4s - 4.2s, Âm hữu thanh / Voiced):      Peak = {peak_seg1_sp:.5f} ({20*np.log10(peak_seg1_sp):.2f} dBFS), RMS = {rms_seg1_sp:.5f} ({20*np.log10(rms_seg1_sp):.2f} dBFS), E = {e_seg1_sp:.2f}")
print(f"  * Đoạn 2 (2.5s - 3.3s, Âm vô thanh / Unvoiced):    Peak = {peak_seg2_sp:.5f} ({20*np.log10(peak_seg2_sp):.2f} dBFS), RMS = {rms_seg2_sp:.5f} ({20*np.log10(rms_seg2_sp):.2f} dBFS), E = {e_seg2_sp:.2f}")
diff_db_sp = 20 * np.log10(rms_seg1_sp / (rms_seg2_sp + 1e-12))
ratio_sp = rms_seg1_sp / (rms_seg2_sp + 1e-12)
print(f"  -> Nhận xét: Đoạn 1 (Voiced) có năng lượng RMS gấp {ratio_sp:.2f} lần đoạn 2 (Unvoiced), chênh lệch {diff_db_sp:.2f} dB.")

# Đối với Âm nhạc:
# Đoạn 1: Cao trào Forte hòa tấu (37.8s đến 38.6s, dài 0.8s)
# Đoạn 2: Dạo đầu nhẹ nhàng Piano (0.0s đến 0.8s, dài 0.8s)
sr_mu = results["music"]["sr"]
x_mu = results["music"]["data"]

seg1_mu = x_mu[int(37.8 * sr_mu) : int(38.6 * sr_mu)]
seg2_mu = x_mu[int(0.0 * sr_mu) : int(0.8 * sr_mu)]

rms_seg1_mu = np.sqrt(np.mean(seg1_mu**2))
rms_seg2_mu = np.sqrt(np.mean(seg2_mu**2))
peak_seg1_mu = np.max(np.abs(seg1_mu))
peak_seg2_mu = np.max(np.abs(seg2_mu))
e_seg1_mu = np.sum(seg1_mu**2)
e_seg2_mu = np.sum(seg2_mu**2)

print("\n[2. Phân tích Âm nhạc (Music)]")
print(f"  * Đoạn 1 (37.8s - 38.6s, Cao trào Forte):          Peak = {peak_seg1_mu:.5f} ({20*np.log10(peak_seg1_mu):.2f} dBFS), RMS = {rms_seg1_mu:.5f} ({20*np.log10(rms_seg1_mu):.2f} dBFS), E = {e_seg1_mu:.2f}")
print(f"  * Đoạn 2 (0.0s - 0.8s, Dạo đầu nhẹ nhàng Piano):   Peak = {peak_seg2_mu:.5f} ({20*np.log10(peak_seg2_mu):.2f} dBFS), RMS = {rms_seg2_mu:.5f} ({20*np.log10(rms_seg2_mu):.2f} dBFS), E = {e_seg2_mu:.2f}")
diff_db_mu = 20 * np.log10(rms_seg1_mu / (rms_seg2_mu + 1e-12))
ratio_mu = rms_seg1_mu / (rms_seg2_mu + 1e-12)
print(f"  -> Nhận xét: Đoạn 1 (Forte) có năng lượng RMS gấp {ratio_mu:.2f} lần đoạn 2 (Piano), chênh lệch {diff_db_mu:.2f} dB.")

# VẼ ĐỒ THỊ WAVEFORM
fig = plt.figure(figsize=(15, 11), constrained_layout=True)
gs = fig.add_gridspec(4, 2)

time_sp = np.linspace(0, len(x_sp) / sr_sp, len(x_sp))
time_mu = np.linspace(0, len(x_mu) / sr_mu, len(x_mu))

# Panel 1: Waveform toàn phần Tiếng nói
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(time_sp, x_sp, color='#1f77b4', linewidth=0.5, alpha=0.85, label='Mono Waveform x[n]')
ax1.axvspan(3.4, 4.2, color='#2ca02c', alpha=0.35, label='Đoạn 1: Âm hữu thanh / Voiced (3.4s - 4.2s)')
ax1.axvspan(2.5, 3.3, color='#ff7f0e', alpha=0.35, label='Đoạn 2: Âm vô thanh / Unvoiced (2.5s - 3.3s)')
ax1.axhline(results["speech"]["rms"], color='red', linestyle='--', linewidth=1, label=f'RMS toàn file = {results["speech"]["rms"]:.3f} (-19.01 dBFS)')
ax1.axhline(-results["speech"]["rms"], color='red', linestyle='--', linewidth=1)
ax1.set_title("1. Toàn bộ dạng sóng (Waveform) tín hiệu tiếng nói (Speech - 14.84s, Fs = 44,100 Hz)", fontsize=11, fontweight='bold')
ax1.set_xlabel("Thời gian (giây)")
ax1.set_ylabel("Biên độ chuẩn hóa")
ax1.set_ylim(-1.05, 1.05)
ax1.legend(loc='upper right', framealpha=0.9, fontsize=8)

# Panel 2: Zoom 2 đoạn tiếng nói
t_seg1_sp = np.linspace(3.4, 4.2, len(seg1_sp))
t_seg2_sp = np.linspace(2.5, 3.3, len(seg2_sp))

ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(t_seg1_sp, seg1_sp, color='#2ca02c', linewidth=0.8)
ax2.axhline(rms_seg1_sp, color='red', linestyle=':', label=f'RMS = {rms_seg1_sp:.3f} (-16.13 dBFS)')
ax2.axhline(-rms_seg1_sp, color='red', linestyle=':')
ax2.set_title("1a. Zoom đoạn 1: Âm hữu thanh (Voiced - 3.4s đến 4.2s)\nDao động tuần hoàn rõ rệt (dây thanh khép mở), biên độ lớn", fontsize=9, fontweight='bold')
ax2.set_xlabel("Thời gian (giây)")
ax2.set_ylabel("Biên độ")
ax2.set_ylim(-0.9, 0.9)
ax2.legend(loc='upper right', fontsize=8)

ax3 = fig.add_subplot(gs[1, 1])
ax3.plot(t_seg2_sp, seg2_sp, color='#ff7f0e', linewidth=0.8)
ax3.axhline(rms_seg2_sp, color='red', linestyle=':', label=f'RMS = {rms_seg2_sp:.3f} (-29.64 dBFS)')
ax3.axhline(-rms_seg2_sp, color='red', linestyle=':')
ax3.set_title("1b. Zoom đoạn 2: Âm vô thanh / Chuyển tiếp (Unvoiced - 2.5s đến 3.3s)\nDao động ngẫu nhiên dạng tạp âm, biên độ suy giảm rõ rệt", fontsize=9, fontweight='bold')
ax3.set_xlabel("Thời gian (giây)")
ax3.set_ylabel("Biên độ")
ax3.set_ylim(-0.9, 0.9)
ax3.legend(loc='upper right', fontsize=8)

# Panel 3: Waveform toàn phần Âm nhạc
ax4 = fig.add_subplot(gs[2, :])
ax4.plot(time_mu, x_mu, color='#9467bd', linewidth=0.4, alpha=0.85, label='Mono Waveform x[n]')
ax4.axvspan(37.8, 38.6, color='#d62728', alpha=0.35, label='Đoạn 1: Cao trào Forte (37.8s - 38.6s)')
ax4.axvspan(0.0, 0.8, color='#8c564b', alpha=0.35, label='Đoạn 2: Dạo đầu nhẹ nhàng Piano (0.0s - 0.8s)')
ax4.axhline(results["music"]["rms"], color='red', linestyle='--', linewidth=1, label=f'RMS toàn file = {results["music"]["rms"]:.3f} (-22.80 dBFS)')
ax4.axhline(-results["music"]["rms"], color='red', linestyle='--', linewidth=1)
ax4.set_title("2. Toàn bộ dạng sóng (Waveform) tín hiệu âm nhạc (Music - 45.84s, Fs = 44,100 Hz)", fontsize=11, fontweight='bold')
ax4.set_xlabel("Thời gian (giây)")
ax4.set_ylabel("Biên độ chuẩn hóa")
ax4.set_ylim(-1.05, 1.05)
ax4.legend(loc='upper right', framealpha=0.9, fontsize=8)

# Panel 4: Zoom 2 đoạn âm nhạc
t_seg1_mu = np.linspace(37.8, 38.6, len(seg1_mu))
t_seg2_mu = np.linspace(0.0, 0.8, len(seg2_mu))

ax5 = fig.add_subplot(gs[3, 0])
ax5.plot(t_seg1_mu, seg1_mu, color='#d62728', linewidth=0.7)
ax5.axhline(rms_seg1_mu, color='black', linestyle=':', label=f'RMS = {rms_seg1_mu:.3f} (-15.56 dBFS)')
ax5.axhline(-rms_seg1_mu, color='black', linestyle=':')
ax5.set_title("2a. Zoom đoạn 1: Cao trào Forte (37.8s đến 38.6s)\nTổng hợp nhiều nhạc cụ dây (tutti), biên độ sóng dày đặc", fontsize=9, fontweight='bold')
ax5.set_xlabel("Thời gian (giây)")
ax5.set_ylabel("Biên độ")
ax5.set_ylim(-0.9, 0.9)
ax5.legend(loc='upper right', fontsize=8)

ax6 = fig.add_subplot(gs[3, 1])
ax6.plot(t_seg2_mu, seg2_mu, color='#8c564b', linewidth=0.7)
ax6.axhline(rms_seg2_mu, color='black', linestyle=':', label=f'RMS = {rms_seg2_mu:.3f} (-22.34 dBFS)')
ax6.axhline(-rms_seg2_mu, color='black', linestyle=':')
ax6.set_title("2b. Zoom đoạn 2: Dạo đầu nhẹ nhàng (Piano - 0.0s đến 0.8s)\nGiai điệu mở đầu thưa hơn, biên độ vừa phải", fontsize=9, fontweight='bold')
ax6.set_xlabel("Thời gian (giây)")
ax6.set_ylabel("Biên độ")
ax6.set_ylim(-0.9, 0.9)
ax6.legend(loc='upper right', fontsize=8)

output_fig = "figures/waveform.png"
plt.savefig(output_fig, dpi=300)
plt.close()
print(f"\nĐã xuất đồ thị chất lượng cao tại: {output_fig}")
