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
#   Provide a DBus Agent with the provided configuration.
#   It parses the command-line arguments, such as the host and port options,
#   and then starts the agent on the specified host and port.
#
#   The agent listens for incoming requests from clients and manages client sessions.
#   It provides a mechanism to execute requests on corresponding DBus services
#   through the assigned Executor instances.
#
# History:
#
# 22.05.2023 / V 0.1.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from RobotFramework_DBus.common.thread_safe_dict import ThreadSafeDict
from RobotFramework_DBus.common.utils import Utils
from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier, DBusObjectIdentifier
from dasbus.client.proxy import disconnect_proxy
from dasbus.loop import EventLoop
from threading import Timer
from dasbus.connection import SessionMessageBus
import xmlrpc.server
import argparse
import secrets
import string


# Define the message bus.
SESSION_BUS = SessionMessageBus()


class DBusClientExecutor:
   """
The DBusClientExecutor class represents an executor responsible for handling client requests on specific DBus services.
It receives requests from the DBusAgent and executes them on the corresponding DBus service.
   """
   _captured_signal_dict = ThreadSafeDict()

   def __init__(self, namespace, object_path):
      """
Constructor for DBusClientExecutor.
      
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

   def get_monitoring_signal_payloads(self, signal):
      """
Get the payloads of a specific signal.
      
**Arguments:**   

* ``signal``    

  / *Condition*: required / *Type*: str /
  
  The name of the DBus signal to get payloads.

**Returns:**

* ``payloads``

  / *Type*: str /
  
  The signal's payloads.
      """
      payloads = None
      if signal in self._captured_signal_dict:
         payloads = self._captured_signal_dict[signal]
      return payloads

   def add_signal_to_captured_dict(self, signal, loop=None, payloads=""):
      """
Add a signal and its payloads to the captured dictionary when the signal be emited.
      
**Arguments:**

* ``signal``    

  / *Condition*: required / *Type*: str /
  
  The name of the DBus signal(s) which has been raised.

* ``loop``    

  / *Condition*: optional / *Type*: EventLoop / *Default*: None /
  
  The Event loop which is running to wait for the raised signal.

* ``payloads``    

  / *Condition*: optional / *Type*: Any / *Default*: "" /
  
  The payloads of the raised signal.

**Returns:**

(*no returns*)      
      """
      self._captured_signal_dict[signal] = payloads
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
            sgn.connect(lambda x: self.add_signal_to_captured_dict(s, None, x))
      elif isinstance(signal, list):
         for s in signal:
            sgn = getattr(self.proxy, s)
            sgn.connect(lambda x: self.add_signal_to_captured_dict(s, None, x))  

   def _run_event_loop_with_timeout(self, loop, timeout):
      """
Run the Event Loop with timeout.
      
**Arguments:**

* ``loop``    

  / *Condition*: required / *Type*: EventLoop /
  
  The Event loop to be run.

* ``timeout``    

  / *Condition*: required / *Type*: int /
  
  The timeout for running Event loop.

**Returns:**

(*no returns*)
      """
      try:
         t = Timer(timeout, loop.quit)
         t.start()
      except Exception as _ex:
         pass

      loop.run()
   
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

      callback_func = lambda x: self.add_signal_to_captured_dict(wait_signal, loop, x)
      sgn.connect(callback_func)
      if wait_signal in self._captured_signal_dict:
         sgn.disconnect(callback_func)
         return self._captured_signal_dict[wait_signal]
      
      self._run_event_loop_with_timeout(loop, timeout)

      if wait_signal in self._captured_signal_dict:
         sgn.disconnect(callback_func)
         return self._captured_signal_dict[wait_signal]
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

* ``mtd_ret``

  / *Type*: Any /
  
  Return from called method.
      """
      try:
         method = getattr(self.proxy, method_name)
         mtd_ret = method(*args)
         return mtd_ret
      except Exception as ex:
         raise ex


class DBusClientAgent:
   """
The DBusClientAgent class acts as a mediator between clients and the corresponding DBus services they request.
It manages client connections, session tokens, and assigns the appropriate DBusClientExecutor for each client session.
   """
   def __init__(self):
      """
Constructor for DBusClientAgent.
      """
      self._executor_dict = dict()

   def get_session_token(self):
      """
 Generates a unique session token for a client and returns it.

**Returns:**

/ *Type*: str /
  
  The random and unique token.
      """      
      return Utils().make_unique_token()

   def initialize_dbus_client(self, session, namespace, object_path):
      """
Initializes an DBusClientExecutor instance for a specific client.

An DBusClientExecutor is an object responsible for executing requests from clients on corresponding DBus services.
By initializing a separate DBusClientExecutor for each client, the DBusClientAgent ensures that requests from different
clients are handled independently.

The client session token is a unique identifier that can be used to associate the DBusClientExecutor with the specific client.
This allows the DBusClientAgent to route incoming requests to the correct DBusClientExecutor based on the client session token.
      
**Arguments:**   

* ``session``    

  / *Condition*: required / *Type*: str /
  
  The client's session token.

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
      if session in self._executor_dict:
         raise Exception("The session '%s' has alreday initialized." % session)
      
      self._executor_dict[session] = DBusClientExecutor(namespace, object_path)
   
   def connect(self, session):
      """
Create a proxy object to DBus service.

**Returns:**

(*no returns*)
      """
      self._executor_dict[session].connect()

   def disconnect(self, session):
      """
Disconnect the DBus proxy from the remote object.

**Returns:**

(*no returns*)
      """
      self._executor_dict[session].disconnect()

   def quit(self, session):
      """
Quit the DBus client.

**Returns:**

(*no returns*)
      """
      self._executor_dict[session].quit()

   def get_monitoring_signal_payloads(self, session, signal):
      """
Get the payloads of a specific signal.
      
**Arguments:**   

* ``session``    

  / *Condition*: required / *Type*: str /
  
  The client's session token.

* ``signal``    

  / *Condition*: required / *Type*: str /
  
  The name of the DBus signal to get payloads.

**Returns:**

* ``payloads``

  / *Type*: str /
  
  The signal's payloads.
      """
      return self._executor_dict[session].get_monitoring_signal_payloads(signal)

   def register_monitored_signal(self, session, signal):
      """
Register a DBus signal or signals to be monitored for a specific connection.
      
**Arguments:**

* ``session``    

  / *Condition*: required / *Type*: str /
  
  The client's session token.

* ``signal``    

  / *Condition*: required / *Type*: str / 
  
  The name of the DBus signal(s) to register. It can be a single signal name as a string,
  or multiple signal names joined by ','. For example: "signal1,signal2,signal3".

**Returns:**

(*no returns*)
      """
      self._executor_dict[session].register_monitored_signal(signal)
   
   def wait_for_signal(self, session, wait_signal="", timeout=0):
      """
Wait for a specific DBus signal to be received within a specified timeout period.
      
**Arguments:**

* ``session``    

  / *Condition*: required / *Type*: str /
  
  The client's session token.

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
      return self._executor_dict[session].wait_for_signal(wait_signal, timeout)

   def call_dbus_method(self, session, method_name, *args):
      """
Call a DBus method with the specified method name and input arguments.
      
**Arguments:**   

* ``session``    

  / *Condition*: required / *Type*: str /
  
  The client's session token.

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
      return self._executor_dict[session].call_dbus_method(method_name, *args)


def run_agent():
   """
Run the DBus Agent with the specified configuration.

Description:

   The `run_agent` function starts the DBus Agent with the provided configuration.
   It parses the command-line arguments, such as the host and port options,
   and then starts the agent on the specified host and port.

   The agent listens for incoming requests from clients and manages client sessions.
   It provides a mechanism to execute requests on corresponding DBus services
   through the assigned Executor instances.

   Command-line Arguments:
      --host (str, optional): The host where the agent is running. Default is '0.0.0.0'.
      --port (int, optional): The port where the agent is listening. Default is 2507.
   """
   # Create the argument parser
   parser = argparse.ArgumentParser(description='DBus Agent Configuration')
   # Add the host option
   parser.add_argument('--host', default='0.0.0.0', help='The host where the agent is running')

   # Add the port option
   parser.add_argument('--port', type=int, default=2507, help='The port where the agent is listening')

   # Parse the command-line arguments
   args = parser.parse_args()

   # Access the values of the host and port options
   host = args.host
   port = args.port

   print("Starting DBus Agent Client on port %s..." % port)
   server = xmlrpc.server.SimpleXMLRPCServer((host, port), allow_none=True)
   server.register_instance(DBusClientAgent())
   server.serve_forever()

if __name__ == '__main__':
   run_agent()