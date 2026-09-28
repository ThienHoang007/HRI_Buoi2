#!/usr/bin/env bash
set -eo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TASK_ROOT"
START_CASE="${1:-1}"
if (( START_CASE <= 1 )); then
bash scripts/run.sh --command 'Đưa khối màu đỏ vào vùng B.' --result results/validation_T1.json > results/validation_T1.log 2>&1
python3 -c 'import json; assert json.load(open("results/validation_T1.json"))["success"]'
fi
if (( START_CASE <= 2 )); then
bash scripts/run.sh --command 'Hãy lấy khối màu vàng và đặt nó vào ô A.' --result results/validation_T2.json > results/validation_T2.log 2>&1
python3 -c 'import json; assert json.load(open("results/validation_T2.json"))["success"]'
fi
if (( START_CASE <= 3 )); then
bash scripts/run.sh --command 'Move the blue cube to zone C.' --result results/validation_T3.json > results/validation_T3.log 2>&1
python3 -c 'import json; assert json.load(open("results/validation_T3.json"))["success"]'
fi
bash scripts/run.sh --command 'Đưa khối màu tím vào vùng D.' --result results/validation_T4.json > results/validation_T4.log 2>&1
bash scripts/run.sh --command 'Arrange all objects according to my student ID.' --result results/validation_T5.json > results/validation_T5.log 2>&1
PYTHONPATH=src/ur3_llm_control python3 -m unittest discover -s tests -v > results/validator_tests.log 2>&1
