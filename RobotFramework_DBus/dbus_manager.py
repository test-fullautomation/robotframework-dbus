from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.api.deco import keyword
# from common import HELLO_WORLD
from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier, DBusObjectIdentifier
from dasbus.client.proxy import disconnect_proxy
from dasbus.client.observer import DBusObserver
from dasbus.loop import EventLoop
from RobotFramework_DBus.dbus_client import DBusClient
import threading


class Singleton(object):  # pylint: disable=R0903
   """
   Class to implement Singleton Design Pattern. This class is used to derive the TTFisClientReal as only a single
   instance of this class is allowed.

   Disabled pyLint Messages:
   R0903:  Too few public methods (%s/%s)
            Used when class has too few public methods, so be sure it's really worth it.

            This base class implements the Singleton Design Pattern required for the TTFisClientReal.
            Adding further methods does not make sense.
   """
   _instance = None
   _lock = threading.Lock()

   def __new__(cls, *args, **kwargs):
      with cls._lock:
         if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
      return cls._instance


class DBusManager(Singleton):   
   """
Class to manage all connections.
   """
   ROBOT_LIBRARY_SCOPE = 'GLOBAL'
   ROBOT_AUTO_KEYWORDS = False

   def __init__(self):
      self.connection_manage_dict = {}

   def __del__(self):
      """
Destructor for ConnectionManager class.

**Returns:**
         None.
      """
      self.quit()

   def quit(self):
      """
Quit connection manager.
      
**Returns:**

(*no returns*)
      """
      for connection in self.connection_manage_dict.values():
         connection.quit()
      self.connection_manage_dict.clear()

   def add_connection(self, name, conn):
      """
Add a connection to managed dictionary.
      
**Arguments:**   

* ``name``   

  / *Condition*: required / *Type*: str /

  Connection's name.
  
* ``conn``   

  / *Condition*: required / *Type*: socket.socket /

  Connection object.

**Returns:**

(*no returns*)
      """
      if name not in self.connection_manage_dict.keys():
         self.connection_manage_dict[name] = conn

   def remove_connection(self, connection_name):
      """
Remove a connection by name.
      
**Arguments:**   

* ``connection_name``   

  / *Condition*: required / *Type*: str /

  Connection's name.

**Returns:**

(*no returns*)
      """
      if connection_name in self.connection_manage_dict.keys():
         del self.connection_manage_dict[connection_name]


   def get_connection_by_name(self, connection_name):
      """
Get an exist connection by name.
      
**Arguments:**   

* ``connection_name``   

  / *Condition*: required / *Type*: str /

  Connection's name.

**Returns:**

* ``conn``

  / *Type*: socket.socket /
  
  Connection object.
      """
      conn = None
      if connection_name in self.connection_manage_dict.keys():
         conn = self.connection_manage_dict[connection_name]
      return conn

   @keyword
   def disconnect(self, connection_name):
      """
Keyword for disconnecting a connection by name.
      
**Arguments:**   

* ``connection_name``   

  / *Condition*: required / *Type*: str /

  Connection's name.

**Returns:**

(*no returns*)
      """
      if connection_name in self.connection_manage_dict.keys():
         self.connection_manage_dict[connection_name].quit()
         del self.connection_manage_dict[connection_name]

   @keyword
   def connect(self, conn_name='default_conn', namespace="", object_path=None):
      """
Making a connection.
      
**Arguments:**   

* ``conn_name``    

  / *Condition*: optional / *Type*: str / *Default*: 'default_conn' /
  
  Name of connection.

* ``conn_type``    

  / *Condition*: optional / *Type*: str / *Default*: 'TCPIP' /
  
  Type of connection.

* ``conn_mode``    

  / *Condition*: optional / *Type*: str / *Default*: '' /
  
  Connection mode.

* ``conn_conf``    

  / *Condition*: optional / *Type*: json / *Default*: {} /
  
  Configuration for connection.

**Returns:**

(*no returns*)
      """
      if conn_name in self.connection_manage_dict.keys():
         raise AssertionError(constants.String.CONNECTION_NAME_EXIST % conn_name)

      if conn_name == 'default_conn':
         conn_name += str(ConnectionManager.id)
         ConnectionManager.id += 1

      try:
         connection_obj = DBusClient(namespace, object_path)
      except Exception as ex:
         # BuiltIn().log("Unable to create connection. Exception: %s" % ex, constants.LOG_LEVEL_ERROR)
         raise AssertionError("Unable to create connection. Exception: %s" % ex)

      if connection_obj is not None:
         setattr(connection_obj, 'connection_name', conn_name)
         if hasattr(connection_obj, "real_obj"):
            setattr(connection_obj.real_obj, 'connection_name', conn_name)
         self.add_connection(conn_name, connection_obj)

      try:
         connection_obj.connect()
      except Exception as ex:
         self.remove_connection(conn_name)
         # BuiltIn().log("Unable to create connection. Exception: %s" % ex, constants.LOG_LEVEL_ERROR)
         raise Exception("Unable to create connection. Exception: %s" % ex)
   
   @keyword
   def set_signal_received_handler(self, conn_name="", signal="", handler=None):
      if conn_name not in self.connection_manage_dict.keys():
         raise AssertionError("The '%s' connection  hasn't been established. Please connect first." % conn_name)
      
      connection_obj = self.connection_manage_dict[conn_name]
      try:
         connection_obj.set_signal_received_handler(signal, handler)
      except Exception as ex:
         pass

   @keyword
   def call_dbus_method(self, conn_name="", method_name="", *args):
      if conn_name not in self.connection_manage_dict.keys():
         raise AssertionError("The '%s' connection  hasn't been established. Please connect first." % conn_name)
      
      connection_obj = self.connection_manage_dict[conn_name]
      try:
         return connection_obj.call_dbus_method(method_name, args)
      except Exception as ex:
         pass

   @keyword
   def wait_for_signal(self, conn_name="", wait_signal="", timeout=0):
      if conn_name not in self.connection_manage_dict.keys():
         raise AssertionError("The '%s' connection  hasn't been established. Please connect first." % conn_name)
      
      connection_obj = self.connection_manage_dict[conn_name]
      payloads = None
      try:
         payloads = connection_obj.wait_for_signal(wait_signal, timeout)
      except Exception as ex:
         raise ex
      return payloads

