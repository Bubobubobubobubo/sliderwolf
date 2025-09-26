import sys
from .domain.models import AppState
from .application.services import BankService, MIDIService, ParameterService
from .infrastructure.storage import FileBankRepository
from .infrastructure.midi import RTMIDIPort
from .infrastructure.ui import CursesRenderer
from .presentation.controllers import UIController


class SliderWolfApp:
    def __init__(self):
        # Infrastructure
        self._bank_repository = FileBankRepository()
        self._midi_port = RTMIDIPort()
        self._renderer = CursesRenderer()

        # Services
        self._bank_service = BankService(self._bank_repository)
        self._midi_service = MIDIService(self._midi_port)
        self._parameter_service = ParameterService(self._bank_service, self._midi_service)

        # Controller
        self._ui_controller = UIController(
            self._renderer,
            self._parameter_service,
            self._bank_service,
            self._midi_service
        )

    def run(self) -> None:
        try:
            # Load initial state
            initial_state = self._load_initial_state()

            # Setup MIDI connection
            self._setup_midi_connection(initial_state)

            # Run the application
            self._ui_controller.run(initial_state)

        except KeyboardInterrupt:
            print("\nApplication interrupted by user")
        except Exception as e:
            print(f"Fatal error: {str(e)}")
        finally:
            self._cleanup()

    def _load_initial_state(self) -> AppState:
        banks = self._bank_service.load_banks()
        preferred_midi_port = self._bank_service.get_preferred_midi_port() or ""

        # Ensure we have at least one bank
        if not banks:
            default_bank = self._bank_service.create_bank("XXX")
            banks["XXX"] = default_bank

        current_bank = list(banks.keys())[0]

        return AppState(
            current_bank=current_bank,
            banks=banks,
            cursor_x=0,
            cursor_y=0,
            preferred_midi_port=preferred_midi_port,
            show_help=True,
            show_cursor_value=False,
            show_all_values=False,
            flip_interval=2.0
        )

    def _setup_midi_connection(self, state: AppState) -> None:
        # Try preferred port first
        if state.preferred_midi_port:
            if self._midi_service.connect_to_port(state.preferred_midi_port):
                return
            else:
                print(f"Warning: Could not connect to preferred MIDI port '{state.preferred_midi_port}'. Trying other ports...")

        # Try first available port
        if not self._midi_service.connect_to_first_available():
            print("Warning: Could not connect to any MIDI port. MIDI functionality will be disabled.")

    def _cleanup(self) -> None:
        try:
            self._midi_service.disconnect()
        except:
            pass


def main():
    app = SliderWolfApp()
    app.run()


if __name__ == "__main__":
    main()
