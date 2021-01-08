========
Overview
========


Simple python driver for SDS011 PM sensor from Nova.

* Free software: MIT license

Installation
============

::

    pip install pysds011

You can also install the in-development version with::

    pip install https://github.com/michelepagot/pysds011/archive/master.zip

Usage
=====
Package has a class interface

.. code-block:: python

    log = logging.getLogger(__name__)
    ser = serial.Serial('/dev/ttyUSB0', 9600)
    ser.open()
    sd = driver.SDS011(ser, log)
    sd.cmd_set_sleep(0)
    sd.cmd_set_mode(sd.MODE_QUERY)
    sd.cmd_firmware_ver()


Package is also provided with a reference cli application
    pysds011.exe --port COM42 version
    >> 21.2.2223


Documentation
=============

This internal package documentation is available at https://pysds011.readthedocs.io/
Some other interesting reading are:
- SDS011 datasheet http://cl.ly/ekot
- This project is inspired by https://gist.github.com/kadamski/92653913a53baf9dd1a8


Development
===========

