from .utils import clamp
from .midi import MIDI
from typing import Any, Dict, List
from .bank import Bank
import curses
import sys

__all__ = ("Application",)

# Constants
GRID_SIZE = 8
MAX_PARAMS = 64
MIDI_VALUE_MIN = 0
MIDI_VALUE_MAX = 127
MIDI_CHANNEL_MIN = 0
MIDI_CHANNEL_MAX = 15
PARAM_NAME_MAX_LENGTH = 3


class Application:
    """
    This class represents the main application for editing MIDI parameters.

    Attributes:
        bank_manager (Bank): An instance of the `Bank` class to manage the MIDI parameter banks.
        banks (Dict[str, Any]): A dictionary of the available MIDI parameter banks.
        current_bank (str): The name of the currently active MIDI parameter bank.
        cursor_x (int): The current x position of the cursor.
        cursor_y (int): The current y position of the cursor.
        screen_width (int): The width of the application screen.
        screen_height (int): The height of the application screen.
        midi_interface (MIDI): An instance of the `MIDI` class to interface with the MIDI device.

    Methods:
        __init__(): Initialize the `Application` class with default settings.
        screen_setup(stdscr: Any): Set up the terminal screen for drawing the application.
        draw_box(stdscr: Any): Draw a box around the application area.
        get_param_value(stdscr: Any, y: int, x: int, default_value, midi_param: bool = False) -> int:
            Get a parameter value from user input and update the screen accordingly.
        on_parameter_change(param_name: str, channel: int, control_number: int, value: int) -> None:
            Display the updated parameter information in the terminal.
        application_loop(stdscr: Any) -> None:
            Main loop that runs the application and handles user input.

    """

    def __init__(self) -> None:
        self.bank_manager = Bank()
        self.banks = self.bank_manager.bank
        self.current_bank = "XXX"
        self.cursor_x: int = 0
        self.cursor_y: int = 0
        self.screen_width: int = 0
        self.screen_height: int = 0

        # Connect to the MIDI port
        self.midi_interface = MIDI()

        # Attempt to connect to the preferred MIDI port
        preferred_midi_port = self.bank_manager.preferred_midi_port
        if preferred_midi_port:
            try:
                self.midi_interface.connect_by_name(preferred_midi_port)
            except ConnectionError as e:
                print(f"Warning: {str(e)}. Trying other available ports...")
        # If there is no preferred MIDI port, connect to the first available port
        else:
            if not self.midi_interface.connect_first_available():
                print("Warning: Could not connect to any MIDI port. MIDI functionality will be disabled.")

    def _cleanup(self) -> None:
        """Clean up resources before exiting"""
        if hasattr(self, 'midi_interface') and self.midi_interface:
            self.midi_interface.close()
        if hasattr(self, 'bank_manager') and self.bank_manager:
            self.bank_manager.save_banks()

    def _validate_midi_value(self, value_str: str, default: int = 0) -> int:
        """Validate and clamp MIDI values (0-127)"""
        try:
            value = int(value_str.strip())
            return clamp(value, MIDI_VALUE_MIN, MIDI_VALUE_MAX)
        except (ValueError, TypeError):
            return default

    def _validate_channel(self, value_str: str, default: int = 0) -> int:
        """Validate and clamp MIDI channel values (0-15)"""
        try:
            value = int(value_str.strip())
            return clamp(value, MIDI_CHANNEL_MIN, MIDI_CHANNEL_MAX)
        except (ValueError, TypeError):
            return default

    def _validate_param_name(self, name_str: str) -> str:
        """Validate parameter name (3 chars, alphanumeric)"""
        if isinstance(name_str, str):
            cleaned = name_str.strip().upper()[:PARAM_NAME_MAX_LENGTH]
            if cleaned.isalnum() and len(cleaned) > 0:
                return cleaned
        return ""

    def screen_setup(self, stdscr: Any) -> None:
        """
        Set up the terminal screen for drawing the application.

        Args:
            stdscr: The curses standard screen object.
        """
        curses.curs_set(2)
        stdscr.timeout(-1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        self.screen_height, self.screen_width = stdscr.getmaxyx()
        self.cursor_x = self.screen_width // 2 - 16
        self.cursor_y = self.screen_height // 2 - 4

    def _draw_interface(self, stdscr: Any) -> None:
        """Draw the main interface elements"""
        stdscr.erase()
        curses.curs_set(1)
        self.draw_box(stdscr)

        start_y = max((self.screen_height - GRID_SIZE) // 2, 1)
        start_x = max((self.screen_width - (GRID_SIZE * 4)) // 2, 1)

        # Show MIDI port info
        midi_port = self.midi_interface.get_connected_port_name()
        stdscr.addstr(start_y + 10, start_x, f"MIDI Port: {midi_port}")

        # Show current bank
        stdscr.attron(curses.color_pair(1))
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(start_y - 1, start_x, f"BANK: {self.current_bank}", curses.A_STANDOUT)
        stdscr.attroff(curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        self._draw_grid(stdscr, start_y, start_x)
        self._draw_cursor(stdscr, start_y, start_x)

    def _draw_grid(self, stdscr: Any, start_y: int, start_x: int) -> None:
        """Draw the parameter grid"""
        params = self.banks[self.current_bank]["params"]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                index = y * GRID_SIZE + x
                if index < len(params):
                    param = params[index]
                    stdscr.addstr(start_y + y, start_x + x * 4, param)

    def _draw_cursor(self, stdscr: Any, start_y: int, start_x: int) -> None:
        """Draw the cursor and parameter info"""
        params = self.banks[self.current_bank]["params"]
        param_values = self.banks[self.current_bank]["values"]

        cursor_index = self.cursor_y * GRID_SIZE + self.cursor_x
        cursor_param = None
        if 0 <= cursor_index < len(params) and cursor_index < MAX_PARAMS:
            cursor_param = params[cursor_index]

        if cursor_param is not None:
            cursor_value = f"{param_values.get(cursor_param, 0): >3}"
            stdscr.addstr(
                start_y + self.cursor_y,
                start_x + self.cursor_x * 4,
                cursor_value,
                curses.A_REVERSE,
            )

            cursor_channel = self.banks[self.current_bank]["channels"].get(cursor_param, 0)
            cursor_control_number = self.banks[self.current_bank]["control_numbers"].get(cursor_param, 0)
            stdscr.addstr(
                start_y + 9,
                start_x,
                f"Channel: {cursor_channel} Control Number: {cursor_control_number}",
            )

    def draw_box(self, stdscr: Any) -> None:
        """
        Draw a box around the application area.

        Args:
            stdscr: The curses standard screen object.
        """
        stdscr.border(0)

    @classmethod
    def get_param_value(
        cls, stdscr: Any, y: int, x: int, default_value, midi_param: bool = False
    ) -> int:
        """
        Prompt the user to enter a value for a MIDI parameter and return the input value.

        Args:
            stdscr: The curses standard screen object.
            y: The y coordinate for the user input.
            x: The x coordinate for the user input.
            default_value: The default value to return if no input is provided.
            midi_param: A boolean flag that indicates whether the parameter is a MIDI parameter.
                If True, the method will allow longer input values to be entered.

        Returns:
            int: The user input value or the default value if no input is provided.
        """
        stdscr.move(y, x)
        curses.echo()
        if not midi_param:
            value = stdscr.getstr(y, x, 3).decode("utf-8")
        else:
            value = stdscr.getstr(y, x, 40).decode("utf-8")
        curses.noecho()
        return value or default_value

    def on_parameter_change(
        self, param_name: str, channel: int, control_number: int, value: int
    ) -> None:
        """
        Display the updated parameter information in the terminal.

        Args:
            param_name: The name of the parameter being changed.
            channel: The MIDI channel of the parameter.
            control_number: The control number of the parameter.
            value: The new value of the parameter.
        """
        self.midi_interface.send_control_message(channel, control_number, value)

    def application_loop(self, stdscr: Any) -> None:
        """
        Main event loop for the application.

        Args:
            stdscr (curses.window): A curses window object representing the entire screen.

        Returns:
            None

        This method controls the application's main event loop, which draws the interface on the screen and listens for user input.
        It uses the curses library to handle the screen drawing and user input.

        The loop runs indefinitely until the user quits the application by pressing the 'q' key.

        The method begins by erasing the entire screen, setting the cursor to be visible, and drawing a box around the main application area.

        It then calculates the starting coordinates for drawing the 8x8 grid of parameter values, and displays the current MIDI port being used by the application.

        The method then draws the parameter grid on the screen, highlighting the currently selected parameter with a reverse video effect.
        It captures user input from the keyboard, and updates the grid and parameter values based on the user's input.
        The following keys can be used to interact with the grid:

        - Arrow keys: Move the cursor to a different parameter.
        - 'v': Change the value of the currently selected parameter.
        - '+': Increment the value of the currently selected parameter.
        - '-': Decrement the value of the currently selected parameter.
        - 'r': Rename the currently selected parameter.
        - 'n': Enter a new MIDI control number for the currently selected parameter.
        - 'c': Enter a new MIDI channel for the currently selected parameter.
        - 'm': Change the MIDI port being used by the application.
        - 'x': Resets the entire bank.
        - 'q': Quit the application.

        The method also handles resizing of the terminal window, saves the current bank of parameter values periodically, and refreshes the screen to display any updates.
        """
        curses.start_color()
        curses.use_default_colors()

        while True:
            self._draw_interface(stdscr)

            # Get current parameter info for input handling
            start_y = max((self.screen_height - GRID_SIZE) // 2, 1)
            start_x = max((self.screen_width - (GRID_SIZE * 4)) // 2, 1)

            params = self.banks[self.current_bank]["params"]
            param_values = self.banks[self.current_bank]["values"]
            cursor_index = self.cursor_y * GRID_SIZE + self.cursor_x
            cursor_param = None
            if 0 <= cursor_index < len(params) and cursor_index < MAX_PARAMS:
                cursor_param = params[cursor_index]

            if cursor_param is not None:
                cursor_channel = self.banks[self.current_bank]["channels"].get(cursor_param, 0)
                cursor_control_number = self.banks[self.current_bank]["control_numbers"].get(cursor_param, 0)

            # Capture user input
            key = stdscr.getch()

            # Update cursor position based on arrow keys
            if key == curses.KEY_UP and self.cursor_y > 0:
                self.cursor_y -= 1
            elif key == curses.KEY_DOWN and self.cursor_y < GRID_SIZE - 1:
                self.cursor_y += 1
            elif key == curses.KEY_LEFT and self.cursor_x > 0:
                self.cursor_x -= 1
            elif key == curses.KEY_RIGHT and self.cursor_x < GRID_SIZE - 1:
                self.cursor_x += 1
            elif key == ord("v"):  # Change value
                curses.curs_set(0)
                stdscr.addstr(
                    start_y + self.cursor_y, start_x + self.cursor_x * 4, "   "
                )
                new_value_str = self.get_param_value(
                    stdscr,
                    start_y + self.cursor_y,
                    start_x + self.cursor_x * 4,
                    str(param_values.get(cursor_param, 0)),
                )[:3]
                new_value = self._validate_midi_value(new_value_str, param_values.get(cursor_param, 0))
                param_values[cursor_param] = new_value
                self.on_parameter_change(
                    cursor_param, cursor_channel, cursor_control_number, new_value
                )
                curses.curs_set(2)
            elif key == ord("+") or key == ord("="):  # Increment value
                curses.curs_set(0)
                param_values[cursor_param] = clamp(
                    param_values.get(cursor_param, 0) + 1, 0, 127
                )
                self.on_parameter_change(
                    cursor_param,
                    cursor_channel,
                    cursor_control_number,
                    param_values[cursor_param],
                )
                curses.curs_set(2)
            elif key == ord("-"):  # Decrement value
                curses.curs_set(0)
                param_values[cursor_param] = clamp(
                    param_values.get(cursor_param, 0) - 1, 0, 127
                )
                self.on_parameter_change(
                    cursor_param,
                    cursor_channel,
                    cursor_control_number,
                    param_values[cursor_param],
                )
                curses.curs_set(2)
            elif key == ord("r"):  # Rename parameter
                curses.curs_set(0)
                new_name_str = self.get_param_value(
                    stdscr,
                    start_y + self.cursor_y,
                    start_x + self.cursor_x * 4,
                    cursor_param,
                )[:3]
                new_name = self._validate_param_name(new_name_str)
                if new_name:
                    old_index = params.index(cursor_param)
                    params[old_index] = new_name
                    if cursor_param in param_values:
                        param_values[new_name] = param_values.pop(cursor_param)

                    self.banks[self.current_bank]["channels"][new_name] = self.banks[
                        self.current_bank
                    ]["channels"].pop(cursor_param, 0)
                    self.banks[self.current_bank]["control_numbers"][
                        new_name
                    ] = self.banks[self.current_bank]["control_numbers"].pop(
                        cursor_param, 0
                    )
                    cursor_param = new_name
                curses.curs_set(2)
            elif key == ord("n"):  # Enter control number
                curses.curs_set(0)
                new_control_str = self.get_param_value(
                    stdscr, start_y + 9, start_x + 27, str(cursor_control_number)
                )
                new_control_number = self._validate_midi_value(new_control_str, cursor_control_number)
                self.banks[self.current_bank]["control_numbers"][
                    cursor_param
                ] = new_control_number
                curses.curs_set(2)
            elif key == ord("c"):  # Enter channel
                curses.curs_set(0)
                new_channel_str = self.get_param_value(
                    stdscr, start_y + 9, start_x + 9, str(cursor_channel)
                )
                new_channel = self._validate_channel(new_channel_str, cursor_channel)
                self.banks[self.current_bank]["channels"][
                    cursor_param
                ] = new_channel
                curses.curs_set(2)
            elif key == ord("m"):  # Enter MIDI port
                curses.curs_set(0)
                stdscr.addstr(
                    start_y + 10,
                    start_x + 11,
                    " " * len(self.midi_interface.get_connected_port_name()),
                )
                new_midi_port = self.get_param_value(
                    stdscr,
                    start_y + 10,
                    start_x + 12,
                    "",
                    midi_param=True,
                )
                if new_midi_port.strip() and self.midi_interface.connect_by_user_input(new_midi_port):
                    self.bank_manager.preferred_midi_port = new_midi_port
                    self.bank_manager.save_banks()
                else:
                    stdscr.addstr(start_y + 11, start_x, "Failed to connect to MIDI port")
                    stdscr.getch()  # Wait for user acknowledgment
                curses.curs_set(2)
            elif key == ord("q"):  # Quit
                stdscr.addstr(start_y + 11, start_x, "Do you want to quit? (y/n): ")
                if stdscr.getch() == ord("y"):
                    self._cleanup()
                    exit()
            elif key == ord("b"):  # Switch bank
                # Get the new bank name from the user
                curses.curs_set(0)
                stdscr.addstr(start_y - 1, start_x + 5, " " * 10)
                new_bank_name_str = self.get_param_value(
                    stdscr, start_y - 1, start_x + 6, ""
                )
                new_bank_name = self._validate_param_name(new_bank_name_str)
                if new_bank_name:
                    if new_bank_name not in self.banks:
                        # Initialize a new bank if it doesn't exist
                        self.banks[new_bank_name] = {
                            "params": [f"P{index:02}" for index in range(MAX_PARAMS)],
                            "values": {
                                param: 0
                                for param in [f"P{index:02}" for index in range(MAX_PARAMS)]
                            },
                            "channels": {
                                param: 0
                                for param in [f"P{index:02}" for index in range(MAX_PARAMS)]
                            },
                            "control_numbers": {
                                param: 0
                                for param in [f"P{index:02}" for index in range(MAX_PARAMS)]
                            },
                        }
                    self.current_bank = new_bank_name
                curses.curs_set(2)
            elif key == ord("x"):  # Reset bank parameters, names, control numbers and channels
                bank = self.banks[self.current_bank]
                for i in range(len(bank["params"])):
                    param = bank["params"][i]
                    bank["values"][param] = 0
                    bank["channels"][param] = 0
                    bank["control_numbers"][param] = 0
                    bank["params"][i] = f"P{i:02}"
                curses.curs_set(2)

            # Handle terminal resize
            new_height, new_width = stdscr.getmaxyx()
            if new_height != self.screen_height or new_width != self.screen_width:
                self.screen_height = new_height
                self.screen_width = new_width

            # Save every few cycles around
            self.bank_manager.save_banks()

            # Refresh and increment the rate
            stdscr.refresh()
