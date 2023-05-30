#  Copyright 2020-2022 Robert Bosch GmbH
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# *******************************************************************************
#
# File: dbus_client.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC12-XC) / May 2023.
#
# Description:
#   Provide a client class for interacting with a specific DBus service.
#
# History:
#
# 22.05.2023 / V 0.1.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier, DBusObjectIdentifier
from dasbus.client.proxy import disconnect_proxy
from dasbus.loop import EventLoop
from threading import Timer
from RobotFramework_DBus.thread_safe_dict import ThreadSafeDict
from dasbus.connection import SessionMessageBus
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.running import Keyword


# Define the message bus.
SESSION_BUS = SessionMessageBus()


class RegisterKeyword:
   """
A class that provides a keyword as a callback function for a DBus signal received.
   """
   def __init__(self, kw):
      """
Constructor for RegisterKeyword class.

**Arguments:**   

* ``kw``    

  / *Condition*: required / *Type*: str /
  
  Keyword name to be set as the callback function.

**Returns:**

(*no returns*)
      """
      self._kw = kw

   def callback_func(self, *observer):
      """
Constructor for RegisterKeyword class.

**Arguments:**   

* ``observer``    

  / *Condition*: optional / *Type*: tuple / *Default*: None /
  
  Input arguments to be passed to the callback method.

**Returns:**

(*no returns*)
      """
      kw_args = None
      input_kw_args = observer
      try:
         all_lib = BuiltIn().get_library_instance(all=True)
         user_keywords = all_lib['BuiltIn']._context.namespace._kw_store.user_keywords
         kw_args = user_keywords.handlers[self._kw.lower()].arguments.argument_names
      except Exception as _ex:
         pass

      if kw_args is not None:
         input_kw_args = observer[0:len(kw_args)]

      BuiltIn().run_keyword(self._kw, *input_kw_args)



class DBusClient:
   """
A client class for interacting with a specific DBus service.
   """
   _watch_dict = ThreadSafeDict()

   def __init__(self, namespace, object_path):
      """
Constructor for DBusClient class.
      
**Arguments:**   

* ``namespace``    

  / *Condition*: optional / *Type*: str / *Default*: '' /
  
  The namespace of the DBus service.
  This identifies the specific service or group of services.
  It is used to differentiate between different service instances.
  The namespace should be a string that uniquely identifies the service.

* ``object_path``    

  / *Condition*: optional / *Type*: str / *Default*: None /
  
  The object path of the DBus service.
  This identifies the specific object within the service that the action will be performed on.
  The object path should be a string that follows the DBus object path naming convention.
  It typically consists of a hierarchical structure separated by slashes (/).

**Returns:**

(*no returns*)
      """
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
      """
Create a proxy object to DBus object.

**Returns:**

(*no returns*)
      """
      self.proxy = self.dbus.get_proxy(self.object_path)

   def disconnect(self):
      """
Disconnect the DBus proxy from the remote object.

**Returns:**

(*no returns*)
      """
      disconnect_proxy(self.proxy)

   def quit(self):
      """
Quit the DBus client.

**Returns:**

(*no returns*)
      """
      self.disconnect()

   def set_signal_received_handler(self, signal, handler):
      """
Set a signal received handler for a specific signal.
      
**Arguments:**   

* ``signal``    

  / *Condition*: required / *Type*: str /
  
  The name of the DBus signal to handle.

* ``handler``    

  / *Condition*: required / *Type*: str /
  
  The keyword to handle the received signal.
  The handler should accept the necessary parameters based on the signal being handled.

**Returns:**

(*no returns*)
      """
      rkw = RegisterKeyword(handler)
      sgn = getattr(self.proxy, signal)
      sgn.connect(rkw.callback_func)

   def add_signal_to_watch_dict(self,  signal, loop=None, payloads=""):
      self._watch_dict[signal] = payloads
      if loop is not None:
         try:
            loop.quit()
         except Exception as _ex:
            pass
   
   def register_monitored_signal(self, signal):
      """
Register a DBus signal or signals to be monitored for a specific connection.
      
**Arguments:**

* ``signal``    

  / *Condition*: optional / *Type*: str / *Default*: '' /
  
  The name of the DBus signal(s) to register. It can be a single signal name as a string,
  or multiple signal names joined by ','. For example: "signal1,signal2,signal3".

**Returns:**

(*no returns*)
      """
      if isinstance(signal, str):
         sgn_list = signal.split(",")
         for s in sgn_list:
            sgn = getattr(self.proxy, s)
            sgn.connect(lambda x: self.add_signal_to_watch_dict(s, None, x))
      elif isinstance(signal, list):
         for s in signal:
            sgn = getattr(self.proxy, s)
            sgn.connect(lambda x: self.add_signal_to_watch_dict(s, None, x))   

   def notify_on_signal(self):
      pass

   def wait_for_signal(self, wait_signal="", timeout=0):
      """
Wait for a specific DBus signal to be received within a specified timeout period.
      
**Arguments:**

* ``wait_signal``    

  / *Condition*: optional / *Type*: str / *Default*: '' /
  
  The name of the DBus signal to wait for.

* ``timeout``    

  / *Condition*: optional / *Type*: int / *Default*: 0 /
  
  The maximum time (in seconds) to wait for the signal.

**Returns:**

* ``payloads``

  / *Type*: str /
  
  The signal payloads.
      """
      timeout = int(timeout)
      loop = EventLoop()
      try:
         sgn = getattr(self.proxy, wait_signal)
      except Exception as _ex:
         raise Exception("DBus service '%s' not have the signal '%s'" % (self.namespace, wait_signal))

      callback_func = lambda x: self.add_signal_to_watch_dict(wait_signal, loop, x)
      sgn.connect(callback_func)
      if wait_signal in self._watch_dict:
         sgn.disconnect(callback_func)
         return self._watch_dict[wait_signal]
      
      try:
         t = Timer(timeout, loop.quit)
         t.start()
      except Exception as _ex:
         pass

      loop.run()
      if wait_signal in self._watch_dict:
         return self._watch_dict[wait_signal]
      else:
         raise AssertionError("Unable to receive the '%s' signal after '%s'" % (wait_signal, timeout))

   def call_dbus_method(self, method_name, *args):
      """
Call a DBus method with the specified method name and input arguments.
      
**Arguments:**   

* ``method_name``    

  / *Condition*: optional / *Type*: str / *Default*: '' /
  
  The name of the DBus method to be called.

* ``args``    

  / *Condition*: optional / *Type*: tuple / *Default*: None /
  
  Input arguments to be passed to the method.

**Returns:**

* ``ret_obj``

  / *Type*: Any /
  
  Connection object.
      """
      try:
         method = getattr(self.proxy, method_name)
         return method(*args)
      except Exception as ex:
         raise ex