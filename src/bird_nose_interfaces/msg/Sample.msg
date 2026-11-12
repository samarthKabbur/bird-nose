# One recording made at a survey stop. The audio is a WAV file on disk,
# because 30 s of multichannel audio is too large for one message.

std_msgs/Header header         # stamp: start of the recording; frame_id: map
uint32 stop_index              # stop number on this survey, from 0
float32 duration_s             # length of the recording, seconds
geometry_msgs/Pose robot_pose  # robot pose in map while recording (the robot is stopped)
string wav_path                # absolute path of the WAV file
uint32 sample_rate             # frames per second
uint16 channels                # number of channels in the WAV file
