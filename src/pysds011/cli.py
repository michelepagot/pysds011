#!/usr/bin/python
# coding=utf-8
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
import click_log
import logging
import serial
import sys
import time

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)15s()]::%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
log = logging.getLogger(__name__)
click_log.basic_config(log)

class Context(object):
    def __init__(self, ser=None):
        self.serial = ser

@click.group()
@click.option('--port', default='/dev/ttyUSB0', help='UART port to communicate with dust sensor.')
@click_log.simple_verbosity_option(log)
@click.pass_context
def main(ctx, port):
    """
    pysds011 cli app entry point
    """
    main_ser = serial.Serial()
    main_ser.port = port
    main_ser.baudrate = 9600
    ctx.obj = Context(ser=main_ser)
    log.debug('Process subcommands')


@main.resultcallback()
def process_result(result, **kwargs):
    log.debug('process_result res:%s' % str(result))
    sys.exit(result)


@main.command()
@click.pass_obj
def fw_version(ctx):
    """
    Get SDS011 FW version
    """
    sd = None
    exit_val = 0
    log.debug('BEGIN')
    try:
        ctx.serial.open()
        ctx.serial.flushInput()
        sd = driver.SDS011(ctx.serial, log)
        sd.cmd_set_sleep(0)
        sd.cmd_set_mode(sd.MODE_QUERY)
        fw_str = sd.cmd_firmware_ver()
        if fw_str:
            click.echo('FW version %s' % fw_str)
        else:
            log.error('Empty FW version string')
            exit_val = 1
    except Exception as e:
        log.exception(e)
        exit_val = 1
    finally:
        if sd is not None:
            sd.cmd_set_sleep(1)
        ctx.serial.close()
    log.debug('END exit_val:%d' % exit_val)
    return exit_val


@main.command()
@click.argument('mode', type=int)
@click.pass_obj
def sleep_mode(ctx, mode):
    """
    Set sleep MODE 1:sleep 0:wakeup
    """
    sd = None
    exit_val = 0
    log.debug('BEGIN mode:%d' % mode)
    try:
        ctx.serial.open()
        ctx.serial.flushInput()
        sd = driver.SDS011(ctx.serial, log)
        sd.cmd_set_sleep(mode)
    except Exception as e:
        log.exception(e)
        exit_val = 1
    finally:
        ctx.serial.close()
    log.debug('END exit_val:%d' % exit_val)
    return exit_val


@main.command()
@click.option('--warmup', default=3, help='Time in sec to warm up the sensor')
@click.option('--format', default='PRETTY', help='result format (PRETTY|JSON)')
@click.pass_obj
def dust(ctx, warmup, format):
    """
    Get dust value
    """
    sd = None
    exit_val = 0
    log.debug('BEGIN')
    try:
        ctx.serial.open()
        ctx.serial.flushInput()
        sd = driver.SDS011(ctx.serial, log)
        sd.cmd_set_sleep(0)
        sd.cmd_set_mode(sd.MODE_QUERY)
        time.sleep(warmup)
        pm = sd.cmd_query_data()
        if pm is not None:
            if 'PRETTY' in format:
                click.echo(str(pm['pretty']))
            elif 'JSON' in format:
                click.echo(pm)
            else:
                log.error('Unknown format %s' % format)
                exit_val = 1
        else:
            log.error('Empty data')
            exit_val = 1
    except Exception as e:
        log.exception(e)
        exit_val = 1
    finally:
        if sd is not None:
            sd.cmd_set_sleep(1)
        ctx.serial.close()
    log.debug('END exit_val:%d' % exit_val)
    return exit_val
