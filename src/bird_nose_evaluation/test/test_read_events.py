"""Round trip: write survey events to an MCAP recording and read them back."""
import pytest

rosbag2_py = pytest.importorskip('rosbag2_py')
serialization = pytest.importorskip('rclpy.serialization')
interfaces = pytest.importorskip('bird_nose_interfaces.msg')


def test_events_are_read_in_order(tmp_path):
    """read_events returns the survey events written to the recording."""
    from bird_nose_evaluation.evaluate_run import read_events

    uri = str(tmp_path / 'run')
    writer = rosbag2_py.SequentialWriter()
    writer.open(rosbag2_py.StorageOptions(uri=uri, storage_id='mcap'),
                rosbag2_py.ConverterOptions('cdr', 'cdr'))
    topic = '/robot/bird_nose/survey_events'
    writer.create_topic(rosbag2_py.TopicMetadata(
        id=0, name=topic, type='bird_nose_interfaces/msg/SurveyEvent',
        serialization_format='cdr'))
    for i, kind in enumerate(['started', 'arrived', 'finished']):
        msg = interfaces.SurveyEvent(event=kind, stop_index=0, stop_count=1, detail=str(i))
        msg.header.stamp.sec = 10 * i
        writer.write(topic, serialization.serialize_message(msg), i)
    del writer

    events = read_events(uri)
    assert [e['event'] for e in events] == ['started', 'arrived', 'finished']
    assert events[2]['time_s'] == pytest.approx(20.0)
