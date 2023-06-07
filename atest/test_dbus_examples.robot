#  Copyright 2020-2022 Robert Bosch Car Multimedia GmbH
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
*** Settings ***
Library    RobotFramework_DBus.DBusManager

*** Test Cases ***
Waiting for DBus Signals with Synchronizatio
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=local

   ${ret}=    Wait For Signal     conn_name=test_dbus
   ...                            signal=YellowMessage
   ...                            timeout=10

   Log To Console    ${ret}

   Disconnect    test_dbus

Handling Multiple DBus Signals : Ensuring Signal Monitoring with the 'Register Signal' Keyword
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=local

   Register Signal    conn_name=test_dbus    signal=GreenMessage

   ${ret}=    Wait For Signal     conn_name=test_dbus
   ...                            signal=YellowMessage
   ...                            timeout=10
   Log To Console    ${ret}

   ${ret}=    Wait For Signal     conn_name=test_dbus
   ...                            signal=GreenMessage
   ...                            timeout=10
   Log To Console    ${ret}

   ${ret}=    Call Dbus Method    test_dbus    Hello    World
   Disconnect    test_dbus

Handling DBus Signals: Non-blocking Signal Handling with the 'Set Signal Received Handler' Keyword
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=local

   Set Signal Received Handler    conn_name=test_dbus
   ...                            signal=RedMessage
   ...                            handler=On Received Red Signal

   Log To Console    The test is continuing...

   Sleep    10s

   Disconnect    test_dbus

Invoking DBus Methods: Using the 'Call Dbus Method' Keyword for Method Invocation and Return Value Retrieval
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=local

   ${ret}=    Call Dbus Method    test_dbus    Hello    World
   Log To Console    ${ret}

   Disconnect    test_dbus

Testing a DBus Service on a Remote System
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=remote
   ...        host=172.17.0.2
   ...        port=2507

   Set Signal Received Handler    conn_name=test_dbus
   ...                            signal=RedMessage
   ...                            handler=On Received Red Signal

   Log To Console    The test is continuing...

   Sleep    10s

   Disconnect    test_dbus

*** Keyword ***
On Received Red Signal
   [Arguments]    ${arg1}=default 1
   log to console      Client received red signal. Payload: ${arg1}
   Unset Signal Received Handler    conn_name=test_dbus    signal=RedMessage    handler=On Received Red Signal


