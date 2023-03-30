import mido
from .bank import Bank

__all__ = ("MIDI",)

class MIDI:
    """
    MIDI Interface for the application
    """

    def __init__(self):
        self.connected_port = None

        self.connect_first_available()

    def connect_by_user_input(self, port_name):
        try:
            self.connect_by_name(port_name)
            # Update preferred MIDI port in the Bank object
            bank_manager = Bank()
            bank_manager.preferred_midi_port = port_name
            bank_manager.save_banks()
        except (IOError, ValueError) as e:
            print(f"Error connecting to MIDI port: {port_name}")
            print(str(e))

    def connect_first_available(self):
        available_ports = mido.get_input_names()
        if available_ports:
            self.connect_by_name(available_ports[0])
        else:
            print("No available MIDI ports found.")

    def get_connected_port_name(self):
        """
        Get the name of the connected MIDI port
        """
        return self.connected_port.name if self.connected_port else "No MIDI port connected"

    def get_available_ports(self):
        """
        Returns a list of available MIDI ports
        """
        return mido.get_output_names()

    def connect_by_name(self, port_name):
        try:
            self.connected_port = mido.open_ioport(port_name)
        except (IOError, ValueError) as e:
            pass


    def send_control_message(self, channel, control, value):
        if self.connected_port is not None:
            message = mido.Message("control_change", channel=channel, control=control, value=value)
            self.connected_port.send(message)
        else:
            print("No connected MIDI port. Cannot send control message.")
