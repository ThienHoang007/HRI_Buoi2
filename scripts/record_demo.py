"""Record the live Gazebo camera and task log as a narrated-by-text MP4.

Run under ROS 2 Humble while the simulator is active; stop with Ctrl+C after
the task completes. Frames come from /overview/overview/image_raw, not stills.
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

import rclpy
from PIL import Image as PILImage, ImageDraw, ImageFont
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


TASK_STEPS = [
    "pick(yellow_cube)", "place(yellow_cube, A)",
    "pick(red_cube)", "place(red_cube, B)",
    "pick(blue_cube)", "place(blue_cube, C)", "home()",
]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


class DemoRecorder(Node):
    def __init__(self, output: Path, log: Path, stop_file: Path, fps: int):
        super().__init__("ur3e_demo_recorder")
        self.output, self.log, self.stop_file, self.fps = output, log, stop_file, fps
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.stop_file.unlink(missing_ok=True)
        self.log.unlink(missing_ok=True)
        self.font = ImageFont.truetype(FONT, 21)
        self.small = ImageFont.truetype(FONT, 17)
        self.head = ImageFont.truetype(FONT, 30)
        self.ffmpeg = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
             "-pixel_format", "rgb24", "-video_size", "1280x720",
             "-framerate", str(fps), "-i", "-", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
             "-movflags", "+frag_keyframe+empty_moov+default_base_moof", str(output)],
            stdin=subprocess.PIPE,
        )
        self.started = None
        self.frames = 0
        self.completed = 0
        self.success = False
        self.offset = 0
        self.stop_requested = False
        self.create_subscription(Image, "/overview/overview/image_raw", self.frame,
                                 qos_profile_sensor_data)
        self.create_timer(0.5, self.check_stop)

    def check_stop(self):
        if self.stop_file.exists():
            self.stop_requested = True

    def update_log(self):
        if not self.log.exists():
            return
        size = self.log.stat().st_size
        if size < self.offset:
            self.offset = 0
            self.completed = 0
            self.success = False
        with self.log.open("r", encoding="utf-8", errors="replace") as stream:
            stream.seek(self.offset)
            for line in stream:
                if line.startswith("EXECUTION: "):
                    try:
                        if json.loads(line[len("EXECUTION: "):]).get("status") == "SUCCESS":
                            self.completed = min(self.completed + 1, len(TASK_STEPS))
                    except json.JSONDecodeError:
                        pass
                elif line.startswith("TASK SUCCESS"):
                    self.success = True
            self.offset = stream.tell()

    def compose(self, image, elapsed):
        frame = PILImage.new("RGB", (1280, 720), "white")
        camera = image.crop((360, 0, 1080, 720))
        frame.paste(camera, (0, 0))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((720, 0, 1279, 719), fill=(247, 249, 251))
        draw.line((720, 0, 720, 720), fill=(50, 56, 60), width=3)
        draw.text((750, 28), "UR3e  |  LLM demo", font=self.head, fill=(20, 30, 38))
        draw.text((750, 80), "ROS 2 Humble + Gazebo + MoveIt 2", font=self.small,
                  fill=(55, 65, 75))
        draw.line((750, 117, 1248, 117), fill=(150, 160, 170), width=2)
        draw.text((750, 138), "Student ID: 23020774", font=self.font, fill=(20, 30, 38))
        draw.text((750, 175), "P = 74 mod 6 = 2", font=self.font, fill=(20, 30, 38))
        for y, zone, name, color in (
            (224, "A", "YELLOW", (230, 183, 0)),
            (259, "B", "RED", (210, 40, 35)),
            (294, "C", "BLUE", (36, 75, 220)),
        ):
            draw.rectangle((752, y + 3, 774, y + 25), fill=color, outline=(40, 40, 40))
            draw.text((789, y), f"Zone {zone}  <-  {name}", font=self.font,
                      fill=(20, 30, 38))
        draw.line((750, 337, 1248, 337), fill=(150, 160, 170), width=2)
        draw.text((750, 351), "LLM plan / execution", font=self.font,
                  fill=(20, 30, 38))
        for index, step in enumerate(TASK_STEPS):
            y = 393 + 35 * index
            if index < self.completed:
                mark, color = "OK", (20, 115, 65)
            elif index == self.completed and not self.success:
                mark, color = "->", (22, 70, 145)
            else:
                mark, color = "  ", (75, 82, 90)
            draw.text((750, y), f"{mark:2} {index + 1}. {step}", font=self.small,
                      fill=color)
        state = "TASK SUCCESS" if self.success else "Live simulation"
        draw.text((750, 659), state, font=self.font,
                  fill=(20, 115, 65) if self.success else (55, 65, 75))
        draw.text((1070, 689), f"{elapsed:5.1f} s", font=self.small,
                  fill=(60, 68, 75))
        return frame

    def frame(self, message: Image):
        if message.encoding not in ("rgb8", "bgr8"):
            return
        now = time.monotonic()
        if self.started is None:
            self.started = now
            print("RECORDER_READY", flush=True)
        elapsed = now - self.started
        target = int(elapsed * self.fps) + 1
        if target <= self.frames:
            return
        self.update_log()
        image = PILImage.frombytes(
            "RGB", (message.width, message.height), bytes(message.data), "raw",
            "RGB" if message.encoding == "rgb8" else "BGR", message.step,
        )
        encoded = self.compose(image, elapsed).tobytes()
        for _ in range(min(target - self.frames, self.fps * 2)):
            if self.ffmpeg.poll() is not None:
                raise RuntimeError("ffmpeg exited while recording")
            self.ffmpeg.stdin.write(encoded)
            self.frames += 1

    def finish(self):
        if self.ffmpeg.stdin:
            self.ffmpeg.stdin.close()
        code = self.ffmpeg.wait(timeout=30)
        metadata = {
            "source_topic": "/overview/overview/image_raw",
            "student_id": "23020774", "P": 2, "fps": self.fps,
            "frames": self.frames, "video_seconds": round(self.frames / self.fps, 3),
            "completed_skills_seen": self.completed, "task_success_seen": self.success,
            "video": str(self.output), "ffmpeg_exit_code": code,
        }
        (self.output.with_suffix(".capture.json")).write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(metadata), flush=True)
        if code:
            raise RuntimeError("ffmpeg failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/ur3e_mssv_23020774_demo.mp4")
    parser.add_argument("--log", default="results/demo_T7_video.log")
    parser.add_argument("--stop-file", default="results/demo_video.stop")
    parser.add_argument("--fps", type=int, default=6)
    args = parser.parse_args()
    rclpy.init()
    recorder = DemoRecorder(Path(args.output), Path(args.log), Path(args.stop_file), args.fps)
    try:
        while rclpy.ok() and not recorder.stop_requested:
            rclpy.spin_once(recorder, timeout_sec=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        recorder.finish()
        recorder.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
