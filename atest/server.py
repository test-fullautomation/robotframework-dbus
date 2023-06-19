from dasbus.loop import EventLoop
from dasbus.server.interface import dbus_interface, dbus_signal
from dasbus.typing import Str
from common import HELLO_WORLD, SESSION_BUS
from dasbus.xml import XMLGenerator
from dasbus.signal import Signal
from datetime import datetime
import random
import time, threading


@dbus_interface(HELLO_WORLD.interface_name)
class HelloWorld(object):
    """The DBus interface for HelloWorld."""

    def __init__(self):
        self.red_signal = Signal()
        self.green_signal = Signal()
        self.yellow_signal = Signal()
        self.red_signal.connect(self.RedMessage)
        self.green_signal.connect(self.GreenMessage)
        self.yellow_signal.connect(self.YellowMessage)

    def send_random_signal(self):
        signal_dict = {
            "red signal from server": self.red_signal,
            "green signal from server": self.green_signal,
            "yellow signal from server": self.yellow_signal}
        ls = list(signal_dict.keys())
        raise_signal_list = random.sample(ls, 3)
        for sgn in raise_signal_list:
            # print(sgn)
            now = datetime.now()
            signal_dict[sgn].emit("%s at %s" % (sgn, now))
            # time.sleep(1)

        threading.Timer(10, self.send_random_signal).start()

    @dbus_signal
    def RedMessage(self, msg: Str):
        """Signal that a message has been received."""
        print("red")

    @dbus_signal
    def GreenMessage(self, msg: Str):
        """Signal that a message has been received."""
        print("green")

    @dbus_signal
    def YellowMessage(self, msg: Str):
        """Signal that a message has been received."""
        print("yellow")

    def Hello(self, name: Str) -> Str:
        return "Hello {}!".format(name)


if __name__ == "__main__":
    # Print the generated XML specification.
    print(XMLGenerator.prettify_xml(HelloWorld.__dbus_xml__))

    try:
        # Create an instance of the class HelloWorld.
        hello_world = HelloWorld()

        # Publish the instance at /org/example/HelloWorld.
        SESSION_BUS.publish_object(HELLO_WORLD.object_path, hello_world)

        # Register the service name org.example.HelloWorld.
        SESSION_BUS.register_service(HELLO_WORLD.service_name)

        hello_world.send_random_signal()

        # Start the event loop.
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SESSION_BUS.disconnect()
