from ..domain.interfaces import BankRepository, MIDIPort
from ..domain.models import AppState, Bank, MIDIChannel, MIDIMessage, Parameter


class BankService:
    """Service for managing parameter banks and persistence."""

    def __init__(self, repository: BankRepository):
        self._repository = repository

    def load_banks(self) -> dict[str, Bank]:
        """Load all banks from storage."""
        return self._repository.load_banks()

    def save_banks(self, banks: dict[str, Bank]) -> None:
        """Save banks to storage."""
        self._repository.save_banks(banks)

    def create_bank(self, name: str) -> Bank:
        """Create a new bank with default parameters."""
        return Bank(name=name)

    def get_preferred_midi_port(self) -> str | None:
        """Get the user's preferred MIDI port name."""
        return self._repository.get_preferred_midi_port()

    def set_preferred_midi_port(self, port: str) -> None:
        """Set the user's preferred MIDI port name."""
        self._repository.set_preferred_midi_port(port)


class MIDIService:
    """Service for managing MIDI port connections and sending messages."""

    def __init__(self, midi_port: MIDIPort):
        self._midi_port = midi_port

    def connect_to_port(self, port_name: str) -> bool:
        """Connect to a specific MIDI port by name."""
        return self._midi_port.connect(port_name)

    def connect_to_first_available(self) -> bool:
        """Connect to the first available MIDI port."""
        available_ports = self._midi_port.get_available_ports()
        if available_ports:
            return self._midi_port.connect(available_ports[0])
        return False

    def disconnect(self) -> None:
        """Disconnect from current MIDI port."""
        self._midi_port.disconnect()

    def send_parameter_change(self, parameter: Parameter) -> bool:
        """Send a MIDI Control Change message for the given parameter."""
        message = MIDIMessage(
            channel=parameter.channel,
            control_number=parameter.control_number,
            value=parameter.value,
        )
        return self._midi_port.send_message(message)

    def get_available_ports(self) -> list[str]:
        """Get list of available MIDI output port names."""
        return self._midi_port.get_available_ports()

    def get_connected_port_name(self) -> str:
        """Get name of currently connected MIDI port."""
        return self._midi_port.get_connected_port_name()

    def is_connected(self) -> bool:
        """Check if connected to a MIDI port."""
        return self._midi_port.is_connected()


class ParameterService:
    """Service for parameter operations and MIDI updates."""

    def __init__(self, bank_service: BankService, midi_service: MIDIService):
        self._bank_service = bank_service
        self._midi_service = midi_service

    def update_parameter_value(
        self, state: AppState, index: int, new_value: int
    ) -> AppState:
        """Update parameter value and send MIDI message."""
        current_bank = state.banks[state.current_bank]
        parameter = current_bank.get_parameter(index)
        updated_parameter = parameter.update_value(new_value)
        updated_bank = current_bank.update_parameter(index, updated_parameter)

        new_banks = state.banks.copy()
        new_banks[state.current_bank] = updated_bank

        self._midi_service.send_parameter_change(updated_parameter)

        return state.with_updates(banks=new_banks)

    def rename_parameter(self, state: AppState, index: int, new_name: str) -> AppState:
        current_bank = state.banks[state.current_bank]
        parameter = current_bank.get_parameter(index)
        updated_parameter = Parameter(
            name=new_name,
            value=parameter.value,
            channel=parameter.channel,
            control_number=parameter.control_number,
        )
        updated_bank = current_bank.update_parameter(index, updated_parameter)

        new_banks = state.banks.copy()
        new_banks[state.current_bank] = updated_bank

        return state.with_updates(banks=new_banks)

    def update_parameter_channel(
        self, state: AppState, index: int, channel: int
    ) -> AppState:
        current_bank = state.banks[state.current_bank]
        parameter = current_bank.get_parameter(index)
        updated_parameter = Parameter(
            name=parameter.name,
            value=parameter.value,
            channel=MIDIChannel.from_int(channel),
            control_number=parameter.control_number,
        )
        updated_bank = current_bank.update_parameter(index, updated_parameter)

        new_banks = state.banks.copy()
        new_banks[state.current_bank] = updated_bank

        return state.with_updates(banks=new_banks)

    def update_parameter_control_number(
        self, state: AppState, index: int, control_number: int
    ) -> AppState:
        current_bank = state.banks[state.current_bank]
        parameter = current_bank.get_parameter(index)
        updated_parameter = Parameter(
            name=parameter.name,
            value=parameter.value,
            channel=parameter.channel,
            control_number=control_number,
        )
        updated_bank = current_bank.update_parameter(index, updated_parameter)

        new_banks = state.banks.copy()
        new_banks[state.current_bank] = updated_bank

        return state.with_updates(banks=new_banks)
