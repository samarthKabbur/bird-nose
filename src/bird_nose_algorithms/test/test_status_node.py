from bird_nose_algorithms.status_node import status_text


def test_status_text_counts():
    assert status_text(3) == 'bird_nose_algorithms alive (3)'
