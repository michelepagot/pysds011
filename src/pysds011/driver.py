#!/usr/bin/python
# coding=utf-8
"""
Module that implements low level communication with Nove SDS011 sensor.
"""

import struct

DEBUG = 1
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0


class SDS011(object):
    """Main driver class
    """

    def __init__(self, ser, log):
        """Constructor that just record serial and logging reference

        :param ser: serial, configured, instance
        :type ser: pyserial
        :param log: logging, configured, instance
        :type log: logging
        """
        self.log = log
        self.ser = ser

    @property
    def MODE_QUERY(self):
        return 1

    def __dump(self, d, prefix=''):
        """Dump bytes as string on the debug log channel

        :param d: bytes to dump
        :type d: bytes
        :param prefix: string to prepend, defaults to ''
        :type prefix: str, optional
        """
        if d:
            self.log.debug(prefix + d.hex())

    def __construct_command(self, cmd, data=[], dest=b'\xff\xff'):
        """
        Assemble packet to write to sensor. This function add
          - HEAD 1byte at the beginning
          - CHECKSUM + TAIL at the end
        :param cmd: Command ID
        :type cmd: int
        :param data: data to sent composed by DATA + DESTINATION 2bytes, defaults to []
        :type data: list, optional
        :param dest: 2 bytes sensor id, defaults to FF FF
        :type dest: 2 bytes
        :return: bytes array ready to be sent to the sensor
        :rtype: bytes
        """
        # all commands are 19bytes long
        #   [1:HEAD] | [1:commandID] | [cmd] | [data] | [2:DESTINATION] | [1:CHECKSUM] | [1:TAIL]
        # this method is in charge of 6 bytes
        # user needs to provide 13bytes = 1byte for cmd + some (max12) bytes for data
        assert len(data) <= 12
        self.log.debug("data:" + str(data) + " dest:" + str(dest))
        # feel not provided data with zero
        data += [0, ]*(12-len(data))
        self.log.debug("Resized data:" + str(data))
        # calculate the checksum: TODO has the dest to be included?
        checksum = (sum(data)+sum(struct.unpack('<BB', dest))+cmd) % 256
        # head:AA  CommandID:B4 --> are common to all PC->Sensor commands
        ret = bytes().fromhex("aab4")  # head
        ret += bytes([cmd])
        ret += bytes(data)
        ret += dest
        ret += bytes([checksum])
        ret += bytes().fromhex("ab")  # tail
        self.__dump(ret, '> ')
        return ret

    def __read_response(self):
        """Read data from the sensor

        :return: read bytes
        :rtype: bytes or None in case of error
        """
        # initialize it to something not like 0xAA
        # as 0xAA is the response beginning that we are looking for.
        # None is not a good value for this dummy initialization as
        # None is the value returned in case of timeout
        byte = b'\xff'
        orig_timeout = self.ser.timeout
        self.ser.timeout = 5.0
        max_driver_reply_len = 20

        # this loop is to aligne to byte
        # that correspond to response beginning
        while byte is not None and byte != b'\xaa' and 0 != len(byte) and max_driver_reply_len > 0:
            max_driver_reply_len -= 1
            byte = self.ser.read(size=1)
            if byte is not None:
                self.log.debug('<first byte:%s:%s:%d', str(byte), str(type(byte)), len(byte))
        # restore timeout of original
        # serial instance injected in constructor
        self.ser.timeout = orig_timeout
        if max_driver_reply_len == 0:
            self.log.error('Not get HEAD after 20 read bytes')
            return None
        if byte is None or 0 == len(byte):
            self.log.debug('No bytes within 5sec')
            return None
        d = self.ser.read(size=9)
        if d is None:
            self.log.error('Timeout reading body')
            return None

        checksum = sum(v for v in d[1:-2]) % 256
        if checksum != d[-2]:
            self.log.error('Wrong rep checksum: expected ' + str(checksum) + ' and get ' + str(d[-2]))
            return None
        # if b'\xab' != d[-1]: # commented as it always result True
        #    self.log.error('Wrong TAIL ' + str(d[-1]))
        #    return None
        self.__dump(d, '< ')
        return byte + d

    def __response_checksum(self, data):
        return sum(v for v in data[2:8]) % 256

    def __process_version(self, d):
        """Get bytes and validate them and eventually return a version dictionary

        :param d: input raw bytes from the sensor
        :type d: bytes
        :return: version dictionary or None if error
        :rtype: dict
        """
        if d is None:
            self.log.error("Empty data for version")
            return
        # Expected response is like
        # |  AA  |  C5  |   7   | YEAR | MONTH | DAY | DevID1 | DevID2 | CHECKSUM |  AB  |
        #  head   cmdID  cmdVER |       ------response------           |          | TAIL |
        # < : little endian
        # B : unsigned char
        # H : unsigned short
        r = struct.unpack('<BBBBBBB', d[3:])
        self.log.debug(r)
        checksum = self.__response_checksum(d)
        if checksum != r[5]:
            self.log.error('Checksum error')
            return None
        if r[6] != 0xab:
            self.log.error('Tail error')
            return None
        res = dict()
        res['year'] = r[0]
        res['month'] = r[1]
        res['day'] = r[2]
        # how many square brakets on the right side
        # of the next line :-)
        # r[3] is an integer and bytes accept both
        #  bytest(int) and bytes([])
        # but bytes(int) means gimme an int long bytes array
        # and bytes([]) means tlaslate int array to bytes array
        # so bytes([r[3]]) means : gimmi a byte array with one element of value r[3]
        res['id'] = bytes([r[3], r[4]])
        res['pretty'] = "Y: {}, M: {}, D: {}, ID: {}".format(r[0], r[1], r[2], ''.join('%02x' % i for i in res['id']))

        return res

    def __process_data(self, d):
        if d[1] != int(b'0xc0', 16):
            self.log.error("Not executed as d[1]="+hex(d[1]))
            return None
        checksum = self.__response_checksum(d)

        r = struct.unpack('<HHxxBB', d[2:])
        if checksum != r[2]:
            self.log.error("Checksum error")
            return None

        if r[3] != 0xab:
            self.log.error("Wrong tail")
            return None
        pm25 = r[0]/10.0
        pm10 = r[1]/10.0
        res_str = "PM 2.5: {} μg/m^3  PM 10: {} μg/m^3".format(pm25, pm10)
        return {'pm25': pm25, 'pm10': pm10, 'pretty': res_str}

    def cmd_get_sleep(self,  id=b'\xff\xff'):
        """Get active sleep mode

        Take care that sensor will not response to it if it is sleeping. So mainly
        this API will return 0 or None. None could means:
        - I'm sleeping, so I cannot reply
        - I'm not sleeping but something went wrong as responding

        :param id: sensor id to request sleep status, defaults to b'\xff\xff' that is 'all'
        :type id: 2 bytes, optional
        :return: True if it is sleeping, False if wakeup, None in case of communication error
        :rtype: bool
        """
        self.ser.write(self.__construct_command(CMD_SLEEP, [0x0, 0x0], id))
        resp = self.__read_response()
        if resp is None:
            self.log.error("No sensor response")
            return None
        if 0 != resp[4] and 1 != resp[4]:
            self.log.error("No valid sensor response %d", resp[4])
            return None
        return 0 == resp[4]

    def cmd_set_sleep(self, sleep=1, id=b'\xff\xff'):
        """Set sleep mode

        :param sleep: 1:enable sleep mode, 0:wakeup, defaults to 1
        :type sleep: int, optional
        :param id: sensor id to request mode, defaults to b'\xff\xff' that is 'all'
        :type id: 2 bytes, optional
        :return: True is set is ok
        :rtype: bool
        """
        assert id is not None
        self.log.debug('is:%s', str(id))
        mode = 0 if sleep else 1
        self.log.debug('driver mode:%d', mode)
        self.ser.write(self.__construct_command(CMD_SLEEP, [0x1, mode], id))
        resp = self.__read_response()
        return resp is not None

    def cmd_get_mode(self, id=b'\xff\xff'):
        """Get active reporting mode

        :param id: sensor id to request mode, defaults to b'\xff\xff' that is 'all'
        :type id: 2 bytes, optional
        :return: mode if it is ok, None if error
        :rtype: int
        """
        assert id is not None
        self.ser.write(self.__construct_command(CMD_MODE, [0x0, 0x0], id))
        resp = self.__read_response()
        if resp is None:
            self.log.error("No valid sensor response")
            return None
        return resp[4]

    def cmd_set_mode(self, mode=1, id=b'\xff\xff'):
        """Set data reporting mode. The setting is still effective after power off

        :param mode: 0：report active mode  1：report query mode, defaults to 1
        :type mode: int, optional
        :param id: sensor id to request mode, defaults to b'\xff\xff' that is 'all'
        :type id: 2 bytes, optional
        :return: True is set is ok
        :rtype: bool
        """
        assert id is not None
        self.log.debug('mode:%d', mode)
        self.ser.write(self.__construct_command(CMD_MODE, [0x1, mode], id))
        resp = self.__read_response()
        if resp is None:
            self.log.error("No valid sensor response")
            return False
        if mode != resp[4]:
            self.log.error("Requested configuration not applied")
            return False
        return True

    def cmd_firmware_ver(self, id=b'\xff\xff'):
        """Get FW version

        :return: version description dictionary  or None if error
                 with fields: 'year', 'month', 'day', 'id', 'pretty'
        :rtype: dict
        """
        assert id is not None
        # 7: CMD_FIRMWARE: not needs any PC->Sensor data
        self.ser.write(self.__construct_command(7, dest=id))
        d = self.__read_response()
        self.log.debug('fw ver byte:%s', str(d))
        return self.__process_version(d)

    def cmd_query_data(self, id=b'\xff\xff'):
        """Read dust values from the sensor

        :param id: Sensor ID, defaults to b'\xff\xff'
        :type id: 2 bytes, optional
        :return: dust data as dictionary
        :rtype: dict
        """
        assert id is not None
        self.ser.write(self.__construct_command(CMD_QUERY_DATA, dest=id))
        d = self.__read_response()
        self.log.debug(d)
        if d is None:
            self.log.error("No data from query")
            return None

        return self.__process_data(d)

    def cmd_set_id(self, id, new_id):
        """Set a device ID to a specific sensor

        :param id: ID of sensor that need a new ID (FF FF is in theory allowed too, but be carefull)
        :type id: 2 bytes
        :param new_id: new ID to be assigned
        :type new_id: 2 bytes
        :return: operation result
        :rtype: bool
        """
        assert id is not None
        assert new_id is not None

        self.ser.write(self.__construct_command(CMD_DEVICE_ID, [0, ]*10 + [new_id[0], new_id[1]], id))
        d = self.__read_response()
        if d is None:
            self.log.error("Error in sensor response")
            return False
        self.log.debug(d[-4:-2])
        if d[-4] == new_id[0] and d[-3] == new_id[1]:
            return True
        return False

    def cmd_set_working_period(self, period=0, id=b'\xff\xff'):
        """Set working period
           The setting is still effective after power off,
           factory default is continuous measurement.
           The sensor works periodically and reports the latest data.

        :param period: 0：continuous(default), 1-30 minute work 30 seconds and sleep n*60-30 seconds
        :type period: int
        :return: result
        :rtype: bool
        """
        assert id is not None
        if period > 30:
            return False
        self.ser.write(self.__construct_command(CMD_WORKING_PERIOD, [0x01, period], id))

        return True

    def cmd_get_working_period(self, id=b'\xff\xff'):
        """Get current working period

        :return: working period in minutes: work 30 seconds and sleep n*60-30 seconds
        :rtype: int
        """
        assert id is not None
        self.ser.write(self.__construct_command(CMD_WORKING_PERIOD, [0x00], id))
        d = self.__read_response()
        if d is None:
            self.log.error("Error in sensor response")
            return None
        self.log.debug(d)
        return d[4]
