#!/usr/bin/python
# coding=utf-8
import serial, struct, sys, time
import logging

DEBUG = 1
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0


class SDS011(object):

    def __init__(self, ser, log):
        self.log = log
        self.ser = ser


    @property
    def MODE_QUERY(self):
        return 1


    def __dump(self, d, prefix=''):
        self.log.debug(prefix + d.hex())


    def __construct_command(self, cmd, data=[]):
        assert len(data) <= 12
        data += [0,]*(12-len(data))
        checksum = (sum(data)+cmd-2)%256
        ret = bytes().fromhex("aab4") + bytes([cmd])
        #ret += ''.join(chr(x) for x in data)
        ret += bytes(data)
        ret += bytes().fromhex("ffff") + bytes([checksum]) + bytes().fromhex("ab")
        self.__dump(ret, '> ')
        return ret


    def __read_response(self):
        # initialize it to something not like
        # 0xAA that is response beginning that
        # while loop will look for but neither
        # None that is what is returned at timeout
        byte = b'\xff'
        orig_timeout = self.ser.timeout
        self.ser.timeout = 5.0

        # this loop is to aligne to byte
        # that correspond to response beginning
        while byte != b'\xaa' and 0 != len(byte):
            byte = self.ser.read(size=1)
            self.log.debug('<first byte:%s:%s:%d', str(byte), str(type(byte)), len(byte))
        # restore timeout of original
        # serial instance injected in constructor
        self.ser.timeout = orig_timeout
        if 0 == len(byte):
            self.log.debug('No bytes within 5sec')
            return None
        d = self.ser.read(size=9)
        self.__dump(d, '< ')
        return byte + d


    def cmd_set_sleep(self, sleep=1):
        mode = 0 if sleep else 1
        self.log.debug('mode:%d', mode)
        self.ser.write(self.__construct_command(CMD_SLEEP, [0x1, mode]))
        self.__read_response()


    def cmd_set_mode(self, mode=1):
        self.log.debug('mode:%d', mode)
        self.ser.write(self.__construct_command(CMD_MODE, [0x1, mode]))
        self.__read_response()


    def cmd_firmware_ver(self):
        self.ser.write(self.__construct_command(CMD_FIRMWARE))
        d = self.__read_response()
        self.log.debug('fw ver byte:%s', str(d))
        self.__process_version(d)


    def __process_version(self, d):
        r = struct.unpack('<BBBHBB', d[3:])
        self.log.debug(r)
        checksum = sum(v for v in d[2:8])%256
        print("Y: {}, M: {}, D: {}, ID: {}, CRC={}".format(r[0], r[1], r[2], hex(r[3]), "OK" if (checksum==r[4] and r[5]==0xab) else "NOK"))


    def __process_data(self, d):
        r = struct.unpack('<HHxxBB', d[2:])
        pm25 = r[0]/10.0
        pm10 = r[1]/10.0

        checksum = sum(v for v in d[2:8])%256

        self.log.info("PM 2.5: {} μg/m^3  PM 10: {} μg/m^3 CRC={}".format(pm25, pm10, "OK" if (checksum==r[2] and r[3]==0xab) else "NOK"))
        if (checksum==r[2] and r[3]==0xab):
            return {'pm25': pm25, 'pm10': pm10}
        else:
            return None


    def cmd_query_data(self):
        self.ser.write(self.__construct_command(CMD_QUERY_DATA))
        d = self.__read_response()
        self.log.debug(d)
        self.log.debug(type(d[0]))
        
        if d[1] == int(b'0xc0', 16):
            return self.__process_data(d)
        else:
            self.log.error("Not executed as d[1]="+hex(d[1]))
            return None


if __name__ == "__main__":
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)15s()]::%(message)s"
    logging.basicConfig(format=FORMAT, level=DEBUG)
    log = logging.getLogger('main')
 
    ser = serial.Serial()
    ser.port = sys.argv[1]
    ser.baudrate = 9600

    ser.open()
    ser.flushInput()

    sd = SDS011(ser, log)
    try:
        sd.cmd_set_sleep(0)
        sd.cmd_set_mode(sd.MODE_QUERY)
        sd.cmd_firmware_ver()
        time.sleep(3)
        pm = sd.cmd_query_data()
        print('####'+str(pm))
    except Exception as e:
        log.exception(e)
    finally:
        sd.cmd_set_sleep(1)

    sys.exit(0)
