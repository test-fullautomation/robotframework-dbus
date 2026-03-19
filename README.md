# RobotFramework_DBus

[![License: Apache v2](https://img.shields.io/pypi/l/robotframework.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

**A Robot Framework library for testing D-Bus services with support for local and remote connections.**

RobotFramework_DBus provides Robot Framework keywords for interacting with [D-Bus](https://www.freedesktop.org/wiki/Software/dbus/) services on Linux systems. It supports connecting to D-Bus services, calling methods, waiting for signals, and handling signal events - both on the local machine and on remote systems via a built-in agent.

## Key Features

- **D-Bus Method Calls** - Invoke any method on a D-Bus service and retrieve return values
- **Signal Waiting (Synchronous)** - Block execution until a specific D-Bus signal is emitted, with configurable timeout
- **Signal Monitoring (Register)** - Pre-register signals for monitoring to avoid missing events during test execution
- **Signal Handlers (Asynchronous)** - Register callback keywords that execute when signals are emitted, without blocking the test
- **Multiple Connections** - Manage multiple named D-Bus connections simultaneously
- **Remote Testing** - Test D-Bus services on remote systems via the built-in DBus Client Agent

## How It Works

```
Local Mode:                          Remote Mode:

┌──────────────┐                     ┌──────────────┐
│  Robot       │                     │  Robot       │
│  Framework   │                     │  Framework   │
│  Test Suite  │                     │  Test Suite  │
└──────┬───────┘                     └──────┬───────┘
       │                                    │
┌──────▼───────┐                     ┌──────▼───────┐
│  DBusManager │                     │  DBusManager │
│  (Library)   │                     │  (Library)   │
└──────┬───────┘                     └──────┬───────┘
       │                                    │ XML-RPC
┌──────▼───────┐                     ┌──────▼───────┐
│  DBusClient  │                     │  DBusClient  │
│  (dasbus)    │                     │  Remote      │
└──────┬───────┘                     └──────┬───────┘
       │                                    │
┌──────▼───────┐                     ┌──────▼───────┐
│  D-Bus       │                     │  DBus Client │
│  Service     │                     │  Agent (SUT) │
└──────────────┘                     └──────┬───────┘
                                            │
                                     ┌──────▼───────┐
                                     │  D-Bus       │
                                     │  Service     │
                                     └──────────────┘
```

## Prerequisites

Before using RobotFramework_DBus, make sure you have the following libraries installed (Linux only):

- **pycairo** - Python bindings for the Cairo graphics library
- **PyGObject** - Python bindings for the GObject library (GTK+, GLib)
- **dasbus** - Pythonic D-Bus library that RobotFramework_DBus is built upon
- **pyinstaller** - Required if you plan to distribute the DBus Client Agent as a standalone executable

## Installation

### 1. Installation via PyPi (recommended for users)

```bash
pip install RobotFramework_DBus
```

[RobotFramework_DBus in PyPi](https://pypi.org/project/RobotFramework_DBus/)

### 2. Installation via GitHub (recommended for developers)

Clone the repository:

```bash
git clone https://github.com/test-fullautomation/robotframework-dbus.git
```

[RobotFramework_DBus in GitHub](https://github.com/test-fullautomation/robotframework-dbus)

Install dependencies:

```bash
pip install -r requirements.txt
```

Install the package:

```bash
python setup.py install
```

## Keywords

RobotFramework_DBus provides the following Robot Framework keywords:

| Keyword | Description |
|---------|-------------|
| `connect` | Establish a connection to a D-Bus service |
| `disconnect` | Disconnect from a D-Bus service |
| `call dbus method` | Call a method on a D-Bus service and get the return value |
| `wait for signal` | Wait (blocking) for a specific signal with timeout |
| `register signal` | Register signal(s) for background monitoring |
| `set signal received handler` | Register a callback keyword for a signal (non-blocking) |
| `unset signal received handler` | Remove a previously registered signal callback |

### connect

Establish a connection to a D-Bus service.

```robotframework
connect    conn_name=[connection name]
...        namespace=[namespace]
...        object_path=[object path]
...        mode=[local|remote]
...        host=[remote host]
...        port=[remote port]
```

**Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `conn_name` | str | `default_conn` | Unique identifier for this connection |
| `namespace` | str | `""` | D-Bus service namespace (e.g. `org.example.HelloWorld`) |
| `object_path` | str | `None` | D-Bus object path (e.g. `/org/example/HelloWorld`) |
| `mode` | str | `local` | Testing mode: `local` or `remote` |
| `host` | str | `localhost` | Remote host IP/hostname (only for `remote` mode) |
| `port` | int | `2507` | Remote agent port (only for `remote` mode) |

### disconnect

Disconnect from a D-Bus service by connection name. Pass `ALL` to disconnect all connections.

```robotframework
disconnect    conn_name
```

### call dbus method

Call a D-Bus method and return its result.

```robotframework
${result}=    call dbus method    [conn_name]    [method_name]    [args...]
```

### wait for signal

Wait (blocking) for a specific D-Bus signal within a timeout period. Returns the signal payloads.

```robotframework
${payloads}=    wait for signal    conn_name=[name]    signal=[signal]    timeout=[seconds]
```

### register signal

Register signal(s) for background monitoring. Multiple signals can be comma-separated.

```robotframework
register signal    conn_name=[name]    signal=Signal1,Signal2,Signal3
```

### set signal received handler

Register a Robot Framework keyword as a callback for a signal (non-blocking).

```robotframework
set signal received handler    conn_name=[name]    signal=[signal]    handler=[keyword name]
```

### unset signal received handler

Remove a previously registered signal callback.

```robotframework
unset signal received handler    conn_name=[name]    signal=[signal]    handler=[keyword name]
```

## Usage Examples

### Example 1 - Synchronized DBus Signal Waiting

Wait for a D-Bus signal using the blocking `wait for signal` keyword.

```robotframework
*** Settings ***
Library    RobotFramework_DBus.DBusManager

*** Test Cases ***
Hello World
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=local

   ${ret}=    Wait For Signal     conn_name=test_dbus
   ...                            signal=YellowMessage
   ...                            timeout=10

   Log To Console    ${ret}

   Disconnect    test_dbus
```

The `Wait for signal` keyword blocks until the `YellowMessage` signal is emitted (or the 10-second timeout is exceeded), then returns the signal payloads.

### Example 2 - Managing Multiple DBus Signals with Register Signal

Pre-register signals to avoid missing events that occur while waiting for other signals.

```robotframework
*** Settings ***
Library    RobotFramework_DBus.DBusManager

*** Test Cases ***
Hello World
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
```

By registering `GreenMessage` before waiting for `YellowMessage`, the signal is monitored in the background. If `GreenMessage` is emitted during the `YellowMessage` wait, it will be captured and returned immediately when `Wait For Signal` is called for it.

### Example 3 - Non-blocking Signal Handling with Callback

Register a keyword as a callback for signal events without blocking the test flow.

```robotframework
*** Settings ***
Library    RobotFramework_DBus.DBusManager

*** Test Cases ***
Hello World
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=local

   Set Signal Received Handler    conn_name=test_dbus
   ...                            signal=RedMessage
   ...                            handler=On Received Red Signal

   Log To Console    The test is continuing...

   Sleep    10s

   Disconnect    test_dbus

*** Keywords ***
On Received Red Signal
   [Arguments]    ${arg1}=default 1
   Log To Console    Client received red signal. Payload: ${arg1}
   Unset Signal Received Handler    conn_name=test_dbus    signal=RedMessage    handler=On Received Red Signal
```

The test continues executing immediately after `Set Signal Received Handler`. When the `RedMessage` signal is emitted, the `On Received Red Signal` keyword is called automatically. The handler should accept arguments matching the signal's payload.

### Example 4 - Calling DBus Methods

Invoke a D-Bus method and retrieve the return value.

```robotframework
*** Settings ***
Library    RobotFramework_DBus.DBusManager

*** Test Cases ***
Hello World
   connect    conn_name=test_dbus
   ...        namespace=org.example.HelloWorld
   ...        mode=local

   ${ret}=    Call Dbus Method    test_dbus    Hello    World
   Log To Console    ${ret}

   Disconnect    test_dbus
```

### Example 5 - Testing a Remote DBus Service

Test a D-Bus service running on a different machine.

**Step 1:** Start the DBus Client Agent on the remote system (SUT):

```bash
dbus_client_agent --host 0.0.0.0 --port 2507
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--host` | str | `0.0.0.0` | Host address for the agent |
| `--port` | int | `2507` | Port for the agent to listen on |

**Step 2:** On the test PC, use `remote` mode with the remote host's address:

```robotframework
*** Settings ***
Library    RobotFramework_DBus.DBusManager

*** Test Cases ***
Hello World
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

*** Keywords ***
On Received Red Signal
   [Arguments]    ${arg1}=default 1
   Log To Console    Client received red signal. Payload: ${arg1}
   Unset Signal Received Handler    conn_name=test_dbus    signal=RedMessage    handler=On Received Red Signal
```

The only difference from local testing is setting `mode=remote` and providing the `host` and `port` of the remote system.

## Project Structure

```
robotframework-dbus/
├── RobotFramework_DBus/
│   ├── __init__.py
│   ├── version.py                  # Version information
│   ├── dbus_manager.py             # Main library - Robot Framework keywords
│   ├── dbus_client.py              # Local D-Bus client (dasbus-based)
│   ├── dbus_client_remote.py       # Remote D-Bus client (XML-RPC based)
│   ├── common/
│   │   ├── priority_queue.py       # Thread-safe priority queue
│   │   ├── register_keyword.py     # RF keyword callback registration
│   │   ├── scheduled_job.py        # Periodic job scheduler
│   │   ├── thread_safe_dict.py     # Thread-safe dictionary
│   │   └── utils.py                # Utility functions
│   └── dbus_agent/
│       └── dbus_client_agent.py    # Remote agent (XML-RPC server)
├── atest/                          # Acceptance tests
├── packagedoc/                     # Package documentation sources
├── setup.py                        # Installation script
├── requirements.txt                # Python dependencies
└── LICENSE                         # Apache License 2.0
```

## Package Documentation

A detailed documentation of the RobotFramework_DBus can be found here:

[RobotFramework_DBus.pdf](https://github.com/test-fullautomation/robotframework-dbus/blob/develop/RobotFramework_DBus/RobotFramework_DBus.pdf)

## Feedback

To give us feedback, you can send an email to [Thomas Pollerspoeck](mailto:Thomas.Pollerspoeck@de.bosch.com).

In case you want to report a bug or request any interesting feature, please don't hesitate to raise a ticket.

## Maintainers

[Thomas Pollerspoeck](mailto:Thomas.Pollerspoeck@de.bosch.com)

[Nguyen Huynh Tri Cuong](mailto:cuong.nguyenhuynhtri@vn.bosch.com)

## Contributors

[Thomas Pollerspoeck](mailto:Thomas.Pollerspoeck@de.bosch.com)

[Nguyen Huynh Tri Cuong](mailto:cuong.nguyenhuynhtri@vn.bosch.com)

## License

Copyright 2020-2024 Robert Bosch GmbH

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License. You may
obtain a copy of the License at

> [![License: Apache v2](https://img.shields.io/pypi/l/robotframework.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
