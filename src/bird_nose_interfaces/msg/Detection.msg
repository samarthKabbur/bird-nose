# One species identified in a sample.

std_msgs/Header header         # stamp: start of the detected call; frame_id: map
uint32 stop_index              # stop the sample was recorded at
string scientific_name         # e.g. Cardinalis cardinalis
string common_name             # e.g. Northern Cardinal
float32 confidence             # 0 to 1, as reported by the classifier
float32 start_s                # start of the call within the sample, seconds
float32 end_s                  # end of the call within the sample, seconds
geometry_msgs/Pose robot_pose  # robot pose in map during the sample
