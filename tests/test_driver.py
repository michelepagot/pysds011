from pysds011.driver import SDS011
import logging


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
        self.__read_reg.append({'size': len(data), 'data': data})

    def test_get_write(self):
        return self.__write_reg


HEAD   = b'\xaa'
CMD_ID = b'\xb4'
RSP_ID = b'\xc5'
TAIL   = b'\xab'


def compose_write(data, id):
    CHECKSUM = bytes([sum(data+id) % 256])
    DRIVER_WRITE = HEAD + CMD_ID + data + id + CHECKSUM + TAIL
    return DRIVER_WRITE


def compose_response(data, rsp=RSP_ID):
    CHECKSUM_RSP = bytes([sum(data) % 256])
    return rsp+data+CHECKSUM_RSP+TAIL


def test_create():
    d = SDS011(None, None)
    assert d is not None


def test_cmd_set_mode():
    """
    Test set data reporting mode: 'active mode'
    """
    ##################
    #   EXPECTATION
    ##################

    # create an artificial, for test purpose, Serial object
    # it will let the test code to:
    #   - check what driver will write to sensor
    #   - decide (simulate) what sensor replay to the driver
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    # this is what driver (code under test) is expected to send to the sensor
    # prepared here but checked later
    DATA = b'\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    # this is to simulate sensor response
    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x02\x01\x00\x00'
    SENSOR_ID_RSP = b'\xab\xcd'  # simulate that sensor response come from sensor with ABCD id
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_mode(0)

    ##################
    #   VERIFICATION
    ##################

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_mode_sensornotapplied():
    """
    Test set data reporting mode
    but in sensor reply the mode is not what requested
    """
    ##################
    #   EXPECTATION
    ##################

    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    # this is to simulate sensor response
    sm.test_expect_read(HEAD)
    # driver set 0 but sensor replay 1 (3rd byte)
    DATA_RSP = b'\x02\x01\x01\x00'
    SENSOR_ID_RSP = b'\xab\xcd'  # simulate that sensor response come from sensor with ABCD id
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert False == d.cmd_set_mode(0)

    ##################
    #   VERIFICATION
    ##################

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_mode_docexample():
    """
    Test set data reporting mode
    example from the datasheet
    """
    ##################
    #   EXPECTATION
    ##################

    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    # this is to simulate sensor response
    sm.test_expect_read(HEAD)
    # driver set 0 but sensor replay 1 (3rd byte)
    DATA_RSP = b'\x02\x01\x01\x00'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_mode(1, SENSOR_ID)

    ##################
    #   VERIFICATION
    ##################

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_get_mode_active():
    """
    Test get data reporting mode: 'active mode'
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x02\x00\x00\x00'
    SENSOR_ID_RSP = b'\xab\xcd'  # simulate that sensor response come from sensor with ABCD id
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert 0 == d.cmd_get_mode()

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_get_mode_query():
    """
    Test get data reporting mode: 'query mode'
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x02\x00\x01\x00'
    SENSOR_ID_RSP = b'\xab\xcd'  # simulate that sensor response come from sensor with ABCD id
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert 1 == d.cmd_get_mode()

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep():
    """
    Test correctly processed set sleep command:
    Send command, set all connected sensors to sleep
    Sensor with ID ABCD confirm
    """
    ##################
    #   EXPECTATION
    ##################

    sm = SerialMock()
    log = logging.getLogger("SDS011")

    DATA = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x06\x01\x00\x00'
    SENSOR_ID_RSP = b'\xab\xcd'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_sleep()

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_docexample1():
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

    DATA = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)

    DATA_RSP = b'\x06\x01\x00\x00'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_sleep(id=SENSOR_ID_RSP)

    ##################
    #   VERIFICATION
    ##################
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_docexample2():
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

    DATA = b'\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)

    DATA_RSP = b'\x06\x01\x01\x00'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_sleep(sleep=0, id=SENSOR_ID_RSP)

    ##################
    #   VERIFICATION
    ##################
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_wakeup():
    """
    Test correctly processed set sleep command
    in wakeup mode
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x06\x01\x01\x00'
    SENSOR_ID_RSP = b'\xab\xcd'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_sleep(0)

    ##################
    #   VERIFICATION
    ##################

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_sleep_no_replay():
    """
    Test situation where sensor does not replay to sleep request
    """
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    d = SDS011(sm, log)
    # calls the sleep driver but without to programm reply from serial
    assert False == d.cmd_set_sleep()


def test_cmd_set_sleep_read_delayed():
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
    assert d.cmd_set_sleep()


def test_cmd_set_sleep_malformed():
    """
    Check driver behavior if no valid data comes
    from sensor for many time (more than max possible read size)
    """
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    for _ in range(30):
        sm.test_expect_read(b'\xff')
    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()
    # also check that driver stop before to read 30 bytes (should stop at 20 bytes)
    remaining_not_requested_byte = sm.read(1)
    assert remaining_not_requested_byte is not None


def test_cmd_set_sleep_get_only_head():
    """
    Test driver behavior if sensor only sends HEAD
    and nothing more
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)

    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA = b'\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA) % 256])
    assert HEAD + CMD_ID + DATA + CHECKSUM + TAIL == production_code_write_to_sensor[0]


def test_cmd_set_sleep_wrong_checksum():
    """
    Test correctly processed set sleep command
    """
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x06\x01\x00\x00\xab\xcd'
    CHECKSUM_RSP = bytes([sum(DATA_RSP) % 256 + 1])
    sm.test_expect_read(RSP_ID+DATA_RSP+CHECKSUM_RSP+TAIL)
    d = SDS011(sm, log)
    assert False == d.cmd_set_sleep()


def test_cmd_get_sleep():
    """
    Test correctly processed get sleep command
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()
    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x06\x00\x00\x00\xab\xcd'
    CHECKSUM_RSP = bytes([sum(DATA_RSP) % 256])
    sm.test_expect_read(RSP_ID+DATA_RSP+CHECKSUM_RSP+TAIL)
    d = SDS011(sm, log)
    assert 1 == d.cmd_get_sleep()

    # check expectation about what driver should sent to sensor
    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    DATA = b'\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'
    CHECKSUM = bytes([sum(DATA) % 256])
    assert HEAD + CMD_ID + DATA + CHECKSUM + TAIL == production_code_write_to_sensor[0]


def test_cmd_query_data():
    """
    Test query data
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\xd4\x04\x3a\x0a'
    SENSOR_ID_RSP = b'\xab\xcd'  # simulate that sensor response come from sensor with ABCD id
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP, rsp=b'\xc0'))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    resp = d.cmd_query_data()

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]
    assert resp is not None
    assert 123.6 == resp['pm25']
    assert 261.8 == resp['pm10']
    assert 'pretty' in resp.keys()


def test_cmd_set_device_id():
    """
    Test set device ID API
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    # New device ID [EF FE]
    NEW_ID = b'\xef\xfe'
    DATA = b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + NEW_ID
    SENSOR_ID = b'\xab\xcd'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x05\x00\x00\x00'
    SENSOR_ID_RSP = NEW_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_id(id=SENSOR_ID, new_id=NEW_ID)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_device_id_wrongidinreplay():
    """
    Test set device ID API: id in replay
    is not the same of new_id
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    # New device ID [EF FE]
    NEW_ID = b'\xef\xfe'
    DATA = b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + NEW_ID
    SENSOR_ID = b'\xab\xcd'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x05\x00\x00\x00'
    SENSOR_ID_RSP = b'\xdd\xdd'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert False == d.cmd_set_id(id=SENSOR_ID, new_id=NEW_ID)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_device_id_wrongchecksum():
    """
    Test set device ID API: id in replay
    is not the same of new_id
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    # New device ID [EF FE]
    NEW_ID = b'\xef\xfe'
    DATA = b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + NEW_ID
    SENSOR_ID = b'\xab\xcd'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x05\x00\x00\x00' + NEW_ID
    CHECKSUM_RSP = bytes([sum(DATA_RSP) % 256 + 1])
    sm.test_expect_read(RSP_ID+DATA_RSP+CHECKSUM_RSP+TAIL)

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert False == d.cmd_set_id(id=SENSOR_ID, new_id=NEW_ID)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_device_id_docexample():
    """
    Test set device ID API: example from datasheet
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    # New device ID [EF FE]
    NEW_ID = b'\xa0\x01'
    DATA = b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + NEW_ID
    SENSOR_ID = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x05\x00\x00\x00'
    SENSOR_ID_RSP = NEW_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_id(id=SENSOR_ID, new_id=NEW_ID)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_working_period_continuous():
    """
    Test set working period API
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x08\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x08\x01\x00\x00'
    SENSOR_ID_RSP = b'\xAB\xCD'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_working_period(0)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_working_period_maxnallowed():
    """
    Test set working period: set to 30min
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    # 0x1E : 30
    DATA = b'\x08\x01\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x08\x01\x1e\x00'
    SENSOR_ID_RSP = b'\xAB\xCD'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_working_period(30)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_set_working_period_morethanallowed():
    """
    Test set working period: set to 31min
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert False == d.cmd_set_working_period(31)

    ##################
    #   VERIFICATION
    ##################
    writes = sm.test_get_write()
    assert 0 == len(writes)


def test_cmd_set_working_period_docexample():
    """
    Test set working period API: example from datasheet
    Send command to set the working period of sensor with ID A160 to 1 minute
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x08\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x08\x01\x01\x00'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert d.cmd_set_working_period(1, id=SENSOR_ID)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_get_working_period():
    """
    Test get working period API
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x08\x00\x00\x00'
    SENSOR_ID_RSP = b'\xAB\xCD'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert 0 == d.cmd_get_working_period()

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_get_working_period_docexample():
    """
    Test get working period API example from datasheet
    Send command to query the working period of the sensor with ID A160
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xa1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x08\x00\x02\x00'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    assert 2 == d.cmd_get_working_period(id=SENSOR_ID)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]


def test_cmd_get_firmware_version():
    """
    Test get firmware version API
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xff\xff'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x07\x01\x02\x03'
    SENSOR_ID_RSP = b'\xAB\xCD'
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    res = d.cmd_firmware_ver()

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]
    assert 'year' in res.keys()
    assert 1 == res['year']
    assert 'month' in res.keys()
    assert 2 == res['month']
    assert 'day' in res.keys()
    assert 3 == res['day']
    assert 'pretty' in res.keys()


def test_cmd_get_firmware_version_docexample():
    """
    Test get firmware version API
    """
    ##################
    #   EXPECTATION
    ##################
    log = logging.getLogger("SDS011")
    sm = SerialMock()

    DATA = b'\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    SENSOR_ID = b'\xA1\x60'
    EXPECTED_DRIVER_WRITE = compose_write(DATA, SENSOR_ID)

    sm.test_expect_read(HEAD)
    DATA_RSP = b'\x07\x0f\x07\x0a'
    SENSOR_ID_RSP = SENSOR_ID
    sm.test_expect_read(compose_response(DATA_RSP + SENSOR_ID_RSP))

    ##################
    #   TEST EXEC
    ##################
    d = SDS011(sm, log)
    res = d.cmd_firmware_ver(id=SENSOR_ID)

    ##################
    #   VERIFICATION
    ##################

    production_code_write_to_sensor = sm.test_get_write()
    assert 1 == len(production_code_write_to_sensor)
    assert EXPECTED_DRIVER_WRITE == production_code_write_to_sensor[0]
    assert 'year' in res.keys()
    assert 15 == res['year']
    assert 'month' in res.keys()
    assert 7 == res['month']
    assert 'day' in res.keys()
    assert 10 == res['day']
    assert 'pretty' in res.keys()
