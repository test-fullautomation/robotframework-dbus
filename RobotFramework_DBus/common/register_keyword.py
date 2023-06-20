#  Copyright 2020-2023 Robert Bosch GmbH
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
# File: register_keyword.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC12-XC) / May 2023.
#
# Description:
#   A class that provides a robotframework keyword as a callback function for a DBus signal received.
#
# History:
#
# 22.05.2023 / V 0.1.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.running import Keyword


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

   def get_kw_name(self):
      """
Get the handle keyword name.

**Returns:**

  / *Type*: str /

  The handle keyword name.
      """
      return self._kw

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
