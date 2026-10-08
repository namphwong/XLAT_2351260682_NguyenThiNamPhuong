# CSE457 — Xử lý âm thanh và tiếng nói

**Nguyễn Thị Nam Phương · MSSV 2351260682 · Lớp 65TTNT**  
Trường Đại học Thủy lợi

Repo lưu bài thực hành, dữ liệu và kết quả của Lab 1 và Lab 2. Mỗi lab nằm trong một thư mục riêng để notebook có thể chạy với các đường dẫn tương đối của lab đó.

| Bài | Nội dung | Notebook | Báo cáo |
|---|---|---|---|
| [Lab 1](lab1/) | Phân tích tín hiệu, FFT/STFT, cửa sổ, lọc, lượng tử hóa và resampling | [Lab01_2351260682.ipynb](lab1/Lab01_2351260682.ipynb) | [Markdown](lab1/README.md), [PDF](lab1/report_Lab01.pdf) |
| [Lab 2](lab2/) | Energy/ZCR, endpoint, MFCC, DTW và nhận dạng từ đơn | [Lab2_2351260682.ipynb](lab2/Lab2_2351260682.ipynb) | [Lab2_Report.md](lab2/Lab2_Report.md) và Markdown cuối notebook |

```text
.
├── README.md
├── .gitignore
├── lab1/
│   ├── Lab01_2351260682.ipynb
│   ├── Lab 1.pdf
│   ├── README.md
│   ├── report_Lab01.pdf
│   ├── audio/
│   └── figures/
└── lab2/
    ├── Lab2_2351260682.ipynb
    ├── Lab 2.pdf
    ├── README.md
    ├── Lab2_Report.md
    ├── lab2_*.py
    ├── requirements.txt
    ├── *_config.json
    ├── data_split.csv
    ├── results.csv
    ├── dataset/       # WAV sử dụng và MP3 nguồn
    ├── trimmed/       # WAV sau endpoint
    ├── figures/       # Hình minh họa
    ├── outputs/       # CSV/JSON trung gian và kiểm tra nộp
    ├── reports/       # Báo cáo từng phase
    ├── features/      # MFCC, DTW và cache thí nghiệm
    ├── experiments/   # Các đối chứng E1–E2
    ├── tests/         # Kiểm thử DTW, recognizer, evaluation và Δ
    └── tools/         # Trang ghi âm và script khởi động
```

Hướng dẫn môi trường, chạy notebook và kiểm tra nằm trong [README Lab 2](lab2/README.md). Với Lab 1, mở notebook từ thư mục `lab1/`; dữ liệu và hình giữ nguyên quan hệ đường dẫn với notebook.

Lab 2 có 25 bản ghi, split cố định 15 template + 10 test. Baseline có trim đạt **80%**, không trim **70%**, MFCC + Δ **80%**. Hai mẫu “không” bị nhận thành “hai”; báo cáo giữ nguyên kết quả và phân tích giới hạn. Cần nghe đối chiếu gốc/trim để xác nhận biên không mất phụ âm trước nộp.

Môi trường ảo, cache Python và tệp tạm không được đưa lên Git. Dữ liệu thực nghiệm, notebook đã chạy và các bằng chứng kết quả được giữ trong repo.
