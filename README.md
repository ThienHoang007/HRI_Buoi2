# Bài thực hành 02 — UR3e, LLM và Skill-based Planning

Workspace ROS 2 độc lập với bài trước. Mã nguồn nằm trong `src/ur3_llm_control`;
báo cáo là `bao_cao_bai_thuc_hanh_02.tex`; bằng chứng chạy thử nằm trong `results`.

Đã xác nhận năm tác vụ LLM hợp lệ (ba tác vụ đơn, một tác vụ ba vật và một tác vụ
theo MSSV 23020774), hoàn thành 23/23 skill; hai yêu cầu không hợp lệ bị từ chối;
19 bài kiểm thử validator đạt.
Xem [bảng bằng chứng thực nghiệm](results/README.md). Gói `bao_cao_latex.zip`
chứa nguồn LaTeX, ảnh Gazebo màu và hình trích đoạn mã dùng trong báo cáo.

## Môi trường

- Ubuntu 22.04 trong WSL2; ROS 2 Humble.
- Gazebo Classic 11, `gazebo_ros`, `gazebo_ros2_control`.
- MoveIt 2, `ur_description`, `ur_moveit_config`.
- Python 3, PyYAML, Pillow; C++17 cho plugin đầu hút.
- 9Router: API tương thích OpenAI `/v1/chat/completions`.

Đây là mô phỏng UR3e với đầu hút lý tưởng. Plugin tạo khớp cố định giữa cup và
vật khi khoảng cách tâm không quá 35 mm, rồi tháo khớp khi thả. Vật được vận
chuyển bởi liên kết vật lý Gazebo; không dùng lệnh đặt lại tọa độ vật để giả lập
kết quả thao tác. Mô hình này chưa đánh giá lực hút, biến dạng hoặc trượt thực tế.

## Build trong Ubuntu

```bash
cd /mnt/c/Users/ThienHoang/Documents/ChatGPT/Ros
source /opt/ros/humble/setup.bash
python3 scripts/generate_world.py
colcon build --packages-select ur3_llm_control --executor sequential
source install/setup.bash
```

Nếu chuyển sang máy khác, cài các dependency được khai báo trong `package.xml`
trước khi build. `scripts/generate_world.py` tạo scene từ `config/scene.yaml`.
Sau khi đổi scene, URDF hoặc cấu hình sinh viên, tạo lại world (nếu cần) và build lại.

## Khởi động

Terminal 1 trong Ubuntu:

```bash
bash scripts/launch.sh gui:=true
```

Dùng `gui:=false` để chạy không mở cửa sổ Gazebo. Camera toàn cảnh của simulator
phát ảnh ở 6 khung hình/giây; camera chỉ dùng làm bằng chứng, không dùng để nhận dạng vật.
Các script sử dụng `ROS_DOMAIN_ID=42` để tách khỏi bài thực hành trước.

Terminal 2 trong Ubuntu, cấu hình 9Router đã kết nối model:

```bash
export NINEROUTER_BASE_URL=http://127.0.0.1:20128/v1
export NINEROUTER_MODEL=oc/mimo-v2.5-free
read -rs -p '9Router API key: ' NINEROUTER_API_KEY; echo
export NINEROUTER_API_KEY
bash scripts/run.sh --command 'Đưa khối màu đỏ vào vùng B.' --result results/red.json
bash scripts/run.sh --command 'Hãy lấy khối màu vàng và đặt nó vào ô A.' --result results/yellow.json
bash scripts/run.sh --command 'Move the blue cube to zone C.' --result results/blue.json
```

Model là cấu hình thay đổi được; cần chọn model còn được nhà cung cấp hỗ trợ.
Lỗi API, JSON hoặc validator khiến tác vụ bị từ chối trước khi robot di chuyển.
Một lần chạy chỉ nhận một tác vụ; đợi tác vụ kết thúc trước khi nhập tác vụ khác.

### 9Router riêng cho máy Windows/WSL này

9Router được cài riêng trong `.runtime/nine-router`, dữ liệu và API key nằm trong
`.runtime` (được loại khỏi Git). Khởi động bằng PowerShell:

```powershell
$env:DATA_DIR = Join-Path $PWD '.runtime\nine-router-data'
$env:PORT = '20128'
$env:HOSTNAME = '127.0.0.1'
node .runtime\nine-router\node_modules\9router\app\custom-server.js
```

Dashboard: <http://127.0.0.1:20128>. Khi có `.runtime/nine-api-key`, `run.sh`
tự đọc key và dùng `scripts/http_bridge.cjs` qua Windows Node để truy cập
localhost Windows từ WSL NAT. Request vẫn đi vào API 9Router thật. Trên Ubuntu
thuần, dùng HTTP trực tiếp với các biến môi trường ở trên.

## Cấu trúc và giao tiếp

- `skill_executor`: node ROS 2 nhận câu lệnh qua CLI, gọi planner, kiểm tra và thực thi.
- `llm_planner.py`: mô-đun HTTP gọi LLM qua 9Router; prompt nằm trong `prompts/planner.txt`.
- `task_validator.py`: schema chặt, allowlist, thứ tự gắp/thả và kiểm tra vùng bị chiếm.
- `robot_skills.py`: `home`, `pick`, `place`; KDL/OMPL qua `/move_action`, các đoạn
  hạ/nâng/rút qua `/compute_cartesian_path` và `/execute_trajectory` của MoveIt.
- `skill_grasp.cpp`: plugin Gazebo; dịch vụ `/grasp/{red_cube,yellow_cube,blue_cube}`.
- MoveIt `move_group`: KDL, OMPL/RRTConnect, kiểm tra va chạm và giới hạn khớp.
- `joint_trajectory_controller`: nhận quỹ đạo đã được MoveIt lập kế hoạch.
- `/gazebo/get_entity_state`: đọc trạng thái thực và xác nhận vật đến đích.

LLM chỉ sinh skill và tên vật/vùng. Tọa độ, tư thế và giới hạn tốc độ nằm ở lớp
skill; LLM không có quyền gửi quỹ đạo hoặc điều khiển khớp.

Đường Cartesian dùng bước 5 mm, chỉ chạy khi đủ 100% và từng mẫu quỹ đạo sau
tham số hóa thời gian đều qua kiểm tra va chạm. Cặp vật–mặt bàn được cho phép
tiếp xúc riêng trong đoạn nhấc thẳng đứng; sau đó bật lại kiểm tra cặp này.
Nghiệm IK tiếp cận được khởi tạo bằng tư thế khuỷu tay cao để hỗ trợ đường hạ
thẳng đứng. Seed IK không được gửi trực tiếp tới bộ điều khiển.

Đầu ra chỉ có dạng:

```json
{"plan":[{"skill":"pick","object":"red_cube"},{"skill":"place","object":"red_cube","zone":"zone_b"},{"skill":"home"}]}
```

## Kiểm thử

```bash
PYTHONPATH=src/ur3_llm_control python3 -m unittest discover -s tests -v
bash scripts/run.sh --inspect --result results/scene.json
bash scripts/run.sh --test-plan tests/red_to_b.json --result results/skill_test.json
```

`--test-plan` là kiểm thử tích hợp skill trực tiếp, **không phải** lần chạy LLM.
File JSON kết quả lưu `mode` để phân biệt. Chạy lại scene bằng cách dừng terminal
mô phỏng với Ctrl+C rồi khởi động lại, nếu cần đưa các vật về vị trí ban đầhi
khởi động một tác vụ mới. Nếu còn giữ vật, dừng và khởi động lại mô phỏng trước.

