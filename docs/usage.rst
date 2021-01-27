=====
Usage
=====

Use the package in a python script
==================================
To use pysds011 in a project, start by importing this package::

	import pysds011

Provide an UART channel, user is in charge to also ``open/close`` it::

    import serial

    ser = serial.Serial('/dev/ttyUSB0', 9600)
    ser.open()

Provide a logger::

    import logging

    log = logging.getLogger(__name__)

Now create a driver instance, injecting serial and logging::

    sd = driver.SDS011(ser, log)

Usually the first step is to wake up the sensor::

    sd.cmd_set_sleep(0)

Then start to interact with it::

    sd.cmd_set_mode(sd.MODE_QUERY)
    fw_ver = sd.cmd_firmware_ver()
    dust_data = sd.cmd_query_data()

Use the command line tool
=========================
This package is provided with a command line tool to be able to immidiately start playing with your sensor
Command line is named ``pysds011``

First stop should be the embedded help. Here just an outdated version of it::

    pysds011.exe --help

    Usage: pysds011 [OPTIONS] COMMAND [ARGS]...

      pysds011 cli app entry point

    Options:
      --port TEXT          UART port to communicate with dust sensor.
      --id TEXT            ID of sensor to use. If not provided, the driver will
                           internally use FFFF that targets all.

      -v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO or DEBUG
      --help               Show this message and exit.

    Commands:
      dust        Get dust value
      fw-version  Get SDS011 FW version
      help        Get specific help of a command
      mode        Get and Set acquisition MODE [0,1] 1: QUERY mode：Sensor...
      sleep       Get and Set sleep MODE 1:sleep 0:wakeup Just 'sleep' without
                  a...

And each command has its own ``help``::

    pysds011.exe help dust

    Usage: pysds011 help [OPTIONS]

    Get dust value

    Options:
      --warmup INTEGER  Time in sec to warm up the sensor
      --format TEXT     result format (PRETTY|JSON|PM2.5|PM10)
      --help            Show this message and exit.

*Nova SDS011* sensor is connected to your machine through UART, so to read the actual ``dust`` value, you need to provide a **port** value::

    pysds011.exe --port COM4 dust
    PM 2.5: 25.9 μg/m^3  PM 10: 62.4 μg/m^3 CRC=OK

.. WARNING:: ``dust`` command changes both ``mode`` and ``sleep``. In particular it leave the sensor sleeping

Dust value can be presented in **multiple format**:

* PRETTY (default)

* JSON::

    pysds011.exe --port COM4 dust --format JSON
    {'pm25': 15.6, 'pm10': 21.8, 'pretty': 'PM 2.5: 15.6 μg/m^3  PM 10: 21.8 μg/m^3'}

* Single PM::

    pysds011.exe --port COM4 dust --format PM2.5
    26.0

    pysds011.exe --port COM4 dust --format PM10
    99.0

Read the dust sensor FW version::

    pysds011.exe --port COM4 fw-version

    FW version Y: 18, M: 11, D: 16, ID: 0xe748

Set the sensor in ``sleep`` more::

    pysds011.exe --port COM4 sleep 1

Take care that in sleep mode the only accepted command is the one to **wakeup**::

    pysds011.exe --port COM4 sleep 0

``mode`` command is about the sensor acquisition mode
* 0：report active mode
* 1：report query mode

Both the ``sleep`` and ``mode`` commands, asserted without and value, read the actual sensor configuration::

    pysds011.exe --port COM4 mode
    1
