from pysds011.driver import SDS011
import logging

def test_create():
    d = SDS011(None, None)
    assert d is not None


def test_cmd_set_sleep(mocker):
    class SerialMock(object):
        def __init__(self):
            self.__write_reg = list()
            self.__read_reg = list()
            self.timeout = 0

        def write(self, data):
            self.__write_reg.append(data)

        def read(self, size):
            return self.__read_reg.pop() if self.__read_reg else None

        def expect_read(self, data):
            self.__read_reg.append(data)

    log = logging.getLogger("SDS011")
    sm = SerialMock()
    d = SDS011(sm, log)
    d.cmd_set_sleep()

