"""Build the final Vietnamese report from the saved, fixed Lab 2 experiment."""
from pathlib import Path
import csv
import json


def rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def build_report(root):
    root = Path(root)
    metrics = json.loads((root / 'outputs/phase8_metrics.json').read_text(encoding='utf-8'))
    experiments = rows(root / 'outputs/phase9_experiment_summary.csv')
    results = rows(root / 'results.csv')
    trim = rows(root / 'outputs/phase4_trim_results.csv')
    before = sum(float(r['before_s']) for r in trim)
    after = sum(float(r['after_s']) for r in trim)
    experiment_table = '\n'.join(
        f"| {r['variant']} | {r['dimensions']} | {r['n_correct']}/{r['n_test']} | "
        f"{float(r['accuracy']):.0%} | {float(r['top2_accuracy']):.0%} | "
        f"{float(r['top3_accuracy']):.0%} | {float(r['macro_f1']):.4f} |"
        for r in experiments)
    prediction_table = '\n'.join(
        f"| {r['file']} | {r['true_label']} | {r['predicted_label']} | "
        f"{r['top1_label']}: {float(r['top1_score']):.4f} | "
        f"{r['top2_label']}: {float(r['top2_score']):.4f} | "
        f"{r['top3_label']}: {float(r['top3_score']):.4f} |" for r in results)
    confusion_table = '\n'.join(
        '| ' + label + ' | ' + ' | '.join(map(str, row)) + ' |'
        for label, row in zip(metrics['labels'], metrics['confusion_matrix']))
    warnings = ', '.join('`' + r['file'] + '`' for r in trim if r['warnings'])
    return f'''# Báo cáo cuối notebook — Phase 10

**LAB 2: Đặc trưng tiếng nói và nhận dạng bằng DTW**  
**Sinh viên:** Nguyễn Thị Nam Phương — **MSSV:** 2351260682 — **Lớp:** 65TTNT  
**Học phần:** CSE457, Trường Đại học Thủy lợi

## 1. Mục tiêu, dữ liệu và quy trình

Xây dựng hệ nhận dạng năm từ tách rời “không, một, hai, ba, bốn” bằng đặc trưng MFCC và DTW tự cài đặt. Pipeline: WAV → framing/energy/ZCR → endpoint → pre-emphasis → Hamming → phổ công suất → Mel → log → DCT → CMN → DTW → nhãn có template gần nhất. Hệ thống trả về ba nhãn khác nhau đứng đầu cùng điểm và template tương ứng.

Bộ dữ liệu có 25 lần thu, mỗi nhãn 5 file. Nguồn MP3 được giữ nguyên; các WAV sử dụng có định dạng PCM 16-bit, mono, 16 kHz. Chuyển đổi không khôi phục thông tin đã mất do nén MP3. Ba file `_01`–`_03` mỗi nhãn làm train/template (15 file); `_04`–`_05` làm test (10 file). `data_split.csv` lưu split và hash âm thanh giải mã để phát hiện file sao chép. Không dùng test làm template hoặc thay đổi tham số theo lỗi test.

Không có metadata phân nhóm người nói để thực hiện đánh giá người nói mới. Kết quả dưới đây chỉ áp dụng cho 10 utterance giữ lại của bộ dữ liệu này, chưa chứng minh khả năng tổng quát cho giọng nói và môi trường khác.

## 2. Bảng tham số thực tế

| Khối | Tham số và quy ước |
|---|---|
| Âm thanh | 16.000 Hz, mono, PCM 16-bit; không tăng gain khi trim |
| Framing | 25 ms = 400 mẫu; hop 10 ms = 160 mẫu; chỉ lấy frame đầy đủ |
| Cửa sổ | Hamming đối xứng; energy/RMS dùng frame có cửa sổ, ZCR dùng frame gốc |
| Energy/ZCR | Energy = tổng bình phương; RMS = căn trung bình bình phương; ZCR = số đổi dấu / 400, zero thuộc phía không âm |
| Log-energy endpoint | 10 log10(E + 1e-9), không phải SPL hoặc dBFS; làm mượt median 5 frame |
| Ước lượng nền | Median ở 200 ms đầu/cuối, bỏ digital zero |
| Ngưỡng endpoint | High = max(peak−18, noise+12); low = max(peak−30, noise+6) dB; nếu high quá sát peak thì dùng ngưỡng tương đối 18/30 dB |
| Điều kiện vùng nói | High liên tục ≥120 ms, nối gap ≤40 ms, mở rộng yếu tối đa 150 ms mỗi phía; chọn vùng high dài nhất, hòa thì theo energy |
| Bảo vệ biên | Margin 80 ms mỗi phía; hỗ trợ ZCR ≥0,1 với energy ≥max(low−5, noise+3) |
| Pre-emphasis | y[n] = x[n] − 0,97 x[n−1] |
| Phổ | rFFT 512 điểm, zero-pad frame 400; power = abs(FFT)² / 512 |
| Mel | 24 tam giác, từ 0 đến 8 kHz; mel(f) = 1125 ln(1+f/700); đỉnh 1, không chuẩn hóa diện tích |
| MFCC | ln(Mel energy + 1e-9), DCT-II trực chuẩn, giữ C0–C12, shape (T,13) |
| CMN | Trừ trung bình từng hệ số trong mỗi utterance, axis=0; giống nhau cho train/test |
| DTW | Euclidean giữa hai vector; bước (1,1), (1,0), (0,1); DP tối thiểu tổng cost; không giới hạn band |
| Hòa cost DTW | Ưu tiên path ít điểm hơn, tiếp đến chéo/lên/trái; truy vết từ cuối về đầu |
| Điểm DTW | Tổng cost trên path / số điểm path; đây là chuẩn hóa sau tìm path tổng cost tối ưu |
| Quyết định | Min score của 3 template mỗi nhãn; xếp hạng 5 nhãn, lấy top-3 nhãn khác nhau |
| Δ cho E2 | Hồi quy N=2 mỗi phía, lặp frame biên; tính trên MFCC đã CMN; ghép 13+13 chiều, trọng số 1, không ΔΔ |

## 3. Các phần A–G và sản phẩm

| Phần | Nội dung đã thực hiện | Bằng chứng |
|---|---|---|
| A | Đọc, chuyển đổi, kiểm tra 25 file và split cố định | outputs/dataset_audit.csv, outputs/audio_conversion.csv, data_split.csv, waveform |
| B | Framing, Hamming, energy, magnitude, RMS, ZCR và autocorrelation | outputs/phase3_*.csv, đồ thị 5 từ và autocorrelation |
| C | Endpoint và so sánh margin | outputs/phase4_trim_results.csv, trimmed/, đồ thị vùng giữ lại |
| D | MFCC từng bước, filterbank, CMN | mfcc_config.json, features/mfcc/, heatmap và filterbank |
| E | Euclidean, ma trận C/D, DP, backtrack và identity | outputs/phase6_*.csv, features/dtw/, hình path cùng/khác từ |
| F | 15 template, top-3 và demo WAV giữ lại | outputs/phase7_predictions.csv, template/label scores, demo trong notebook |
| G | Đánh giá đủ 10 test, confusion matrix, phân tích 2 lỗi, E1–E2 | results.csv, outputs/phase8_*.csv/json, experiments/phase9/, hình so sánh |

Endpoint giảm tổng thời lượng từ {before:.3f} s xuống {after:.3f} s, tương đương bỏ {100*(1-after/before):.2f}% thời lượng. Không diễn giải toàn bộ phần bỏ đi là silence đã gán nhãn. MFCC trim có 1.815 frame, shape mỗi file (T,13). Các kiểm tra identity của DTW trên 25 file đều có score 0. Các khoảng cách cùng/khác từ trên train có phân bố chồng lấn, vì vậy không thể dùng một ngưỡng đơn giản để bảo đảm phân biệt từ.

## 4. Kết quả nhận dạng cơ sở

Baseline endpoint 80 ms + MFCC13/CMN đạt **{metrics['n_correct']}/{metrics['n_test']} = {metrics['accuracy']:.0%} accuracy**, top-2 **90%**, top-3 **100%**, macro precision **0,7000**, macro recall **0,8000**, macro F1 **0,7333**. Precision của `khong` được đặt 0 theo `zero_division=0` vì không có dự đoán nhãn này. Mỗi nhãn chỉ có hai mẫu test; một mẫu đúng/sai làm accuracy tổng thay đổi 10 điểm phần trăm.

Ma trận nhầm lẫn: hàng = nhãn thật, cột = nhãn dự đoán; thứ tự không/một/hai/ba/bốn.

| Thật / dự đoán | khong | mot | hai | ba | bon |
|---|---|---|---|---|---|
{confusion_table}

![Ma trận nhầm lẫn cơ sở](figures/phase8_confusion_matrix.png)

| File test | Nhãn thật | Dự đoán | Top-1 / score | Top-2 / score | Top-3 / score |
|---|---|---|---|---|---|
{prediction_table}

Điểm thấp hơn nghĩa là gần template hơn; score và chênh lệch score không phải xác suất tin cậy. Hệ closed-set luôn chọn một trong năm nhãn, chưa có cơ chế từ chối từ ngoài từ vựng. Demo dùng `khong_04.wav` đã giữ lại, không được mô tả là lần thu mới.

## 5. Thí nghiệm E1–E2

Cùng split, 15 template, 10 test, metric và cách tổng hợp min theo nhãn. Mỗi cấu hình tính lại đặc trưng cho cả 25 WAV gốc. Đối chứng tính lại khớp Phase 8; không chỉnh split hay tham số sau khi xem test.

| Cấu hình | Chiều | Đúng / test | Accuracy | Top-2 | Top-3 | Macro F1 |
|---|---|---|---|---|---|---|
{experiment_table}

![So sánh accuracy các cấu hình](figures/phase9_accuracy_comparison.png)

**E1 — trim so với không trim:** chỉ đổi endpoint ở cả train/test. Trim tăng từ 70% lên 80%, sửa `ba_05.wav` từ “một” thành “ba”. Hai file “không” vẫn sai, nhưng nhãn sai đổi từ “một” sang “hai”. Full WAV có 6.324 frame, trim có 1.815 frame. Tổng số ô DP của 150 phép đối sánh là 9.757.163 và 777.974, chênh khoảng 12,54 lần; đây là khối lượng ô tính, không phải thời gian CPU đo được. Các path full được phân tích có 69,4–81,2% điểm nằm ngoài endpoint tham chiếu. Vùng ngoài endpoint có thể chứa nhiễu, tiếng click hoặc âm yếu; tỷ lệ này không phải tỷ lệ silence có ground truth.

**E2 — MFCC so với MFCC+Δ:** chỉ ghép đặc trưng động học. Công thức Δc[t] = Σ(n=1..2) n(c[t+n]−c[t−n]) / (2Σ(n=1..2)n²), mẫu ngoài biên được lặp từ frame đầu/cuối. Số frame và 13 cột tĩnh giữ nguyên. Accuracy vẫn 80%; top-2 tăng 90% lên 100%, nhãn thật của `khong_04.wav` từ hạng 3 lên hạng 2. Δ chưa sửa lỗi top-1 nào trong tập này. Score 13 và 26 chiều không được so với cùng ngưỡng tuyệt đối vì không gian đặc trưng thay đổi.

E3 là tùy chọn, không thực hiện trong báo cáo này. E4 về người nói chưa thực hiện vì thiếu metadata phân nhóm người nói. Không suy luận kết quả E4 từ split utterance hiện tại.

## 6. Trả lời 9 câu hỏi báo cáo

### Câu 1. Vì sao không dùng toàn bộ waveform làm template chính khi thời lượng khác nhau?

Hai lần đọc cùng từ có tốc độ và thời điểm bắt đầu khác nhau, làm vector mẫu khác chiều và không đồng bộ. So sánh từng mẫu chịu ảnh hưởng mạnh của pha, mức âm lượng, nền và khoảng im lặng. MFCC theo frame mô tả bao phổ, còn DTW cho phép căn chỉnh thời gian không tuyến tính. E1 cho thấy full WAV vẫn có thể đưa qua MFCC/DTW nhưng giảm accuracy và tăng khối lượng DP trong dữ liệu này; điều đó không đồng nghĩa waveform không có ích để kiểm tra chất lượng và biên.

### Câu 2. Vai trò của short-time energy và ZCR trong endpoint?

Energy phản ánh độ mạnh tín hiệu theo frame, hữu ích để tìm vùng nói nổi hơn nền; âm đầu/cuối yếu có thể bị bỏ nếu chỉ dùng ngưỡng energy cao. ZCR đo tốc độ đổi dấu, hỗ trợ nhận diện vùng giống âm vô thanh hoặc tiếng xát. Nhiễu cũng có thể có ZCR cao, nên ZCR không đủ để quyết định speech. Cài đặt phối hợp ngưỡng energy cao/thấp, nền, ZCR và margin 80 ms; việc giữ được phụ âm cần nghe lại, không chỉ nhìn đồ thị.

### Câu 3. Vì sao khoảng cách Mel filterbank theo Hz rộng dần ở tần số cao?

Thang Mel phi tuyến mel(f)=1125 ln(1+f/700). Với bước Mel bằng nhau, hàm nghịch đảo f=700(exp(mel/1125)−1) tạo bước Hz tăng dần. Filterbank có độ phân giải Hz dày ở vùng thấp và thưa ở vùng cao, mô phỏng gần đúng cách cảm nhận tần số; không có nghĩa hệ số cao hoàn toàn không quan trọng.

### Câu 4. Log và DCT trong MFCC có tác dụng gì?

Log nén dynamic range năng lượng các băng Mel, giảm sự lấn át của băng mạnh và biến nhân hệ số mức năng lượng thành cộng trong miền log. Epsilon ngăn log(0). DCT-II biến 24 log-energy tương quan thành các hệ số cepstral, thuận tiện giữ thành phần biến thiên trơn của bao phổ. Giữ C0–C12 tạo vector 13 chiều; C0 liên quan mức log-energy trung bình trên các băng, không đồng nhất trực tiếp với energy miền thời gian. CMN trừ trung bình mỗi hệ số để giảm lệch ổn định theo utterance, không loại bỏ mọi ảnh hưởng người nói hoặc nhiễu.

### Câu 5. Ý nghĩa bước ngang, dọc và chéo trong DTW?

Với hàng i là frame query, cột j là frame template: bước chéo tăng cả i,j để ghép một frame mỗi phía; bước dọc tăng i giữ j để nhiều query frame ghép một template frame; bước ngang giữ i tăng j để một query frame ghép nhiều template frame. Các bước mô tả co/giãn thời gian cục bộ, không phải bỏ âm tùy ý. Path đi đơn điệu, nối điểm đầu và cuối; không suy ra ranh giới âm vị chỉ từ các bước này.

### Câu 6. Vì sao chuẩn hóa DTW cost theo path length?

Tổng cost tích lũy thường lớn hơn khi path dài, ngay cả khi độ khác biệt trung bình tương tự. Chia tổng cho số điểm path tạo cost trung bình mỗi cặp frame, giảm thiên lệch do thời lượng và hỗ trợ xếp hạng template khác độ dài. Đây không phải bảo đảm bất biến hoàn toàn với thời lượng. Cài đặt tìm path tối thiểu tổng trước rồi chuẩn hóa, không giải bài toán path có trung bình nhỏ nhất.

### Câu 7. Vì sao MFCC khác nhau giữa hai lần nói cùng từ?

Các nguyên nhân gồm tốc độ đọc và độ dài âm; biến đổi phát âm, cao độ và cấu hình đường thanh quản; cường độ/ khoảng cách/ góc micro; đáp ứng micro và môi trường; nhiễu hoặc tiếng click; biên endpoint và vị trí frame. Pre-emphasis, CMN và DTW giảm một số biến thiên nhưng không loại hết chúng. Nếu cấu hình train/test khác nhau thì MFCC còn sai khác do pipeline, vì vậy cấu hình được lưu và kiểm tra nhất quán.

### Câu 8. Cặp từ dễ nhầm nhất và phân tích waveform/MFCC/path?

Trong baseline, cả hai mẫu “không” bị nhận thành “hai”; hai mẫu “hai” đều đúng. Nhầm lẫn quan sát là có hướng `khong → hai`, không chứng minh hai chiều tương đương. `khong_04.wav` dài sau trim 0,425 s (41 frame), score template đúng `khong_02.wav` là 7,104658 nhưng template `hai_02.wav` đạt 6,342908. `khong_05.wav` có 68 frame, hai score tương ứng 6,819653 và 6,734468, chênh chỉ 0,085185.

Waveform query có một vùng mạnh nổi bật, còn `khong_02.wav` có hai vùng mạnh; template “hai” có 65 frame so với 88 frame của template “không”. Heatmap MFCC cho thấy C0/C1 có cấu trúc biến thiên nổi bật. Path DTW của query ngắn phải ghép nhiều frame template, và cost trung bình của template “hai” thấp hơn dù nhãn sai. Số frame gần nhau chỉ là một yếu tố hỗ trợ phân tích, không quyết định trực tiếp kết quả vì DTW cho phép co giãn.

Giả thuyết là khác biệt cách phát âm/tốc độ, chất lượng thu hoặc endpoint ảnh hưởng âm yếu làm bao phổ gần template khác. Chưa nghe xác nhận nên không kết luận đã mất phụ âm. E2 nâng nhãn thật của `khong_04` lên top-2 nhưng chưa vượt nhãn sai. Hướng cải thiện cần kiểm chứng trên train/validation mới: nghe và gán biên, bổ sung template đa dạng cách đọc, giảm nhiễu khi thu; giữ test hiện tại để báo cáo trung thực.

![Waveform lỗi không 04](figures/phase8_error_khong_04_waveforms.png)

![MFCC lỗi không 04](figures/phase8_error_khong_04_mfcc.png)

![DTW path lỗi không 04](figures/phase8_error_khong_04_dtw.png)

### Câu 9. Hạn chế DTW với người nói mới và liên hệ Chương 3?

DTW căn chỉnh tốc độ nhưng vẫn so với ít template cụ thể. Người nói mới có thanh quản, phát âm, giọng và đặc tính thu khác, nên cùng từ có thể xa template hơn một từ khác. DTW không tự học phân bố biến thiên giữa nhiều người nói; CMN cũng không tạo đặc trưng hoàn toàn độc lập người nói.

Trang 15 của đề Lab 2 nêu rõ HMM, mô hình âm học, mô hình ngôn ngữ và từ điển phát âm thuộc Lab/Chương 3. HMM và mô hình âm học huấn luyện trên nhiều người nói là hướng phù hợp hơn để mô hình hóa trạng thái âm học và biến thiên thời gian/phát âm thay vì dựa vào một số bản ghi mẫu. Từ điển phát âm và mô hình ngôn ngữ hỗ trợ khi mở rộng từ vựng hoặc chuỗi từ; chúng không tự khắc phục toàn bộ khác biệt âm học của người nói mới. Đây là liên hệ lý thuyết, chưa triển khai hoặc đo độ chính xác HMM trong Lab này.

## 7. Kết luận và giới hạn

Hệ thống hoàn thành trích MFCC theo từng bước, tự cài DP/backtracking DTW, nhận dạng theo nhiều template và đánh giá toàn bộ test. Baseline đạt 8/10, có hai lỗi “không” → “hai”. E1 cho thấy trim giúp accuracy và giảm số ô DP; E2 cải thiện top-2 nhưng không thay đổi top-1. Kết quả chỉ là thực nghiệm trên tập nhỏ với 5 nhãn, chưa đủ kết luận về khả năng nhận dạng người nói mới hoặc dữ liệu ngoài từ vựng.

**Cần kiểm tra thủ công trước nộp:** nghe đối chiếu WAV gốc/trim, ưu tiên hai file lỗi và bảy file có cảnh báo endpoint: {warnings}. Chưa đánh dấu xác nhận “không mất phụ âm” hoặc “mọi file đúng từ” khi chưa nghe. Notebook có helper `listen_endpoint_comparison` để hỗ trợ đối chiếu.

## 8. Tái lập và tệp nộp

Chọn kernel **Lab 2 (Python 3.11)** (`lab2-2351260682`), Restart Kernel rồi Run All từ đầu. Không cần chạy cell thủ công theo thứ tự khác. Kiểm thử:

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 -m unittest discover -s tests -p 'test_lab2_*.py' -v
```

Tệp chính: `Lab2_2351260682.ipynb`, `dataset/`, `figures/`, `results.csv`. Nộp kèm các module `lab2_*.py`, cấu hình JSON, `data_split.csv`, `requirements.txt` và `README.md` để notebook tái lập được. `trimmed/`, `features/`, `experiments/` và CSV/báo cáo từng phase lưu bằng chứng chi tiết. Không cần mang `.venv-lab2/`, `__pycache__/` hoặc `tmp/` sang máy khác; tạo môi trường theo README.

Báo cáo này nằm trong phần Markdown cuối notebook và có bản riêng `Lab2_Report.md`, đáp ứng lựa chọn báo cáo Markdown ở mục 7 của đề. Chưa xuất PDF. Kiểm tra tự động sau Run All được lưu ở `reports/Phase10_Submission_Check.md` và `outputs/phase10_submission_manifest.csv`; kiểm tra tự động không thay thế bước nghe thủ công.

**Nguồn:** `Lab 2.pdf`, đặc biệt yêu cầu báo cáo/sản phẩm ở trang 13–15; dữ liệu và bảng kết quả do pipeline trong notebook tạo. Không sử dụng dịch vụ ASR trực tuyến.
'''


def write_report(root):
    root = Path(root)
    report = build_report(root)
    (root / 'Lab2_Report.md').write_text(report, encoding='utf-8')
    return report


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    write_report(root)
    print(root / 'Lab2_Report.md')
