from .utils import clamp
from .midi import MIDI
from typing import Any
from .bank import Bank
import curses
import sys

__all__ = ("Application",)


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
            except Exception as e:
                print(
                    f"Failed to connect to the preferred MIDI port: {preferred_midi_port}"
                )
                print(str(e))
        # If there is no preferred MIDI port, connect to the first available port
        else:
            ports = self.midi_interface.get_available_ports()
            if ports:
                try:
                    self.midi_interface.connect_by_name(ports[0])
                except Exception as e:
                    print(
                        f"Failed to connect to the first available MIDI port: {ports[0]}"
                    )
                    print(str(e))
            else:
                print("No MIDI ports available")
                sys.exit(1)

    def screen_setup(self, stdscr: Any) -> None:
        """
        Set up the terminal screen for drawing the application.

        Args:
            stdscr: The curses standard screen object.
        """
        curses.curs_set(2)
        # stdscr.nodelay(0)
        stdscr.timeout(-1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        self.screen_height, self.screen_width = stdscr.getmaxyx()
        self.cursor_x = self.screen_width // 2 - 16
        self.cursor_y = self.screen_height // 2 - 4

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
        - 'q': Quit the application.

        The method also handles resizing of the terminal window, saves the current bank of parameter values periodically, and refreshes the screen to display any updates.
        """

        while True:
            stdscr.erase()
            curses.curs_set(1)
            # Draw a box around the application area
            self.draw_box(stdscr)

            # Calculate the starting coordinates for drawing the grid
            start_y = max((self.screen_height - 8) // 2, 1)
            start_x = max((self.screen_width - 32) // 2, 1)

            midi_port = self.midi_interface.get_connected_port_name()
            stdscr.addstr(
                start_y + 10,
                start_x,
                f"MIDI Port: {midi_port}",
            )

            # Show current bank
            stdscr.attron(curses.color_pair(1))
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(start_y - 1, start_x, f"BANK: {self.current_bank}")
            stdscr.attroff(curses.A_BOLD)
            stdscr.attroff(curses.color_pair(1))

            # Draw the 8x8 grid
            params = self.banks[self.current_bank]["params"]
            param_values = self.banks[self.current_bank]["values"]

            for y in range(8):
                for x in range(8):
                    index = y * 8 + x
                    param = params[index]
                    stdscr.addstr(start_y + y, start_x + x * 4, param)

            # Draw the cursor
            cursor_index = self.cursor_y * 8 + self.cursor_x
            cursor_param = None
            if cursor_index < len(params):
                cursor_param = params[cursor_index]
            if cursor_param is not None:
                cursor_value = f"{param_values[cursor_param]: >3}"
                stdscr.addstr(
                    start_y + self.cursor_y,
                    start_x + self.cursor_x * 4,
                    cursor_value,
                    curses.A_REVERSE,
                )

                cursor_channel = self.banks[self.current_bank]["channels"][cursor_param]
                cursor_control_number = self.banks[self.current_bank][
                    "control_numbers"
                ][cursor_param]
                stdscr.addstr(
                    start_y + 9,
                    start_x,
                    f"Channel: {cursor_channel} Control Number: {cursor_control_number}",
                )

                try:
                    midi_port = self.bank_manager.bank["preferred_midi_port"]
                except KeyError:
                    pass  # TODO: FIX ME
                cursor_channel = self.banks[self.current_bank]["channels"][cursor_param]
                cursor_control_number = self.banks[self.current_bank][
                    "control_numbers"
                ][cursor_param]
                stdscr.addstr(
                    start_y + 9,
                    start_x,
                    f"Channel: {cursor_channel} Control Number: {cursor_control_number}",
                )

            # Capture user input
            key = stdscr.getch()

            # Update cursor position based on arrow keys
            if key == curses.KEY_UP and self.cursor_y > 0:
                self.cursor_y -= 1
            elif key == curses.KEY_DOWN and self.cursor_y < 7:
                self.cursor_y += 1
            elif key == curses.KEY_LEFT and self.cursor_x > 0:
                self.cursor_x -= 1
            elif key == curses.KEY_RIGHT and self.cursor_x < 7:
                self.cursor_x += 1
            elif key == ord("v"):  # Change value
                curses.curs_set(0)
                stdscr.addstr(
                    start_y + self.cursor_y, start_x + self.cursor_x * 4, "   "
                )
                new_value = self.get_param_value(
                    stdscr,
                    start_y + self.cursor_y,
                    start_x + self.cursor_x * 4,
                    param_values[cursor_param],
                )[:3]
                try:
                    new_value = clamp(int(new_value), 0, 127)
                    param_values[cursor_param] = new_value
                except ValueError:
                    pass
                self.on_parameter_change(
                    cursor_param, cursor_channel, cursor_control_number, new_value
                )
                curses.curs_set(2)
            elif key == ord("+") or key == ord("="):  # Increment value
                curses.curs_set(0)
                param_values[cursor_param] = clamp(
                    param_values[cursor_param] + 1, 0, 127
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
                    param_values[cursor_param] - 1, 0, 127
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
                new_name = self.get_param_value(
                    stdscr,
                    start_y + self.cursor_y,
                    start_x + self.cursor_x * 4,
                    cursor_param,
                )[:3].upper()
                if len(new_name) == 3 and new_name.isalpha():
                    old_index = params.index(cursor_param)
                    params[old_index] = new_name
                    param_values[new_name] = param_values.pop(cursor_param)
                    self.banks[self.current_bank]["channels"][new_name] = self.banks[
                        self.current_bank
                    ]["channels"].pop(cursor_param)
                    self.banks[self.current_bank]["control_numbers"][
                        new_name
                    ] = self.banks[self.current_bank]["control_numbers"].pop(
                        cursor_param
                    )
                    cursor_param = new_name
                curses.curs_set(2)
            elif key == ord("n"):  # Enter control number
                curses.curs_set(0)
                new_control_number = self.get_param_value(
                    stdscr, start_y + 9, start_x + 27, str(cursor_control_number)
                )
                new_control_number = clamp(int(new_control_number), 0, 127)
                self.banks[self.current_bank]["control_numbers"][
                    cursor_param
                ] = new_control_number
                curses.curs_set(2)
            elif key == ord("c"):  # Enter channel
                curses.curs_set(0)
                new_channel = self.get_param_value(
                    stdscr, start_y + 9, start_x + 9, str(cursor_channel)
                )
                try:
                    new_channel = clamp(int(new_channel), 0, 15)
                    self.banks[self.current_bank]["channels"][
                        cursor_param
                    ] = new_channel
                except ValueError:
                    pass
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
                    str(cursor_channel),
                    midi_param=True,
                )
                self.midi_interface.connect_by_user_input(new_midi_port)
                self.bank_manager.preferred_midi_port = new_midi_port # <-- Add this line to update the preferred MIDI port
                self.bank_manager.save_banks()
                curses.curs_set(2)
            elif key == ord("q"):  # Quit
                stdscr.addstr(start_y + 11, start_x, "Do you want to quit? (y/n): ")
                if stdscr.getch() == ord("y"):
                    exit()
            elif key == ord("b"):  # Switch bank
                # Get the new bank name from the user
                curses.curs_set(0)
                stdscr.addstr(start_y - 1, start_x + 5, " " * 10)
                new_bank_name = self.get_param_value(
                    stdscr, start_y - 1, start_x + 6, ""
                ).upper()

                if new_bank_name.isalpha():
                    if new_bank_name not in self.banks:
                        # Initialize a new bank if it doesn't exist
                        self.banks[new_bank_name] = {
                            "params": [f"P{index:02}" for index in range(64)],
                            "values": {
                                param: 0
                                for param in [f"P{index:02}" for index in range(64)]
                            },
                            "channels": {
                                param: 0
                                for param in [f"P{index:02}" for index in range(64)]
                            },
                            "control_numbers": {
                                param: 0
                                for param in [f"P{index:02}" for index in range(64)]
                            },
                        }
                    self.current_bank = new_bank_name

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
