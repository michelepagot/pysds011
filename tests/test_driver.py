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
def compose_write(data, id):
    CHECKSUM = bytes([sum(data+id)%256])
    DRIVER_WRITE = HEAD + CMD_ID + data + id + CHECKSUM + TAIL
    return DRIVER_WRITE


def compose_response(data):
    CHECKSUM_RSP = bytes([sum(data)%256])
    return RSP_ID+data+CHECKSUM_RSP+TAIL


def test_cmd_set_sleep(mocker):
    """
    Test correctly processed set sleep command:
    Send command, set all connected sensors to sleep
    Sensor with ID ABCD confirm
    """
    ##################
    #   EXPECTATION
    ##################

    # create an artificial for test purpose Serial object
    # it will let the test code to:
    #   - check what driver will write to sensor
    #   - decide (simulate) what sensor replay to the driver
    sm = SerialMock()
    log = logging.getLogger("SDS011")

    # this is what driver (code under test) is expected to send to the sensor
    # prepared here but checked later
    DATA  = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID  = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    # this is to simulate sensor response
    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x06\x01\x00\x00'
    SENSOR_ID_RSP = b'\xab\xcd'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert True == d.cmd_set_sleep()

    ##################
    #   VERIFICATION
    ##################

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_docexample1(mocker):
    """
    Test correctly processed set sleep command
    Send command, set the sensor with ID A160 to sleep
    AA B4 06 01 00 00 00 00 00 00 00 00 00 00 00 A1 60 08 AB
    Sensor with ID A160 response:
    AA C5 06 01 00 00 A1 60 08 AB
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA  = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID  = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)

    DATA_RSP = b'\x06\x01\x00\x00'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert True == d.cmd_set_sleep(id=SENSOR_ID_RSP)

    ##################
    #   VERIFICATION
    ##################
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_docexample2(mocker):
    """
    Test correctly processed set sleep command
    Send command, set the sensor with ID A160 to sleep
    AA B4 06 01 01 00 00 00 00 00 00 00 00 00 00 A1 60 09 AB
    Sensor with ID A160 response:
    AA C5 06 01 01 00 A1 60 09 AB
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA  = b'\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID  = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)

    DATA_RSP = b'\x06\x01\x01\x00'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert True == d.cmd_set_sleep(sleep=0, id=SENSOR_ID_RSP)

    ##################
    #   VERIFICATION
    ##################
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_wakeup(mocker):
    """
    Test correctly processed set sleep command
    in wakeup mode
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA  = b'\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID  = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x06\x01\x01\x00'
    SENSOR_ID_RSP = b'\xab\xcd'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert True == d.cmd_set_sleep(0)

    ##################
    #   VERIFICATION
    ##################

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_no_replay(mocker):
    """
    Test situation where sensor does not replay to sleep request
    """
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    d = SDS011(sm, log)
    # calls the sleep driver but without to programm reply from serial
    assert False == d.cmd_set_sleep()


def test_cmd_set_sleep_read_delayed(mocker):
    """
    Check driver mechanism that look for initial sensor respons
    """
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(b'\xff')
    sm.test_expect_read(b'\xff')
    sm.test_expect_read(b'\xff')
    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x06\x01\x00\x00'
    SENSOR_ID_RSP = b'\xab\xcd'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    d = SDS011(sm, log)
    assert True == d.cmd_set_sleep()


def test_cmd_set_sleep_malformed(mocker):
    """
    Check driver behavior is no valid data comes
    from sensor for many time (more than max possible read size)
    """
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    for _ in range(30):
        sm.test_expect_read(b'\xff')
    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()
    # also check that driver stop before to read 30 bytes (should stop at 20 bytes)
    remaining_not_requested_byte =  sm.read(1)
    assert remaining_not_requested_byte is not None


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


def test_cmd_set_sleep_wrong_checksum(mocker):
    """
    Test correctly processed set sleep command
    """
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)
    DATA_RSP =  b'\x06\x01\x00\x00\xab\xcd'
    CHECKSUM_RSP = bytes([sum(DATA_RSP)%256 + 1])
    sm.test_expect_read(RSP_ID+DATA_RSP+CHECKSUM_RSP+TAIL)
    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()


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
