import mido
from typing import List, Optional
from ..domain.interfaces import MIDIPort
from ..domain.models import MIDIMessage


class RTMIDIPort(MIDIPort):
    def __init__(self):
        self._connected_port: Optional[mido.ports.IOPort] = None

    def connect(self, port_name: str) -> bool:
        try:
            if self._connected_port:
                self._connected_port.close()
            self._connected_port = mido.open_ioport(port_name)
            return True
        except (IOError, ValueError) as e:
            print(f"Failed to connect to MIDI port '{port_name}': {str(e)}")
            return False

    def disconnect(self) -> None:
        if self._connected_port:
            self._connected_port.close()
            self._connected_port = None

    def send_message(self, message: MIDIMessage) -> bool:
        if not self._connected_port:
            return False

        try:
            midi_message = mido.Message(
                "control_change",
                channel=message.channel.value,
                control=message.control_number,
                value=message.value
            )
            self._connected_port.send(midi_message)
            return True
        except Exception as e:
            print(f"Failed to send MIDI message: {str(e)}")
            return False

    def get_available_ports(self) -> List[str]:
        return mido.get_output_names()

    def get_connected_port_name(self) -> str:
        if self._connected_port:
            return self._connected_port.name
        return "No MIDI port connected"

    def is_connected(self) -> bool:
        return self._connected_port is not None
