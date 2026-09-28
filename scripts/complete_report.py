"""Refresh the evidence index and portable LaTeX archive.

The edited .tex file is the report source and is never overwritten here.
"""
from __future__ import annotations

import json
import math
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
REPORT = ROOT / "bao_cao_bai_thuc_hanh_02.tex"

cases = [(f"T{i}", RESULTS / f"validation_T{i}.json") for i in range(1, 7)]
cases.append(("T7", RESULTS / "validation_student_P2.json"))
runs = [(label, json.loads(path.read_text(encoding="utf-8")), path) for label, path in cases]
for label, run, _ in runs:
    expected = label not in {"T4", "T5"}
    if run["success"] != expected:
        raise RuntimeError(f"Unexpected result for {label}: success={run['success']}")

targets = {
    "yellow_cube": (0.4, -0.2, 0.12),
    "red_cube": (0.4, 0.0, 0.12),
    "blue_cube": (0.4, 0.2, 0.12),
}
student = runs[-1][1]
student_errors = {
    obj: round(math.dist(student["final_positions"][obj], target) * 1000, 3)
    for obj, target in targets.items()
}
summary = {
    "student_name": "Nguyễn Hoàng Thiện",
    "student_id": "23020774",
    "last_two_digits": 74,
    "P": 2,
    "student_assignment": {
        "zone_a": "yellow_cube", "zone_b": "red_cube", "zone_c": "blue_cube"
    },
    "student_case": {
        "success": student["success"],
        "seconds": student["seconds"],
        "skills": len(student["steps"]),
        "motions": len(student["motions"]),
        "cartesian_motions": sum("fraction" in motion for motion in student["motions"]),
        "error_mm": student_errors,
    },
}
(RESULTS / "validation_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

lines = [
    "# Bằng chứng thực nghiệm",
    "",
    "Các ca dưới đây gọi LLM thật qua 9Router và chạy UR3e trong Gazebo.",
    "T5 được chạy trước khi có MSSV; T7 dùng MSSV thật 23020774, với P = 74 mod 6 = 2.",
    "",
    "| Ca | Câu lệnh | Kết quả | Skill hoàn tất | Thời gian (s) |",
    "|---|---|---|---:|---:|",
]
for label, run, path in runs:
    outcome = "Thành công" if run["success"] else "Từ chối đúng; không chuyển động"
    completed = sum(step["status"] == "SUCCESS" for step in run["steps"])
    lines.append(
        f'| [{label}]({path.name}) | {run["command"]} | {outcome} | '
        f'{completed} | {run["seconds"]:.3f} |'
    )
lines.extend(
    [
        "",
        "T1–T3 chạy tuần tự trên một cảnh. T6 và T7 bắt đầu từ các cảnh mới.",
        "T7: Zone A → vàng, Zone B → đỏ, Zone C → xanh; 7/7 skill, 19/19 chuyển động MoveIt thành công.",
        "Video màu quay trực tiếp: `ur3e_mssv_23020774_demo.mp4` (104 giây); log của lần quay: `demo_T7_video.json`.",
        "Ảnh camera gốc, bản cắt màu và hình trích đoạn mã dùng trong báo cáo đều nằm trong thư mục này.",
        "Validator: 19 bài kiểm thử đạt; xem `validator_tests.log`.",
        "Các file `development_*`, `red_to_b_*` và `llm_red_*` ghi lại quá trình sửa lỗi.",
    ]
)
(RESULTS / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

source = REPORT.read_text(encoding="utf-8")
assets = sorted(
    {
        name
        for name in re.findall(r"\\(?:Anh|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}", source)
        if name.startswith("results/")
    }
)
missing = [name for name in assets if not (ROOT / name).is_file()]
if missing:
    raise FileNotFoundError(f"Report image assets are missing: {missing}")
with zipfile.ZipFile(ROOT / "bao_cao_latex.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for path in [REPORT.relative_to(ROOT).as_posix(), *assets]:
        archive.write(ROOT / path, path)
print(json.dumps(summary, ensure_ascii=False, indent=2))
