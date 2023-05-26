from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier, DBusObjectIdentifier
from dasbus.client.proxy import disconnect_proxy
from dasbus.loop import EventLoop
from threading import Timer
from RobotFramework_DBus.thread_safe_dict import ThreadSafeDict
from dasbus.connection import SessionMessageBus
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

# Define the message bus.
SESSION_BUS = SessionMessageBus()

class RegisterKeyword:
    def __init__(self, kw):
        self._kw = kw

    def callback_func(self, observer):
        BuiltIn().log_to_console(observer)
        BuiltIn().run_keyword(self._kw)


class DBusClient:

   _watch_dict = ThreadSafeDict()

   def __init__(self, namespace, object_path):
      namespace_tuple = tuple(namespace.split('.'))
      self.proxy = None
      self.namespace = namespace
      self.object_path = object_path
      try:
         self.dbus = DBusServiceIdentifier(
                            namespace=namespace_tuple,
                            message_bus=SESSION_BUS
                        )

      except Exception as ex:
         raise Exception("Unable to connect to '%s' DBus. Reason: '%s'" % (namespace, str(ex)) )

   def connect(self):
      self.proxy = self.dbus.get_proxy(self.object_path)

   def disconnect(self):
      disconnect_proxy(self.proxy)

   def quit(self):
      self.disconnect()

   def set_signal_received_handler(self, signal, handler):
      rkw = RegisterKeyword(handler)
      sgn = getattr(self.proxy, signal)
      sgn.connect(rkw.callback_func)

   def add_signal_to_watch_dict(self, loop, signal, payloads=""):
      self._watch_dict[signal] = payloads
      try:
         loop.quit()
      except Exception as _ex:
         pass

   def wait_for_signal(self, wait_signal="", timeout=0):
      timeout = int(timeout)
      loop = EventLoop()
      try:
         sgn = getattr(self.proxy, wait_signal)
      except Exception as _ex:
         raise Exception("DBus service '%s' not have the signal '%s'" % (self.namespace, wait_signal))
      sgn.connect(lambda x: self.add_signal_to_watch_dict(loop, wait_signal, x))
      
      try:
         t = Timer(timeout, loop.quit)
         t.start()
      except Exception as _ex:
         pass
      loop.run()
      if wait_signal in self._watch_dict:
         return self._watch_dict[wait_signal]
      else:
         raise Exception("Unable to receive the '%s' signal after '%s'" % (wait_signal, timeout))

   def call_dbus_method(self, method_name, *args):
      try:
         method = getattr(self.proxy, method_name)
         return method(*args)
      except Exception as _ex:
         pass