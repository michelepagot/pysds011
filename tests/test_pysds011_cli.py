
from click.testing import CliRunner

from pysds011.cli import main, fw_version
from serial import SerialException


def test_noargs(mocker):
    '''
    Run the cli with no arguments print the help and return 0
    '''
    #mocker.patch('serial.Serial.open')
    #mocker.patch('serial.Serial.flushInput')
    #mocker.patch('serial.Serial.write')
    #mocker.patch('serial.Serial.read')
    #mocker.patch('serial.Serial.close')
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_option_help(mocker):
    '''
    Run the cli with --help
    '''
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])

    assert 'Usage:' in result.output
    assert result.exit_code == 0


def test_option_help(mocker):
    '''
    Run the cli with some base option but with no sub-command
    is not allowed
    '''
    runner = CliRunner()
    result = runner.invoke(main, ['--port', '/dev/ttyPANINO'])

    assert 'Error: Missing command' in result.output
    assert result.exit_code == 2


def test_subcommand_help(mocker):
    '''
    The cli support an help subcommand to retrieve specific
    help about a sub-command
    '''
    runner = CliRunner()
    # as help itself is a subcommand try
    # the unrealistic but valid ...
    result = runner.invoke(main, ['help', 'help'])

    assert 'Get specific help of a command' in result.output
    assert result.exit_code == 0


def test_subcommand_dust(mocker):
    '''
    Read dust
    '''
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    mocker.patch('time.sleep')
    cqd = mocker.patch('pysds011.driver.SDS011.cmd_query_data')
    # 'pretty' is truly a cmd_query_data output field,
    # 'woman' is just a film citation
    cqd.return_value = {'pretty' : 'woman'}

    runner = CliRunner()
    result = runner.invoke(main, ['dust'])

    assert 'woman' in result.output
    assert result.exit_code == 0


def test_main_notExitinPort(mocker):
    mocker.patch('serial.Serial.open', side_effect=SerialException())
    mocker.patch('serial.Serial.close')
    runner = CliRunner()
    result = runner.invoke(main, ['dust'])

    assert result.exit_code == 1


def test_version(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    cfv = mocker.patch('pysds011.driver.SDS011.cmd_firmware_ver')
    cfv.return_value = 'per il momento sono una stringa'
    runner = CliRunner()
    result = runner.invoke(main, ['fw-version'])

    assert 'per il momento sono una stringa' in result.output
    assert result.exit_code == 0
