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
# File: dbus_client_remote.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC12-XC) / May 2023.
#
# Description:
#   Provide a client class for interacting with a specific DBus service on a remote machine.
#
# History:
#
# 22.05.2023 / V 0.1.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from threading import Timer
from RobotFramework_DBus.common.thread_safe_dict import ThreadSafeDict
from RobotFramework_DBus.common.register_keyword import RegisterKeyword
from RobotFramework_DBus.common.scheduled_job import ScheduledJob
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.running import Keyword
from datetime import timedelta
import threading
import xmlrpc.client


class DBusClientRemote:
   """
A client class for interacting with a specific DBus service.
   """

   _CHECK_SIGNAL_INTERVAL = 50

   def __init__(self, namespace, object_path, host, port):
      """
Constructor for DBusClientRemote class.
      
**Arguments:**   

* ``namespace``    

  / *Condition*: required / *Type*: str /
  
  The namespace of the DBus service.
  This identifies the specific service or group of services.
  It is used to differentiate between different service instances.
  The namespace should be a string that uniquely identifies the service.

* ``object_path``    

  / *Condition*: required / *Type*: str /
  
  The object path of the DBus service.
  This identifies the specific object within the service that the action will be performed on.
  The object path should be a string that follows the DBus object path naming convention.
  It typically consists of a hierarchical structure separated by slashes (/).

* ``host``    

  / *Condition*: required / *Type*: str /
  
  The address of the host which DBus SUT is running on.

* ``port``    

  / *Condition*: required / *Type*: int /
  
  The port which the DBus Agent is listening on the remote system.

**Returns:**

(*no returns*)
      """
      namespace_tuple = tuple(namespace.split('.'))
      self.rpc_proxy = xmlrpc.client.ServerProxy("http://%s:%s" % (host, port), allow_none=True)
      self.session = self.rpc_proxy.get_session_token()
      self.singal_handler_dict = dict()
      self.namespace = namespace
      self.object_path = object_path
      try:
         self.rpc_proxy.initialize_dbus_client(self.session, self.namespace, self.object_path)
      except Exception as ex:
         raise Exception("Unable to connect to '%s' DBus. Reason: '%s'" % (namespace, str(ex)) )

   def connect(self):
      """
Create a proxy object to DBus object.

**Returns:**

(*no returns*)
      """
      self.rpc_proxy.connect(self.session)

   def disconnect(self):
      """
Disconnect the DBus proxy from the remote object.

**Returns:**

(*no returns*)
      """
      self.rpc_proxy.disconnect(self.session)

   def quit(self):
      """
Quit the DBus client.

**Returns:**

(*no returns*)
      """
      self.disconnect()
      for job in self.singal_handler_dict.values():
         job.stop()
      self.singal_handler_dict.clear()

   def do_signal_check(self, signal, call_back_func):
      """
Checking if the signal was emited.

**Arguments:**   

* ``signal``    

  / *Condition*: required / *Type*: str /
  
  The name of the DBus signal to check.

* ``call_back_func``    

  / *Condition*: required / *Type*: callable /
  
  The function to be callback when receiving the signal.

**Returns:**

(*no returns*)
      """
      rpc_proxy = xmlrpc.client.ServerProxy("http://%s:%s" % (self.host, self.port), allow_none=True)
      payloads = rpc_proxy.get_monitoring_signal_payloads(self.session, signal)
      if payloads is not None:
         call_back_func(payloads)

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
      signal_check_job = ScheduledJob( timedelta(milliseconds=DBusClientRemote._CHECK_SIGNAL_INTERVAL), 
                              self.do_signal_check, 
                              *(signal, rkw.callback_func))
      self.rpc_proxy.register_monitored_signal(self.session, signal)
      signal_check_job.start()
      self.singal_handler_dict[signal] = signal_check_job

   def unset_signal_received_handler(self, signal):
      """
Unset a signal received handler for a specific signal.
      
**Arguments:**   

* ``signal``    

  / *Condition*: required / *Type*: str /
  
  The name of the DBus signal to handle.

**Returns:**

(*no returns*)
      """
      if signal in self.singal_handler_dict:
         job_check = self.singal_handler_dict[signal]
         job_check.stop()
         del self.singal_handler_dict[signal]

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
      self.rpc_proxy.register_monitored_signal(self.session, signal) 

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
      return self.rpc_proxy.wait_for_signal(self.session, wait_signal, timeout)

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
      return self.rpc_proxy.call_dbus_method(self.session, method_name, *args)