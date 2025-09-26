import curses
import threading

from ..application.services import BankService, MIDIService, ParameterService
from ..domain.interfaces import Renderer
from ..domain.models import AppState, Bank


class InputHandler:
    def __init__(self) -> None:
        self.GRID_SIZE = 8

    def handle_navigation(self, key: int, state: AppState) -> AppState:
        new_cursor_x = state.cursor_x
        new_cursor_y = state.cursor_y

        if key == curses.KEY_UP and state.cursor_y > 0:
            new_cursor_y -= 1
        elif key == curses.KEY_DOWN and state.cursor_y < self.GRID_SIZE - 1:
            new_cursor_y += 1
        elif key == curses.KEY_LEFT and state.cursor_x > 0:
            new_cursor_x -= 1
        elif key == curses.KEY_RIGHT and state.cursor_x < self.GRID_SIZE - 1:
            new_cursor_x += 1

        return state.with_updates(cursor_x=new_cursor_x, cursor_y=new_cursor_y)

    def get_cursor_index(self, state: AppState) -> int:
        return state.cursor_y * self.GRID_SIZE + state.cursor_x

    def validate_midi_value(self, value_str: str, default: int = 0) -> int:
        try:
            value = int(value_str.strip())
            return max(0, min(127, value))
        except (ValueError, TypeError):
            return default

    def validate_channel(self, value_str: str, default: int = 0) -> int:
        try:
            value = int(value_str.strip())
            return max(0, min(15, value))
        except (ValueError, TypeError):
            return default

    def validate_param_name(self, name_str: str) -> str:
        if isinstance(name_str, str):
            cleaned = name_str.strip().upper()[:3]
            if cleaned.isalnum() and len(cleaned) > 0:
                return cleaned
        return ""


class UIController:
    def __init__(
        self,
        renderer: Renderer,
        parameter_service: ParameterService,
        bank_service: BankService,
        midi_service: MIDIService,
    ):
        self._renderer = renderer
        self._parameter_service = parameter_service
        self._bank_service = bank_service
        self._midi_service = midi_service
        self._input_handler = InputHandler()
        self._running = True
        self._pending_save: dict[str, Bank] | None = None
        self._save_timer: threading.Timer | None = None
        self._save_lock = threading.Lock()
        self._save_delay = 1.0  # seconds

    def initialize(self) -> None:
        self._renderer.initialize()

    def cleanup(self) -> None:
        self._renderer.cleanup()

    def run(self, state: AppState) -> None:
        try:
            self.initialize()
            current_state = state

            while self._running:
                # Check if we should flip the cursor display
                if current_state.should_flip_cursor_display():
                    current_state = current_state.flip_cursor_display()

                self._render_ui(current_state)

                # Use timeout for input to allow periodic display updates
                key = self._renderer.get_input()
                if key != -1:  # Only process if we got actual input
                    new_state = self._handle_input(key, current_state)

                    # Only save if banks actually changed
                    if new_state.banks != current_state.banks:
                        self._schedule_save(new_state.banks)

                    current_state = new_state

        finally:
            self._flush_pending_save()
            self.cleanup()

    def _render_ui(self, state: AppState) -> None:
        current_bank = state.banks[state.current_bank]
        midi_port = self._midi_service.get_connected_port_name()

        self._renderer.render_grid(
            current_bank,
            state.cursor_x,
            state.cursor_y,
            show_all_values=state.show_all_values,
            show_cursor_value=state.show_cursor_value,
        )
        self._renderer.render_status(state.current_bank, midi_port)
        self._renderer.render_help(state.show_help)

    def _handle_input(self, key: int, state: AppState) -> AppState:
        # Navigation
        if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            return self._input_handler.handle_navigation(key, state)

        cursor_index = self._input_handler.get_cursor_index(state)

        # Parameter value operations
        if key == ord("v"):  # Change value
            return self._handle_value_change(state, cursor_index)
        elif key == ord("+") or key == ord("="):  # Increment
            return self._handle_value_increment(state, cursor_index)
        elif key == ord("-"):  # Decrement
            return self._handle_value_decrement(state, cursor_index)

        # Parameter property changes
        elif key == ord("r"):  # Rename
            return self._handle_rename(state, cursor_index)
        elif key == ord("n"):  # Control number
            return self._handle_control_number_change(state, cursor_index)
        elif key == ord("c"):  # Channel
            return self._handle_channel_change(state, cursor_index)

        # Bank operations
        elif key == ord("b"):  # Switch bank
            return self._handle_bank_switch(state)
        elif key == ord("x"):  # Reset bank
            return self._handle_bank_reset(state)

        # MIDI operations
        elif key == ord("m"):  # Change MIDI port
            return self._handle_midi_port_change(state)

        # Help toggle
        elif key == ord("h"):  # Toggle help
            return self._handle_help_toggle(state)

        # Show all values (space bar)
        elif key == ord(" "):  # Space bar - toggle show all values
            return state.with_updates(show_all_values=not state.show_all_values)

        # Quit
        elif key == ord("q"):
            self._handle_quit()

        return state

    def _handle_value_change(self, state: AppState, index: int) -> AppState:
        current_bank = state.banks[state.current_bank]
        current_param = current_bank.get_parameter(index)

        new_value_str = self._renderer.prompt_input("New value: ", 3)
        if not new_value_str:
            return state

        new_value = self._input_handler.validate_midi_value(
            new_value_str, current_param.value
        )
        return self._parameter_service.update_parameter_value(state, index, new_value)

    def _handle_value_increment(self, state: AppState, index: int) -> AppState:
        current_bank = state.banks[state.current_bank]
        current_param = current_bank.get_parameter(index)
        new_value = min(127, current_param.value + 1)
        return self._parameter_service.update_parameter_value(state, index, new_value)

    def _handle_value_decrement(self, state: AppState, index: int) -> AppState:
        current_bank = state.banks[state.current_bank]
        current_param = current_bank.get_parameter(index)
        new_value = max(0, current_param.value - 1)
        return self._parameter_service.update_parameter_value(state, index, new_value)

    def _handle_rename(self, state: AppState, index: int) -> AppState:
        new_name = self._renderer.prompt_input("New name: ", 3)
        if not new_name:
            return state

        validated_name = self._input_handler.validate_param_name(new_name)
        if not validated_name:
            return state

        return self._parameter_service.rename_parameter(state, index, validated_name)

    def _handle_control_number_change(self, state: AppState, index: int) -> AppState:
        current_bank = state.banks[state.current_bank]
        current_param = current_bank.get_parameter(index)

        new_control_str = self._renderer.prompt_input("Control number: ", 3)
        if not new_control_str:
            return state

        new_control = self._input_handler.validate_midi_value(
            new_control_str, current_param.control_number
        )
        return self._parameter_service.update_parameter_control_number(
            state, index, new_control
        )

    def _handle_channel_change(self, state: AppState, index: int) -> AppState:
        current_bank = state.banks[state.current_bank]
        current_param = current_bank.get_parameter(index)

        new_channel_str = self._renderer.prompt_input("Channel: ", 2)
        if not new_channel_str:
            return state

        new_channel = self._input_handler.validate_channel(
            new_channel_str, current_param.channel.value
        )
        return self._parameter_service.update_parameter_channel(
            state, index, new_channel
        )

    def _handle_bank_switch(self, state: AppState) -> AppState:
        new_bank_name = self._renderer.prompt_input("Bank name: ", 3)
        if not new_bank_name:
            return state

        validated_name = self._input_handler.validate_param_name(new_bank_name)
        if not validated_name:
            return state

        new_banks = state.banks.copy()
        if validated_name not in new_banks:
            new_banks[validated_name] = self._bank_service.create_bank(validated_name)

        return state.with_updates(current_bank=validated_name, banks=new_banks)

    def _handle_bank_reset(self, state: AppState) -> AppState:
        new_banks = state.banks.copy()
        new_banks[state.current_bank] = self._bank_service.create_bank(
            state.current_bank
        )

        return state.with_updates(banks=new_banks)

    def _handle_midi_port_change(self, state: AppState) -> AppState:
        new_port = self._renderer.prompt_input("MIDI port: ", 40)
        if not new_port.strip():
            return state

        if self._midi_service.connect_to_port(new_port):
            self._bank_service.set_preferred_midi_port(new_port)
            return state.with_updates(preferred_midi_port=new_port)

        return state

    def _handle_help_toggle(self, state: AppState) -> AppState:
        return state.with_updates(show_help=not state.show_help)

    def _handle_quit(self) -> None:
        confirm = self._renderer.prompt_input("Quit? (y/n): ", 1)
        if confirm.lower() == "y":
            self._running = False

    def _schedule_save(self, banks: dict[str, Bank]) -> None:
        """Schedule a debounced save operation"""
        with self._save_lock:
            self._pending_save = banks

            if self._save_timer:
                self._save_timer.cancel()

            self._save_timer = threading.Timer(self._save_delay, self._perform_save)
            self._save_timer.start()

    def _perform_save(self) -> None:
        """Perform the actual save operation"""
        with self._save_lock:
            if self._pending_save is not None:
                self._bank_service.save_banks(self._pending_save)
                self._pending_save = None
                self._save_timer = None

    def _flush_pending_save(self) -> None:
        """Force immediate save of pending changes"""
        with self._save_lock:
            if self._save_timer:
                self._save_timer.cancel()
                self._save_timer = None

            if self._pending_save is not None:
                self._bank_service.save_banks(self._pending_save)
                self._pending_save = None
