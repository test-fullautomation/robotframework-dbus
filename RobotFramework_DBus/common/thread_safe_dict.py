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
# File: thread_safe_dict.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC12-XC) / May 2023.
#
# Description:
#   Provides a dictionary with thread-safe operations by utilizing locks for synchronized access.
#
# History:
#
# 22.05.2023 / V 0.1.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from threading import RLock


class ThreadSafeDict(dict):
   """
This class provides a dictionary with thread-safe operations by
utilizing locks for synchronized access.
   """
   def __init__(self):
      """
Constructor for ThreadSafeDict class.
      """
      super(ThreadSafeDict, self).__init__()
      self.__RLock=RLock()
   
   def __setitem__(self, key, item): 
      """
Set the value for a given key.

**Arguments:**

* ``key``    

  / *Condition*: required / *Type*: Any /
  
  The key of dictionary.

* ``item``    

  / *Condition*: required / *Type*: Any / 
  
  The value of given key.

**Returns:**

(*no returns*)
      """
      with self.__RLock:
         super(ThreadSafeDict, self).__setitem__(key, item)
      
   def __delitem__(self, key): 
      """
Delete the value associated with a given key.

**Arguments:**

* ``key``    

  / *Condition*: required / *Type*: Any /
  
  The key of dictionary to be delteted.

**Returns:**

(*no returns*)
      """
      with self.__RLock:
         super(ThreadSafeDict, self).__delitem__(key)    
       
   def clear(self): 
      """
Remove all key-value pairs from the dictionary.

**Returns:**

(*no returns*)
      """
      with self.__RLock:
         super(ThreadSafeDict, self).clear()    
        
   def pop(self, key, *args): 
      """
Remove and return the value associated with a given key.

**Arguments:**

* ``key``    

  / *Condition*: required / *Type*: Any /
  
  The key of dictionary to be pop.

**Returns:**

* ``o``

  / *Type*: Any /
  
  Value of the given key.
      """
      with self.__RLock:
         o=super(ThreadSafeDict, self).pop(key,*args)
      return o        
        
   def popitem(self):
      """
Remove and return an arbitrary key-value pair from the dictionary.

**Returns:**

(*no returns*)
      """
      with self.__RLock:
         o=super(ThreadSafeDict, self).popitem()        
      return o
    
   def update(self, dict=None):
      """
Update the dictionary with key-value pairs from another dictionary.

**Arguments:**

* ``dict``    

  / *Condition*: optional / *Type*: dict / *Default*: None /
  
  Another dictionary-like object to update from.

**Returns:**

(*no returns*)
      """
      if dict is None:
         pass
      elif isinstance(dict, type({})):
         for (key,value) in dict.items():
            self.__setitem__(key,value)
      else:
         raise TypeError