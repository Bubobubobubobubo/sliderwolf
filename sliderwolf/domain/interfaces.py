from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from .models import Bank, MIDIMessage


class BankRepository(ABC):
    @abstractmethod
    def load_banks(self) -> Dict[str, Bank]:
        pass

    @abstractmethod
    def save_banks(self, banks: Dict[str, Bank]) -> None:
        pass

    @abstractmethod
    def get_preferred_midi_port(self) -> Optional[str]:
        pass

    @abstractmethod
    def set_preferred_midi_port(self, port: str) -> None:
        pass


class MIDIPort(ABC):
    @abstractmethod
    def connect(self, port_name: str) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def send_message(self, message: MIDIMessage) -> bool:
        pass

    @abstractmethod
    def get_available_ports(self) -> List[str]:
        pass

    @abstractmethod
    def get_connected_port_name(self) -> str:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass


class Renderer(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

    @abstractmethod
    def render_grid(self, bank: Bank, cursor_x: int, cursor_y: int, show_all_values: bool = False, show_cursor_value: bool = False) -> None:
        pass

    @abstractmethod
    def render_status(self, bank_name: str, midi_port: str) -> None:
        pass

    @abstractmethod
    def render_help(self, show_help: bool) -> None:
        pass

    @abstractmethod
    def get_input(self) -> int:
        pass

    @abstractmethod
    def prompt_input(self, prompt: str, max_length: int) -> str:
        pass
