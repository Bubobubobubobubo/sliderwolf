import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MIDIChannel(int, Enum):
    """MIDI channel enumeration (0-15 corresponding to MIDI channels 1-16)."""

    CH_1 = 0
    CH_2 = 1
    CH_3 = 2
    CH_4 = 3
    CH_5 = 4
    CH_6 = 5
    CH_7 = 6
    CH_8 = 7
    CH_9 = 8
    CH_10 = 9
    CH_11 = 10
    CH_12 = 11
    CH_13 = 12
    CH_14 = 13
    CH_15 = 14
    CH_16 = 15

    @classmethod
    def from_int(cls, value: int) -> "MIDIChannel":
        """Create MIDIChannel from integer, clamped to valid range."""
        return cls(max(0, min(15, value)))


@dataclass
class Parameter:
    """A MIDI control parameter with name, value, channel, and control number."""

    name: str
    value: int = 0
    channel: MIDIChannel = MIDIChannel.CH_1
    control_number: int = 0

    def __post_init__(self) -> None:
        """Clamp values to valid ranges and truncate name to 3 characters."""
        self.value = max(0, min(127, self.value))
        self.control_number = max(0, min(127, self.control_number))
        if len(self.name) > 3:
            self.name = self.name[:3]

    def update_value(self, new_value: int) -> "Parameter":
        """Create new Parameter with updated value, clamped to 0-127 range."""
        return Parameter(
            name=self.name,
            value=max(0, min(127, new_value)),
            channel=self.channel,
            control_number=self.control_number,
        )


@dataclass
class Bank:
    """A collection of 64 parameters organized in an 8x8 grid."""

    name: str
    parameters: list[Parameter] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure bank name is 3 characters and pad parameters to 64."""
        if len(self.name) > 3:
            self.name = self.name[:3]

        while len(self.parameters) < 64:
            idx = len(self.parameters)
            self.parameters.append(Parameter(name=f"P{idx:02}"))

    def get_parameter(self, index: int) -> Parameter:
        """Get parameter by index (0-63)."""
        if 0 <= index < len(self.parameters):
            return self.parameters[index]
        raise IndexError(f"Parameter index {index} out of range")

    def update_parameter(self, index: int, parameter: Parameter) -> "Bank":
        """Create new Bank with parameter updated at given index."""
        if 0 <= index < len(self.parameters):
            new_params = self.parameters.copy()
            new_params[index] = parameter
            return Bank(name=self.name, parameters=new_params)
        raise IndexError(f"Parameter index {index} out of range")


@dataclass
class MIDIMessage:
    """A MIDI Control Change message with channel, control number, and value."""

    channel: MIDIChannel
    control_number: int
    value: int

    def __post_init__(self) -> None:
        """Clamp control number and value to valid MIDI ranges (0-127)."""
        self.control_number = max(0, min(127, self.control_number))
        self.value = max(0, min(127, self.value))


@dataclass
class AppState:
    """Application state containing current bank, cursor position, and UI settings."""

    current_bank: str = "XXX"
    banks: dict[str, Bank] = field(default_factory=dict)
    cursor_x: int = 0
    cursor_y: int = 0
    preferred_midi_port: str = ""
    show_help: bool = True
    last_flip_time: float = field(default_factory=time.time)
    show_cursor_value: bool = False
    show_all_values: bool = False
    flip_interval: float = 1.0

    def __post_init__(self) -> None:
        """Ensure at least one bank exists."""
        if not self.banks:
            default_bank = Bank(name=self.current_bank)
            self.banks[self.current_bank] = default_bank

    def should_flip_cursor_display(self) -> bool:
        """Check if enough time has passed to flip cursor display mode."""
        return time.time() - self.last_flip_time >= self.flip_interval

    def flip_cursor_display(self) -> "AppState":
        """Create new state with flipped cursor display mode."""
        return AppState(
            current_bank=self.current_bank,
            banks=self.banks,
            cursor_x=self.cursor_x,
            cursor_y=self.cursor_y,
            preferred_midi_port=self.preferred_midi_port,
            show_help=self.show_help,
            last_flip_time=time.time(),
            show_cursor_value=not self.show_cursor_value,
            show_all_values=self.show_all_values,
            flip_interval=self.flip_interval,
        )

    def with_updates(self, **kwargs: Any) -> "AppState":
        """Create new state with specified field updates."""
        return AppState(
            current_bank=kwargs.get("current_bank", self.current_bank),
            banks=kwargs.get("banks", self.banks),
            cursor_x=kwargs.get("cursor_x", self.cursor_x),
            cursor_y=kwargs.get("cursor_y", self.cursor_y),
            preferred_midi_port=kwargs.get(
                "preferred_midi_port", self.preferred_midi_port
            ),
            show_help=kwargs.get("show_help", self.show_help),
            last_flip_time=kwargs.get("last_flip_time", self.last_flip_time),
            show_cursor_value=kwargs.get("show_cursor_value", self.show_cursor_value),
            show_all_values=kwargs.get("show_all_values", self.show_all_values),
            flip_interval=kwargs.get("flip_interval", self.flip_interval),
        )
