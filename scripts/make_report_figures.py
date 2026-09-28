"""Create faithful color camera crops and readable source-code figures."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "ur3_llm_control" / "ur3_llm_control"
RESULTS = ROOT / "results"
FONT = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 25)
TITLE_FONT = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 29)


def camera_crop(source: str, target: str) -> None:
    with Image.open(RESULTS / source) as image:
        image.crop((440, 190, 950, 710)).convert("RGB").save(RESULTS / target)


def code_figure(source: str, spans: list[tuple[int, int]], target: str) -> None:
    path = PKG / source
    original = path.read_text(encoding="utf-8").splitlines()
    selected: list[tuple[int | None, str]] = []
    for index, (first, last) in enumerate(spans):
        if index:
            selected.append((None, "..."))
        selected.extend((line, original[line - 1]) for line in range(first, last + 1))

    width = 1700
    row_height = 36
    image = Image.new("RGB", (width, 100 + row_height * len(selected) + 24), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 74), fill="#e9edf2")
    draw.text((34, 18), source, font=TITLE_FONT, fill="#172838")
    draw.line((0, 74, width, 74), fill="#a6afb8", width=2)
    for row, (number, content) in enumerate(selected):
        y = 94 + row * row_height
        if number is None:
            draw.text((112, y), content, font=FONT, fill="#6a7077")
            continue
        important = any(
            term in content
            for term in (
                "p = int(", "return p,", "context =", "plan = parse_plan(",
                "steps=validate(", "node.pick(", "node.place(", "ZONE_OCCUPIED",
            )
        )
        if important:
            draw.rectangle((94, y - 2, width - 28, y + 32), fill="#fff3cd")
        draw.text((28, y), f"{number:>3}", font=FONT, fill="#64717e")
        draw.text((116, y), content, font=FONT, fill="#172838")
    image.save(RESULTS / target)


for source, target in (
    ("validation_T1.before.png", "validation_T1.before_color_crop.png"),
    ("validation_T1.step1.png", "validation_T1.step1_color_crop.png"),
    ("validation_T6.after.png", "validation_T6.after_color_crop.png"),
    ("validation_student_P2.after.png", "validation_student_P2.after_color_crop.png"),
):
    camera_crop(source, target)

code_figure("llm_planner.py", [(12, 23), (41, 45)], "code_llm_planner.png")
code_figure("task_validator.py", [(39, 55), (62, 70)], "code_task_validator.png")
code_figure("skill_executor.py", [(40, 55)], "code_skill_executor.png")
code_figure("task_validator.py", [(14, 18)], "code_student_assignment.png")
