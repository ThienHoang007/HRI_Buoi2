"""Explicit recovery after a stopped integration test; no object repositioning."""
import os
import sys
from pathlib import Path
import threading
os.environ['ROS_DOMAIN_ID']='42'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/ur3_llm_control'))
import rclpy
from rclpy.executors import MultiThreadedExecutor
from ur3_llm_control.robot_skills import RobotSkills
rclpy.init(); node=RobotSkills(); executor=MultiThreadedExecutor(); executor.add_node(node)
thread=threading.Thread(target=executor.spin,daemon=True); thread.start()
try:
    node.switch(sys.argv[1],False)
    node.attach_scene(sys.argv[1],False)
    node.ready()
    node.home()
    print('RECOVERY SUCCESS',flush=True)
finally:
    executor.shutdown(); thread.join(); node.destroy_node(); rclpy.shutdown()
