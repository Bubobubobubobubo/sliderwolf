from ..domain.interfaces import BankRepository, MIDIPort
from ..domain.models import AppState, Bank, MIDIChannel, MIDIMessage, Parameter


class BankService:
    def __init__(self, repository: BankRepository):
        self._repository = repository

    def load_banks(self) -> dict[str, Bank]:
        return self._repository.load_banks()

    def save_banks(self, banks: dict[str, Bank]) -> None:
        self._repository.save_banks(banks)

    def create_bank(self, name: str) -> Bank:
        return Bank(name=name)

    def get_preferred_midi_port(self) -> str | None:
        return self._repository.get_preferred_midi_port()

    def set_preferred_midi_port(self, port: str) -> None:
        self._repository.set_preferred_midi_port(port)


class MIDIService:
    def __init__(self, midi_port: MIDIPort):
        self._midi_port = midi_port

    def connect_to_port(self, port_name: str) -> bool:
        return self._midi_port.connect(port_name)

    def connect_to_first_available(self) -> bool:
        available_ports = self._midi_port.get_available_ports()
        if available_ports:
            return self._midi_port.connect(available_ports[0])
        return False

    def disconnect(self) -> None:
        self._midi_port.disconnect()

    def send_parameter_change(self, parameter: Parameter) -> bool:
        message = MIDIMessage(
            channel=parameter.channel,
            control_number=parameter.control_number,
            value=parameter.value,
        )
        return self._midi_port.send_message(message)

    def get_available_ports(self) -> list[str]:
        return self._midi_port.get_available_ports()

    def get_connected_port_name(self) -> str:
        return self._midi_port.get_connected_port_name()

    def is_connected(self) -> bool:
        return self._midi_port.is_connected()


class ParameterService:
    def __init__(self, bank_service: BankService, midi_service: MIDIService):
        self._bank_service = bank_service
        self._midi_service = midi_service

    def update_parameter_value(
        self, state: AppState, index: int, new_value: int
    ) -> AppState:
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
