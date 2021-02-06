#!/usr/bin/python
# coding=utf-8
"""
Module that contains the command line app.
"""
#  Why does this file exist, and why not put this in __main__?
#
#  You might be tempted to import things from __main__ later, but that will cause
#  problems: the code will get executed twice:
#
#  - When you run `python -mpysds011` python will execute
#    ``__main__.py`` as a script. That means there won't be any
#    ``pysds011.__main__`` in ``sys.modules``.
#  - When you import __main__ it will get executed again (as a module) because
#    there's no ``pysds011.__main__`` in ``sys.modules``.
#
#  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration

from pysds011 import driver
import click
import click_log
import logging
import serial
import sys
import time
import json

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)15s()]::%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
log = logging.getLogger(__name__)
click_log.basic_config(log)


class Context(object):
    def __init__(self, ser=None, id=None):
        self.serial = ser
        self.id = id


@click.group()
@click.option('--port', default='/dev/ttyUSB0', help='UART port to communicate with dust sensor.')
@click.option('--id', help='ID of sensor to use. If not provided, the driver will internally use FFFF that targets all.')
@click_log.simple_verbosity_option(log)
@click.pass_context
def main(ctx, port, id):
    """
    pysds011 cli app entry point
    """
    main_ser = serial.Serial()
    main_ser.port = port
    main_ser.baudrate = 9600
    sensor_id = None
    if id:
        sensor_id = bytes.fromhex(id)
    else:
        sensor_id = b'\xff\xff'
    ctx.obj = Context(ser=main_ser, id=sensor_id)
    log.debug('Process subcommands')


@main.resultcallback()
def process_result(result, **kwargs):
    log.debug('process_result res:%s' % str(result))
    sys.exit(result)


@main.command()
@click.argument('subcommand')
@click.pass_context
def help(ctx, subcommand):
    """
    Get specific help of a command
    """
    subcommand_obj = main.get_command(ctx, subcommand)
    if subcommand_obj is None:
        click.echo("I don't know that command.")
    else:
        click.echo(subcommand_obj.get_help(ctx))


@main.command()
@click.option('--format', default='PRETTY', help='result format (PRETTY|JSON|PM2.5|PM10)')
@click.pass_obj
def fw_version(ctx, format):
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
            if 'PRETTY' in format:
                click.echo('FW version %s' % fw_str['pretty'])
            elif 'JSON' in format:
                click.echo(json.dumps(fw_str))
            else:
                log.error('Unknown format %s' % format)
                exit_val = 1
        else:
            log.error('Invalid FW version')
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
@click.argument('mode', type=click.Choice(['0', '1']), required=False)
@click.pass_obj
def sleep(ctx, mode):
    """
    Get and Set sleep MODE 1:sleep 0:wakeup
    Just 'sleep' without a number result in querying the actual value applied in the sensor
    """
    sd = None
    exit_val = 0
    try:
        ctx.serial.open()
        ctx.serial.flushInput()
        sd = driver.SDS011(ctx.serial, log)
        if mode:
            log.debug('BEGIN cli query mode:%d' % int(mode))
            if not sd.cmd_set_sleep(int(mode), id=ctx.id):
                log.error('cmd_set_sleep error')
                exit_val = 1
        else:
            click.echo(sd.cmd_get_sleep(id=ctx.id))
    except Exception as e:
        log.exception(e)
        exit_val = 1
    finally:
        ctx.serial.close()
    log.debug('END exit_val:%d' % exit_val)
    return exit_val


@main.command()
@click.argument('mode', type=click.Choice(['0', '1']), required=False)
@click.pass_obj
def mode(ctx, mode):
    """
    Get and Set acquisition MODE [0,1]
    1: QUERY mode：Sensor received query data command to report a measurement data.
    0: ACTIVE mode：Sensor automatically reports a measurement data in a work period.
    """
    sd = None
    exit_val = 0
    try:
        ctx.serial.open()
        ctx.serial.flushInput()
        sd = driver.SDS011(ctx.serial, log)
        if mode:
            log.debug('BEGIN cli acquisition mode:%d' % int(mode))
            if not sd.cmd_set_mode(int(mode), id=ctx.id):
                log.error('cmd_set_mode error')
                exit_val = 1
        else:
            click.echo(sd.cmd_get_mode(id=ctx.id))
    except Exception as e:
        log.exception(e)
        exit_val = 1
    finally:
        ctx.serial.close()
    log.debug('END exit_val:%d' % exit_val)
    return exit_val


@main.command()
@click.option('--warmup', default=3, help='Time in sec to warm up the sensor')
@click.option('--format', default='PRETTY', help='result format (PRETTY|JSON|PM2.5|PM10)')
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
        if sd.cmd_set_sleep(0, id=ctx.id) is not True:
            log.error('WakeUp failure')
            exit_val = 1
            return exit_val  # this jump to finally
        if sd.cmd_set_mode(sd.MODE_QUERY, id=ctx.id) is not True:
            log.error('Set MODE_QUERY failure')
            exit_val = 1
            return exit_val  # this jump to finally
        time.sleep(warmup)
        pm = sd.cmd_query_data(id=ctx.id)
        if pm is not None:
            if 'PRETTY' in format:
                click.echo(str(pm['pretty']))
            elif 'JSON' in format:
                click.echo(json.dumps(pm))
            elif 'PM2.5' in format:
                click.echo(pm['pm25'])
            elif 'PM10' in format:
                click.echo(pm['pm10'])
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
        log.debug('Dust finally')
        if sd is not None:
            sd.cmd_set_sleep(1, id=ctx.id)
        ctx.serial.close()
    log.debug('END exit_val:%d' % exit_val)
    return exit_val


@main.command()
@click.argument('id', required=False)
@click.pass_obj
def id(ctx, id):
    """
    Get and set the sensor address
    """
    sd = None
    exit_val = 0
    log.debug('BEGIN')
    sleep_address = ctx.id
    try:
        if id and (ctx.id is None or ctx.id == b'\xff\xff'):
            log.error("Missing current id")
            exit_val = 1
        else:
            ctx.serial.open()
            ctx.serial.flushInput()
            sd = driver.SDS011(ctx.serial, log)
            if sd.cmd_set_sleep(0, id=sleep_address) is not True:
                log.error('WakeUp failure')
                exit_val = 1
                return exit_val  # this jump to finally
            if id:
                sd.cmd_set_id(id=sleep_address, new_id=bytes.fromhex(id))
                sleep_address = bytes.fromhex(id)
            else:
                fw = sd.cmd_firmware_ver(id=sleep_address)
                if fw is None:
                    log.error('cmd_firmware_ver failure')
                    exit_val = 1
                    return exit_val
                log.debug("fw:"+str(fw))
                click.echo(''.join('%02x' % i for i in fw['id']))
    except Exception as e:
        log.exception(e)
        exit_val = 1
    finally:
        log.debug('Id finally')
        if sd is not None:
            sd.cmd_set_sleep(1, id=sleep_address)
        ctx.serial.close()
    log.debug('END exit_val:%d' % exit_val)
    return exit_val
