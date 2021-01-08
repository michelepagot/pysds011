
from click.testing import CliRunner

from pysds011.cli import main, fw_version
from serial import SerialException


def test_main_noargs_notfunctionalUART(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    mocker.patch('serial.Serial.write')
    mocker.patch('serial.Serial.read')
    mocker.patch('serial.Serial.close')
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 1


def test_main_notExitinPort(mocker):
    mocker.patch('serial.Serial.open', side_effect=SerialException())
    mocker.patch('serial.Serial.close')
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 1



def test_version(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    mocker.patch('serial.Serial.write')
    mocker.patch('serial.Serial.read')
    mocker.patch('serial.Serial.close')
    runner = CliRunner()
    result = runner.invoke(fw_version, [])

    assert result.exit_code == 1
