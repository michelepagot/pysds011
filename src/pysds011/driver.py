# coding=utf-8
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
        if d:
            self.log.debug(prefix + d.hex())

    def __construct_command(self, cmd, data=[]):
        # all commands are 19bytes long
        #   [1:HEAD] | [1:commandID] | [cmd] | [data] | [2:DESTINATION] | [1:CHECKSUM] | [1:TAIL]
        # this method is in charge of 6 bytes
        # user needs to provide 13bytes = 1byte for cmd + some (max12) bytes for data
        assert len(data) <= 12
        # feel not provided data with zero
        data += [0, ]*(12-len(data))
        # calculate the checksum
        checksum = (sum(data)+cmd-2) % 256
        # head:AA  CommandID:B4 --> are common to all PC->Sensor commands
        ret = bytes().fromhex("aab4")
        ret += bytes([cmd])
        ret += bytes(data)
        # FF FF means "Al sensors response"
        ret += bytes().fromhex("ffff")
        ret += bytes([checksum])
        # tail
        ret += bytes().fromhex("ab")
        self.__dump(ret, '> ')
        return ret

    def __read_response(self):
        # initialize it to something not like 0xAA
        # as 0xAA is the response beginning that we are looking for.
        # None is not a good value for this dummy initialization as
        # None is the value returned in case of timeout
        byte = b'\xff'
        orig_timeout = self.ser.timeout
        self.ser.timeout = 5.0

        # this loop is to aligne to byte
        # that correspond to response beginning
        while byte is not None and byte != b'\xaa' and 0 != len(byte):
            byte = self.ser.read(size=1)
            if byte is not None:
                self.log.debug('<first byte:%s:%s:%d', str(byte), str(type(byte)), len(byte))
        # restore timeout of original
        # serial instance injected in constructor
        self.ser.timeout = orig_timeout
        if  byte is None or 0 == len(byte):
            self.log.debug('No bytes within 5sec')
            return None
        d = self.ser.read(size=9)
        if d is None:
            self.log.error('Timeout reading body')
            return None
        self.__dump(d, '< ')
        return byte + d

    def __response_checksum(self, data):
        return sum(v for v in data[2:8])%256

    def __process_version(self, d):
        if d is None:
            self.log.error("Empty data for version")
            return
        # Expected response is like
        # |  AA  |  C5  |   7   | YEAR | MONTH | DAY | DevID1 | DevID2 | CHECKSUM |  AB  |
        #  head   cmdID  cmdVER |       ------response------           |          | TAIL |
        # < : little endian
        # B : unsigned char
        # H : unsigned short
        r = struct.unpack('<BBBHBB', d[3:])
        self.log.debug(r)
        checksum = self.__response_checksum(d)
        return "Y: {}, M: {}, D: {}, ID: {}, CRC={}".format(r[0], r[1], r[2], hex(r[3]), "OK" if (checksum==r[4] and r[5]==0xab) else "NOK")

    def __process_data(self, d):
        r = struct.unpack('<HHxxBB', d[2:])
        pm25 = r[0]/10.0
        pm10 = r[1]/10.0

        checksum = self.__response_checksum(d)

        res_str = "PM 2.5: {} μg/m^3  PM 10: {} μg/m^3 CRC={}".format(pm25, pm10, "OK" if (checksum==r[2] and r[3]==0xab) else "NOK")
        if (checksum==r[2] and r[3]==0xab):
            return {'pm25': pm25, 'pm10': pm10, 'pretty': res_str}
        else:
            return None

    def cmd_get_sleep(self):
        """Get active sleep mode

        :return: True if it is sleeping
        :rtype: bool
        """
        self.ser.write(self.__construct_command(CMD_SLEEP, [0x0, 0x0]))
        return True


    def cmd_set_sleep(self, sleep=1):
        """Set sleep mode

        :param sleep: 1:enable sleep mode, 0:wakeup, defaults to 1
        :type sleep: int, optional
        :return: True is set is ok
        :rtype: bool
        """
        mode = 0 if sleep else 1
        self.log.debug('mode:%d', mode)
        self.ser.write(self.__construct_command(CMD_SLEEP, [0x1, mode]))
        resp = self.__read_response()
        return resp is not None

    def cmd_set_mode(self, mode=1):
        self.log.debug('mode:%d', mode)
        self.ser.write(self.__construct_command(CMD_MODE, [0x1, mode]))
        self.__read_response()

    def cmd_firmware_ver(self):
        """Get FW version

        :return: version description string
        :rtype: string
        """
        # 7: CMD_FIRMWARE: not needs any PC->Sensor data
        self.ser.write(self.__construct_command(7))
        d = self.__read_response()
        self.log.debug('fw ver byte:%s', str(d))
        return self.__process_version(d)

    def cmd_query_data(self):
        self.ser.write(self.__construct_command(CMD_QUERY_DATA))
        d = self.__read_response()
        self.log.debug(d)
        if d is None:
            self.log.error("No data from query")
            return None
        self.log.debug(type(d[0]))

        if d[1] == int(b'0xc0', 16):
            return self.__process_data(d)
        else:
            self.log.error("Not executed as d[1]="+hex(d[1]))
            return None
