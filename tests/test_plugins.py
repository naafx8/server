"""test plugins module."""
from unittest import mock
import itertools
import os
import pytest

from happypanda.core import plugins, command
from happypanda.common import hlogger
from happypanda.core.plugins import PluginManager, HPluginMeta
from happypanda.common import exceptions as hp_exceptions
from happypanda.common import constants

pytestmark = pytest.mark.plugintest

constants.available_commands = command.get_available_commands()

@pytest.fixture(scope='function')
def hplugin():
    hplugin_attr = dict(
        ID = "0890c892-cfa4-4e06-8962-460d395a7c5d",
        NAME = "Test",
        AUTHOR = "Pewpew",
        DESCRIPTION = "A test plugin",
        VERSION = (0, 0, 1),
        WEBSITE = "www.test.test")
    return type("HPlugin", (), hplugin_attr)

@pytest.fixture(scope='function')
def hplugin_meta(hplugin):
    return HPluginMeta(hplugin.__name__,
                      hplugin.__bases__,
                      dict(hplugin.__dict__))

@mock.patch('builtins.open', spec=open)
def test_plugin_load(m_open, hplugin):
    "Test if a plugin can be loaded"
    hpm = plugins._plugin_load(hplugin, 'test')

@pytest.mark.parametrize("init_func,exc_msg",
                          [
                              (lambda self:None, "Unexpected"),
                              (lambda self, t, *args, **kwargs: None, "Unexpected"),
                              (lambda self, t, *args:None, "__init__(self, *args, **kwargs)")
                              ])
def test_plugin_init_sig_error(init_func, exc_msg, hplugin_meta):
    "Test for errors if plugin class has wrong signature"
    pm = PluginManager()
    
    pm.register(hplugin_meta, mock.Mock(spec=hlogger.Logger))

    hplugin_meta.__init__ = init_func
    with pytest.raises(hp_exceptions.PluginSignatureError) as excinfo:
        pm.init_plugins()
    assert exc_msg in str(excinfo.value)

def test_plugin_init_sig(hplugin_meta):
    "Test if plugin class has the expected signature"
    pm = PluginManager()
    
    pm.register(hplugin_meta, mock.Mock(spec=hlogger.Logger))

    # good __init__
    hplugin_meta.__init__ = lambda self, *args, **kwargs:None
    pm.init_plugins()


def test_hplugin_missing_attrib_error():
    "Test for errors if plugin class has ommited required attributes"
    hplugin = type("HPlugin", (), {})
    for a, v in (("ID", ""), ("NAME", ""), ("VERSION", (0,0,0)), ("AUTHOR", ""), ("DESCRIPTION", "")):
        with pytest.raises(hp_exceptions.PluginAttributeError) as excinfo:
            hpm = plugins._plugin_load(hplugin, 'test')
        assert "attribute is missing" in str(excinfo.value)
        setattr(hplugin, a, v)

def test_hplugin_methods(hplugin_meta):
    "Test if plugclass has the required methods"
    assert hasattr(hplugin_meta, 'get_logger')
    assert hasattr(hplugin_meta, 'on_command')
    assert hasattr(hplugin_meta, 'create_command')

def test_hplugin_validuuid_error(hplugin):
    "Test for error on invalid plugin id"
    hplugin.ID = "123"
    with pytest.raises(hp_exceptions.PluginIDError):
        hpm = plugins._plugin_load(hplugin, 'test')
        # TODO: check exc msg

@mock.patch.object(PluginManager, "attach_to_command")
def test_hplugin_on_command(m_method, hplugin_meta):
    "Test plugin class on_command method"
    cmd_name = "test_command"
    constants.available_commands.add(cmd_name)
    def phandler():
        pass
    def hinit(self, *args, **kwargs):
        self.on_command(cmd_name, phandler)

    hplugin_meta.__init__ = hinit

    pmanager = PluginManager()
    pnode = pmanager.register(hplugin_meta, mock.Mock(spec=hlogger.Logger))
    pmanager.init_plugins()
    m_method.assert_called_with(pnode, cmd_name, phandler)

def test_hplugin_on_command_not_init_error(hplugin_meta):
    "Test for error when plugin attaches handler to command outside __init__"

def test_hplugin_on_command_handler_error(hplugin_meta):
    "Test for error on invalid command handler"
    cmd_name = "test_command"
    constants.available_commands.add(cmd_name)
    def hinit(self, *args, **kwargs):
        self.on_command(cmd_name, None)

    hplugin_meta.__init__ = hinit

    pmanager = PluginManager()
    pnode = pmanager.register(hplugin_meta, mock.Mock(spec=hlogger.Logger))
    with pytest.raises(hp_exceptions.PluginCommandError) as excinfo:
        pmanager.init_plugins()
    assert "Handler should be callable" in str(excinfo)

def test_hplugin_on_command_name_error(hplugin_meta):
    "Test for error on nonexistant command"
    cmd_name = "test_command"
    def phandler():
        pass

    def hinit(self, *args, **kwargs):
        self.on_command("test", phandler)

    hplugin_meta.__init__ = hinit

    pmanager = PluginManager()
    pnode = pmanager.register(hplugin_meta, mock.Mock(spec=hlogger.Logger))
    with pytest.raises(hp_exceptions.PluginCommandError) as excinfo:
        pmanager.init_plugins()
    assert "does not exist" in str(excinfo)

@mock.patch('builtins.open', spec=open)
def test_hplugin_logger_creation(m_open, hplugin):
    "Test plugin-specific logger is created"

    plugins.registered = PluginManager()

    p = os.path.join(os.getcwd(), "plugin")
    p_log = "plugin.log"
    enc = 'utf-8'

    hplugin.NAME = "test"

    node = plugins._plugin_load(hplugin, p)

    m_open.assert_called_with(os.path.join(p, p_log), 'a', encoding=enc)

    assert node.logger._logger.name == 'HPX Plugin.'+hplugin.NAME

def test_hplugin_get_logger(hplugin_meta):
    "Test get logger"

    with mock.patch.object(hplugin_meta, 'get_logger') as mget_logger:
        def hinit(self, *args, **kwargs):
            self.logger = self.get_logger()

        hplugin_meta.__init__ = hinit

        m_log = mock.Mock(spec=hlogger.Logger)
        pmanager = PluginManager()
        pnode = pmanager.register(hplugin_meta, m_log)
        pmanager.init_plugins()

        assert mget_logger.assert_called_with()


