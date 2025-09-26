import mido
from .bank import Bank
from typing import List, Optional

__all__ = ("MIDI",)


class MIDI:
    """
    MIDI Interface for the application
    """

    def __init__(self) -> None:
        self.connected_port: Optional[mido.ports.IOPort] = None

        self.connect_first_available()

    def close(self):
        """Close the MIDI connection"""
        if self.connected_port:
            self.connected_port.close()
            self.connected_port = None

    def connect_by_user_input(self, port_name: str) -> bool:
        try:
            self.connect_by_name(port_name)
            # Update preferred MIDI port in the Bank object
            bank_manager = Bank()
            bank_manager.preferred_midi_port = port_name
            bank_manager.save_banks()
            return True
        except ConnectionError as e:
            return False

    def connect_first_available(self) -> bool:
        available_ports = mido.get_input_names()
        if available_ports:
            try:
                self.connect_by_name(available_ports[0])
                return True
            except ConnectionError:
                return False
        else:
            return False

    def get_connected_port_name(self) -> str:
        """
        Get the name of the connected MIDI port
        """
        return (
            self.connected_port.name
            if self.connected_port
            else "No MIDI port connected"
        )

    def get_available_ports(self) -> List[str]:
        """
        Returns a list of available MIDI ports
        """
        return mido.get_output_names()

    def connect_by_name(self, port_name: str) -> None:
        try:
            if self.connected_port:
                self.connected_port.close()
            self.connected_port = mido.open_ioport(port_name)
        except (IOError, ValueError) as e:
            raise ConnectionError(f"Failed to connect to MIDI port '{port_name}': {str(e)}")

    def send_control_message(self, channel: int, control: int, value: int) -> bool:
        if self.connected_port is not None:
            try:
                message = mido.Message(
                    "control_change", channel=channel, control=control, value=value
                )
                self.connected_port.send(message)
                return True
            except Exception as e:
                return False
        else:
            return False
