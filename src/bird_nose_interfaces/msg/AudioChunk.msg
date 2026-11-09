# A short block of audio from every channel of the microphone array.
# Published about every 100 ms. Samples are interleaved by frame:
# data = [f0c0, f0c1, ..., f0c(N-1), f1c0, f1c1, ...].

std_msgs/Header header  # stamp: time of the first frame; frame_id: the array's frame
uint32 sample_rate      # frames per second, e.g. 48000
uint16 channels         # number of channels N
int16[] data            # 16-bit signed samples, interleaved; length = N * frames
