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
# File: scheduled_job.py
#
# Initially created by Nguyen Huynh Tri Cuong (MS/EMC12-XC) / May 2023.
#
# Description:
#   A threaded job that executes a function at a specified interval.
#
# History:
#
# 22.05.2023 / V 0.1.0 / Nguyen Huynh Tri Cuong
# - Initialize
#
# *******************************************************************************
import threading


class ScheduledJob(threading.Thread):
   """
A threaded job that executes a function at a specified interval.
   """
   def __init__(self, interval, execute, *args, **kwargs):
      """
Constructor for ScheduledJob class.

**Arguments:**   

* ``interval``    

  / *Condition*: required / *Type*: datetime.timedelta /
  
  The interval between function executions.

* ``execute``    

  / *Condition*: required / *Type*: callable /
  
  The function to execute.

* ``args``    

  / *Condition*: required / *Type*: tuple /
  
  Variable-length positional arguments to pass to the function.

* ``kwargs``    

  / *Condition*: required / *Type*: dict /
  
  Keyword arguments to pass to the function.

**Returns:**

(*no returns*)
      """
      threading.Thread.__init__(self)
      self.daemon = False
      self.stopped = threading.Event()
      self.interval = interval
      self.execute = execute
      self.args = args
      self.kwargs = kwargs

   def stop(self):
      """
Stop the execution of the job.

**Returns:**

(*no returns*)
      """
      self.stopped.set()
      self.join()

   def run(self):
      """
Start the job execution loop.

**Returns:**

(*no returns*)
      """
      while not self.stopped.wait(self.interval.total_seconds()):
         self.execute(*self.args, **self.kwargs)