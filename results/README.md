# Bằng chứng thực nghiệm

Các ca dưới đây gọi LLM thật qua 9Router và chạy UR3e trong Gazebo.
T5 được chạy trước khi có MSSV; T7 dùng MSSV thật 23020774, với P = 74 mod 6 = 2.

| Ca | Câu lệnh | Kết quả | Skill hoàn tất | Thời gian (s) |
|---|---|---|---:|---:|
| [T1](validation_T1.json) | Đưa khối màu đỏ vào vùng B. | Thành công | 3 | 37.621 |
| [T2](validation_T2.json) | Hãy lấy khối màu vàng và đặt nó vào ô A. | Thành công | 3 | 41.531 |
| [T3](validation_T3.json) | Move the blue cube to zone C. | Thành công | 3 | 36.670 |
| [T4](validation_T4.json) | Đưa khối màu tím vào vùng D. | Từ chối đúng; không chuyển động | 0 | 8.191 |
| [T5](validation_T5.json) | Arrange all objects according to my student ID. | Từ chối đúng; không chuyển động | 0 | 5.781 |
| [T6](validation_T6.json) | Đặt khối đỏ vào vùng A, khối vàng vào vùng B và khối xanh dương vào vùng C, rồi về home. | Thành công | 7 | 87.426 |
| [T7](validation_student_P2.json) | Arrange all objects according to my student ID. | Thành công | 7 | 84.572 |

T1–T3 chạy tuần tự trên một cảnh. T6 và T7 bắt đầu từ các cảnh mới.
T7: Zone A → vàng, Zone B → đỏ, Zone C → xanh; 7/7 skill, 19/19 chuyển động MoveIt thành công.
Video màu quay trực tiếp: `ur3e_mssv_23020774_demo.mp4` (104 giây); log của lần quay: `demo_T7_video.json`.
Ảnh camera gốc, bản cắt màu và hình trích đoạn mã dùng trong báo cáo đều nằm trong thư mục này.
Validator: 19 bài kiểm thử đạt; xem `validator_tests.log`.
Các file `development_*`, `red_to_b_*` và `llm_red_*` ghi lại quá trình sửa lỗi.
