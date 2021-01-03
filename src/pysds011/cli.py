"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mpysds011` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``pysds011.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``pysds011.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
from pysds011 import driver
import click
import logging
import serial
import sys


@click.command()
@click.option('--port', default='/dev/ttyUSB0', help='UART port to communicate with dust sensor.')
@click.option('-v', '--verbose', count=True, default=1, help="Verbosity level (1:warning[default], 2:info, 3:debug) ")
def main(port, verbose):
    """cli interface to SD011 driver"""
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)15s()]::%(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    log = logging.getLogger(__name__)
    if verbose <= 1:
        log.setLevel(logging.WARNING)
    elif verbose == 2:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.DEBUG)

    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 9600

    ser.open()
    ser.flushInput()
    sd = driver.SDS011(ser, log)
    try:
        sd.cmd_set_sleep(0)
        sd.cmd_set_mode(sd.MODE_QUERY)
        sd.cmd_firmware_ver()
        time.sleep(3)
        pm = sd.cmd_query_data()
        click.echo('####'+str(pm))
    except Exception as e:
        log.exception(e)
    finally:
        sd.cmd_set_sleep(1)

    sys.exit(0)
