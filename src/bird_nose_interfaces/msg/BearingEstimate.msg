# Direction from the robot to a detected call, in the map frame.

std_msgs/Header header         # stamp: start of the call; frame_id: map
uint32 stop_index              # stop the sample was recorded at
string scientific_name         # species of the detection this bearing belongs to
float32 start_s                # time window used within the sample, seconds
float32 end_s
float32 bearing_rad            # direction in map, radians, counterclockwise from +x
float32 bearing_std_rad        # estimated standard deviation of bearing_rad, radians
geometry_msgs/Pose robot_pose  # robot pose in map during the sample (the bearing's origin)
