
from click.testing import CliRunner
from unittest.mock import call
import json

from pysds011.cli import main
from serial import SerialException


def test_noargs(mocker):
    '''
    Run the cli with no arguments print the help and return 0
    '''
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


def test_option_nosubcommand(mocker):
    '''
    Run the cli with some base option but with no sub-command
    is not allowed
    '''
    runner = CliRunner()
    result = runner.invoke(main, ['--port', '/dev/ttyPANINO'])

    assert 'Error: Missing command' in result.output
    assert result.exit_code == 2


def test_main_notExistinPort(mocker):
    mocker.patch('serial.Serial.open', side_effect=SerialException())
    mocker.patch('serial.Serial.close')
    runner = CliRunner()
    result = runner.invoke(main, ['--port', 'COM42', 'dust'])

    assert result.exit_code == 1


def test_help(mocker):
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


def test_dust(mocker):
    '''
    Read dust
    '''
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = True
    csm = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    csm.return_value = True
    mocker.patch('time.sleep')
    cqd = mocker.patch('pysds011.driver.SDS011.cmd_query_data')
    # 'pretty' is a keys of cmd_query_data output field,
    # 'woman' is just a film citation
    cqd.return_value = {'pretty': 'woman'}

    runner = CliRunner()
    result = runner.invoke(main, ['dust'])

    cqd.assert_called_once_with(id=b'\xff\xff')
    assert 'woman' in result.output
    assert result.exit_code == 0


def test_dust_with_id(mocker):
    '''
    Read dust of a specific sensor
    '''
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = True
    csm = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    csm.return_value = True
    mocker.patch('time.sleep')
    cqd = mocker.patch('pysds011.driver.SDS011.cmd_query_data')
    # 'pretty' is a keys of cmd_query_data output field,
    # 'woman' is just a film citation
    cqd.return_value = {'pretty': 'woman'}

    runner = CliRunner()
    result = runner.invoke(main, ['--id', 'ABCD', 'dust'])

    assert 'woman' in result.output
    assert result.exit_code == 0
    calls = [call(0, id=b'\xab\xcd'), call(1, id=b'\xab\xcd')]
    css.assert_has_calls(calls, any_order=False)
    csm.assert_called_once_with(1, id=b'\xab\xcd')
    cqd.assert_called_once_with(id=b'\xab\xcd')


def test_dust_format_json(mocker):
    '''
    Use dust command with JSON as output format
    '''
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = True
    csm = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    csm.return_value = True
    mocker.patch('time.sleep')
    cqd = mocker.patch('pysds011.driver.SDS011.cmd_query_data')
    # 'pretty' is a keys of cmd_query_data output field,
    # 'woman' is just a film citation
    cqd.return_value = {"pretty": "woman"}

    runner = CliRunner()
    result = runner.invoke(main, ['dust', '--format', 'JSON'])

    obj = json.loads(result.output)
    assert 'pretty' in obj.keys()
    assert 'woman' in obj['pretty']
    assert result.exit_code == 0


def test_dust_with_format_pm25(mocker):
    '''
    Use dust command with PM2.5 format and check that
    only the corresponding value is printed out
    '''
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = True
    csm = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    csm.return_value = True
    mocker.patch('time.sleep')
    cqd = mocker.patch('pysds011.driver.SDS011.cmd_query_data')
    # 'pretty' is a keys of cmd_query_data output field,
    # 'woman' is just a film citation
    cqd.return_value = {'pretty': "woman", 'pm25': 21.07}

    runner = CliRunner()
    result = runner.invoke(main, ['dust', '--format', 'PM2.5'])
    assert '21.07' in result.output
    assert result.exit_code == 0


def test_dust_with_invalid_format(mocker):
    '''
    Use dust command with not supported as output format
    '''
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = True
    csm = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    csm.return_value = True
    mocker.patch('time.sleep')
    cqd = mocker.patch('pysds011.driver.SDS011.cmd_query_data')
    # 'pretty' is a keys of cmd_query_data output field,
    # 'woman' is just a film citation
    cqd.return_value = {'pretty': "woman", 'pm25': 21.07}

    runner = CliRunner()
    result = runner.invoke(main, ['dust', '--format', 'NOTSUPPORTED'])
    assert result.exit_code == 1


def test_dust_error_wakeup(mocker):
    '''
    Use dust command, driver error at wakeup
    '''
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = False
    mocker.patch('serial.Serial.close')

    runner = CliRunner()
    result = runner.invoke(main, ['dust'])
    assert result.exit_code == 1


def test_version(mocker):
    """ Get the sensor firmware version
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    cfv = mocker.patch('pysds011.driver.SDS011.cmd_firmware_ver')
    cfv.return_value = {'pretty': 'BimBumBam'}
    runner = CliRunner()
    result = runner.invoke(main, ['fw-version'])

    assert 'BimBumBam' in result.output
    assert result.exit_code == 0


def test_fw_version_json_format(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    cfv = mocker.patch('pysds011.driver.SDS011.cmd_firmware_ver')
    cfv.return_value = {'pretty': 'BimBumBam'}
    runner = CliRunner()
    result = runner.invoke(main, ['fw-version', '--format', 'JSON'])
    obj = json.loads(result.output)

    assert 'BimBumBam' in obj['pretty']
    assert result.exit_code == 0


def test_fw_version(mocker):
    """Test fw_version comand
    By default it use the PRETTY format
    Pretty format has an intro text like "FW version"
    then it print 'pretty' field in driver response
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    cfv = mocker.patch('pysds011.driver.SDS011.cmd_firmware_ver')
    cfv.return_value = {'pretty': 'BimBumBam'}
    runner = CliRunner()
    result = runner.invoke(main, ['fw-version'])

    assert 'FW version' in result.output
    assert 'BimBumBam' in result.output
    assert result.exit_code == 0


def test_sleep_set(mocker):
    """Set the sleep mode 1:SLEEP
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    runner = CliRunner()
    result = runner.invoke(main, ['sleep', '1'])
    css.assert_called_once_with(1, id=b'\xff\xff')

    assert result.exit_code == 0


def test_sleep_set_wakeup(mocker):
    """Set the sleep mode 0:WAKEUP
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    runner = CliRunner()
    result = runner.invoke(main, ['sleep', '0'])
    css.assert_called_once_with(0, id=b'\xff\xff')

    assert result.exit_code == 0


def test_sleep_with_id(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    runner = CliRunner()
    result = runner.invoke(main, ['--id', 'ABCD', 'sleep', '1'])
    css.assert_called_once_with(1, id=b'\xab\xcd')

    assert result.exit_code == 0


def test_sleep_invalid_mode(mocker):
    """
    sleep set behavior if command is called
    with mode not in valid rage
    """
    runner = CliRunner()
    result = runner.invoke(main, ['sleep', '2'])

    assert result.exit_code == 2
    assert 'Usage:' in result.output
    assert 'invalid choice: 2' in result.output


def test_sleep_driver_error(mocker):
    """
    sleep set behavior if cmd_set_sleep return False
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = False
    runner = CliRunner()
    result = runner.invoke(main, ['sleep', '0'])

    assert result.exit_code == 1


def test_sleep_get(mocker):
    """Run 'sleep' without any parameter
    result in asking to sensor the actual applied value
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    cgs = mocker.patch('pysds011.driver.SDS011.cmd_get_sleep')
    cgs.return_value = 1
    runner = CliRunner()
    result = runner.invoke(main, ['sleep'])
    cgs.assert_called_once_with(id=b'\xff\xff')

    assert '1' in result.output
    assert result.exit_code == 0


def test_slepp_get_at_id(mocker):
    """get actual sleep mode of a particular sensor id
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    cgs = mocker.patch('pysds011.driver.SDS011.cmd_get_sleep')
    runner = CliRunner()
    result = runner.invoke(main, ['--id', 'ABCD', 'sleep'])
    cgs.assert_called_once_with(id=b'\xab\xcd')

    assert result.exit_code == 0


def test_mode_set(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    runner = CliRunner()
    result = runner.invoke(main, ['mode', '1'])
    css.assert_called_once_with(1, id=b'\xff\xff')

    assert result.exit_code == 0


def test_mode_set_active(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    runner = CliRunner()
    result = runner.invoke(main, ['mode', '1'])
    css.assert_called_once_with(1, id=b'\xff\xff')

    assert result.exit_code == 0


def test_mode_set_query(mocker):
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_mode')
    runner = CliRunner()
    result = runner.invoke(main, ['mode', '0'])
    css.assert_called_once_with(0, id=b'\xff\xff')

    assert result.exit_code == 0


def test_mode_get(mocker):
    """get actual acquisition mode by not providing any value
    after 'mode'
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    cgs = mocker.patch('pysds011.driver.SDS011.cmd_get_mode')
    runner = CliRunner()
    result = runner.invoke(main, ['mode'])
    cgs.assert_called_once_with(id=b'\xff\xff')

    assert result.exit_code == 0


def test_mode_get_at_id(mocker):
    """get actual acquisition of a particular sensor id
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    cgs = mocker.patch('pysds011.driver.SDS011.cmd_get_mode')
    runner = CliRunner()
    result = runner.invoke(main, ['--id', 'ABCD', 'mode'])
    cgs.assert_called_once_with(id=b'\xab\xcd')

    assert result.exit_code == 0


def test_id_set(mocker):
    """ Set a sensor id
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = True
    csi = mocker.patch('pysds011.driver.SDS011.cmd_set_id')
    runner = CliRunner()
    result = runner.invoke(main, ['--id', 'cccc', 'id', 'abcd'])

    # Two calls to cmd_set_sleep:
    #  the first use original address
    #  at the second one, the sensor has a new address: so sleep
    # has the use the new one
    calls = [call(0, id=b'\xcc\xcc'), call(1, id=b'\xab\xcd')]
    css.assert_has_calls(calls, any_order=False)
    csi.assert_called_once_with(id=b'\xcc\xcc', new_id=b'\xab\xcd')
    assert result.exit_code == 0


def test_id_is_set_without_original_id(mocker):
    """ Set a sensor id without to specify original id
    result in an error. As it is a matter of input parameter validation,
    no interaction with pyserial or driver has to take place at all
    """
    runner = CliRunner()
    result = runner.invoke(main, ['id', 'abcd'])
    assert result.exit_code != 0


def test_id_get(mocker):
    """Run 'id' without any parameter
    result in asking to sensor its id
    As a dedicated get_id sensor command does not exist,
    and as to ask a specific id to a specific sensor
    I should neet its id ... but why I'm asking for an id if I need the id
    and as in any case each command replay with the id
    it is made with a trick: the cmd_firmware_ver is sent
    with FFFF, id is extracted by all sensors that replay to me
    """
    mocker.patch('serial.Serial.open')
    mocker.patch('serial.Serial.flushInput')
    css = mocker.patch('pysds011.driver.SDS011.cmd_set_sleep')
    css.return_value = True
    cfv = mocker.patch('pysds011.driver.SDS011.cmd_firmware_ver')
    cfv.return_value = {'id': b'\x12\x34', 'paperino': 'maciomicio'}
    runner = CliRunner()
    result = runner.invoke(main, ['id'])

    calls = [call(0, id=b'\xff\xff'), call(1, id=b'\xff\xff')]
    css.assert_has_calls(calls, any_order=False)

    assert '12' in result.output and '34' in result.output
    assert result.exit_code == 0
