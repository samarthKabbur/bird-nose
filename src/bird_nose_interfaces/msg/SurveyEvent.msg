# Progress of a survey: one message per event, in order.

string STARTED=started         # survey began; stop_count is set
string ARRIVED=arrived         # robot reached stop stop_index
string FAILED=failed           # Nav2 could not reach stop stop_index; detail says why
string RECORDED=recorded       # the stop's recording (or wait) finished
string FINISHED=finished       # survey ended; no more events follow

std_msgs/Header header         # stamp: when the event happened; frame_id: map
string event                   # one of the constants above
uint32 stop_index              # stop the event is about (0 for started and finished)
uint32 stop_count              # number of stops on this survey
geometry_msgs/Pose target      # the stop's goal pose in map (empty for started and finished)
string detail                  # extra information, such as Nav2's final status
