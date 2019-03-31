

from backend.utils import report_speed
from backend.utils import with_speed_report
from time import sleep
from datetime import timedelta

def test_report_speed():
    assert list(with_speed_report(range(10))) == list(range(10))
    assert list(with_speed_report([])) == []
    
    @report_speed(name='my_generator', report_delay=timedelta(seconds=0.1))
    def second_generator(limit):
        for elem in range(limit):
            sleep(0.01)
            yield elem
    
    assert list(second_generator(20)) == list(range(20))
    