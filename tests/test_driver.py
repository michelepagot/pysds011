from pysds011.driver import SDS011
import logging

def test_create():
    d = SDS011(None, None)
    assert d is not None

class SerialMock(object):
    def __init__(self):
        self.__write_reg = list()
        self.__read_reg = list()
        self.timeout = 0

    def write(self, data):
        self.__write_reg.append(data)

    def read(self, size):
        if self.__read_reg:
            frame = self.__read_reg.pop(0)
            assert size == frame['size']
            return frame['data']
        else:
            return None

    def test_expect_read(self, data):
        self.__read_reg.append({'size' : len(data), 'data': data})

    def test_get_write(self):
        return self.__write_reg

HEAD   = b'\xaa'
CMD_ID = b'\xb4'
RSP_ID = b'\xc5'
TAIL   = b'\xab'

def test_cmd_set_sleep(mocker):
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)
    DATA_RSP =  b'\x06\x01\x00\x00\xab\xcd'
    CHECKSUM_RSP = bytes([sum(DATA_RSP)%256])
    sm.test_expect_read(RSP_ID+DATA_RSP+CHECKSUM_RSP+TAIL)
    d = SDS011(sm, log)
    assert True == d.cmd_set_sleep()

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA   = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA)%256])
    assert HEAD + CMD_ID + DATA+ CHECKSUM + TAIL == production_code_write_to_sensor[0]

def test_cmd_set_sleep_wakeup(mocker):
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)
    DATA_RSP =  b'\x06\x01\x01\x00\xab\xcd'
    CHECKSUM_RSP = bytes([sum(DATA_RSP)%256])
    sm.test_expect_read(RSP_ID+DATA_RSP+CHECKSUM_RSP+TAIL)
    d = SDS011(sm, log)
    assert True == d.cmd_set_sleep(0)

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA   = b'\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA)%256])
    assert HEAD + CMD_ID + DATA+ CHECKSUM + TAIL == production_code_write_to_sensor[0]


def test_cmd_set_sleep_no_replay(mocker):
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()

    # check expectation about what driver should sent to sensor
    # driver is expected to write to sensor as it happens before than
    # sensor replay with malformed data
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA   = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA)%256])
    assert HEAD + CMD_ID + DATA+ CHECKSUM + TAIL == production_code_write_to_sensor[0]


def test_cmd_set_sleep_read_malformed_data(mocker):
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(b'\xff\xff\xff\xff')
    sm.test_expect_read(b'\x11\x11')

    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA   = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA)%256])
    assert HEAD + CMD_ID + DATA+ CHECKSUM + TAIL == production_code_write_to_sensor[0]


def test_cmd_set_sleep_get_only_head(mocker):
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)

    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA   = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA)%256])
    assert HEAD + CMD_ID + DATA+ CHECKSUM + TAIL == production_code_write_to_sensor[0]

def test_cmd_get_sleep(mocker):
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)
    DATA_RSP =  b'\x06\x00\x00\x00\xab\xcd'
    CHECKSUM_RSP = bytes([sum(DATA_RSP)%256])
    sm.test_expect_read(RSP_ID+DATA_RSP+CHECKSUM_RSP+TAIL)
    d = SDS011(sm, log)
    assert 1 == d.cmd_get_sleep()

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA   = b'\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA)%256])
    assert HEAD + CMD_ID + DATA+ CHECKSUM + TAIL == production_code_write_to_sensor[0]
