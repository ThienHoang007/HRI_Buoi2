import os
os.environ['ROS_DOMAIN_ID']='42'
import rclpy
from gazebo_msgs.msg import LinkStates
rclpy.init()
node=rclpy.create_node('diagnose_links')
def callback(msg):
    print('\n'.join(msg.name),flush=True)
    raise SystemExit(0)
node.create_subscription(LinkStates,'/gazebo/link_states',callback,10)
rclpy.spin(node)
