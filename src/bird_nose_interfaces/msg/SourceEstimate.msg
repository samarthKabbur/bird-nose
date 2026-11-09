# Where calls of one species are estimated to come from.
# A candidate location, not a confirmed nest.

string scientific_name         # species
geometry_msgs/Point position   # in map, metres; z is 0 in version 1 (ground plane only)
float64[4] covariance_xy       # 2x2 position covariance, row-major, square metres
uint32 num_bearings            # bearings combined into this estimate
