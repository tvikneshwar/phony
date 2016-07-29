import dbus
import time

from dbus import service
from phony.base import execute
from phony.base.log import ClassLogger, ScopedLogger, Levels

class Headset(ClassLogger, dbus.service.Object):
  OBJECT_PATH = '/org/littlecraft/Phony'
  SERVICE_NAME = 'org.littlecraft.Phony'

  __bus = None
  __adapter = None
  __profile = None
  __started = False

  def __init__(self, bus, adapter, hfp):
    ClassLogger.__init__(self)

    self.__bus = bus.session_bus()
    self.__bus.request_name(self.SERVICE_NAME)
    bus_name = dbus.service.BusName(self.SERVICE_NAME, bus = self.__bus)
    dbus.service.Object.__init__(self, bus_name, self.OBJECT_PATH)

    self.__adapter = adapter
    self.__hfp = hfp

    adapter.on_device_connected(self.device_connected)
    adapter.on_device_disconnected(self.device_disconnected)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.stop()

  @ClassLogger.TraceAs.call(with_arguments = False)
  def start(self, name, pincode):
    if self.__started:
      return

    self.enable()
    self.__hfp.start()
    self.__adapter.start(name, pincode)

  def stop(self):
    if self.__started:
      self.__adapter.stop()
      self.__hfp.stop()

  def enable(self):
    self.log().info("Enabling radio")
    # TODO: Ignore if rfkill is not available
    self.__exec("rfkill unblock bluetooth")

  def disable(self):
    self.log().info("Disabling radio")
    self.__exec("rfkill block bluetooth")

  def enable_pairability(self, timeout = 0):
    self.__adapter.enable_pairability(timeout)

  def disable_visibility(self):
    self.__adapter.disable_pairability()

  @ClassLogger.TraceAs.event(log_level = Levels.INFO)
  def device_connected(self, address):
    self.__endpoint = address
    #try:
    #  time.sleep(5)
    #  self.__hfp.attach(self.__adapter, address)
    #except Exception, ex:
    #  self.log().error('Unable to attach to device: ' + address + ': ' + str(ex))
    pass

  @ClassLogger.TraceAs.event(log_level = Levels.INFO)
  def device_disconnected(self, address):
    #self.__hfp.detach(self.__adapter, address)
    pass

  @ClassLogger.TraceAs.event(log_level = Levels.INFO)
  def profile_attached(self, hfp):
    pass

  @ClassLogger.TraceAs.event(log_level = Levels.INFO)
  def profile_detached(self, hfp):
    pass

  @dbus.service.method(dbus_interface = SERVICE_NAME)
  def BeginVoiceDial(self):
    self.__hfp.begin_voice_dial()

  @dbus.service.method(dbus_interface = SERVICE_NAME,
    input_signature = 's')
  def Dial(self, number):
    self.__hfp.dial(number)

  def __exec(self, command):
    self.log().debug('Running: ' + command)
    execute.privileged(command, shell = True)