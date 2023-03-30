from .utils import clamp
from .midi import MIDI
from typing import Any
from .bank import Bank
import curses

__all__ = ("Application",)


class Application():
    """
    Main application class that handles user interface for editing MIDI parameters.
    """

    def __init__(self) -> None:
        """
        Initialize the Application class with default settings.
        """
        self.bank_manager = Bank()
        self.banks = self.bank_manager.bank
        self.current_bank = "default"
        self.cursor_x: int = 0
        self.cursor_y: int = 0
        self.screen_width: int = 0
        self.screen_height: int = 0

    def screen_setup(self, stdscr: Any) -> None:
        """
        Set up the terminal screen for drawing the application.
    
        Args:
            stdscr: The curses standard screen object.
        """
        curses.curs_set(2)
        # stdscr.nodelay(0)
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
    def get_param_value(cls, stdscr: Any, y: int, x: int, default_value) -> int:
        """
        Get a parameter value from user input and update the screen accordingly.
    
        Args:
            stdscr: The curses standard screen object.
            y: The y coordinate for the user input.
            x: The x coordinate for the user input.
            default_value: The default value to return if no input is provided.
    
        Returns:
            int: The user input value or the default value if no input is provided.
        """
        stdscr.move(y, x)
        curses.echo()
        value = stdscr.getstr(y, x, 3).decode("utf-8")
        curses.noecho()
        return value or default_value


    @classmethod
    def on_parameter_change(cls, param_name: str, channel: int, control_number: int, value: int) -> None:
        """
        Display the updated parameter information in the terminal.
    
        Args:
            param_name: The name of the parameter being changed.
            channel: The MIDI channel of the parameter.
            control_number: The control number of the parameter.
            value: The new value of the parameter.
        """
        print(
            f"Parameter {param_name} (Channel: {channel}, Control Number: {control_number}) changed to {value}"
        )

    def application_loop(self, stdscr: Any) -> None:
        """
        Main event loop for the Curses application. Draws the screen, updates information,
        and handles user input. The mechanism will also be in charge of auto-saving application state
        every now and then.
    
        Args:
            stdscr: The curses standard screen object.
        """
        # Set up the screen
        self.screen_setup(stdscr)
    
        # Set up color pairs
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    
        while True:
            stdscr.clear()
            curses.curs_set(1)  # Make the cursor visible
    
            # Draw a box around the application area
            self.draw_box(stdscr)
    
            # Center the application in the terminal
            center_y = self.screen_height // 2
            center_x = self.screen_width // 2
    
            # Show current bank
            stdscr.attron(curses.color_pair(1))
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(center_y - 5, center_x - 16, f"BANK: {self.current_bank}")
            stdscr.attroff(curses.A_BOLD)
            stdscr.attroff(curses.color_pair(1))
    
            # Draw the 8x8 grid
            params = self.banks[self.current_bank]["params"]
            param_values = self.banks[self.current_bank]["values"]
    
            for y in range(8):
                for x in range(8):
                    index = y * 8 + x
                    param = params[index]
                    stdscr.addstr(center_y - 4 + y, center_x - 16 + x * 4, param)
    
            # Draw the cursor
            cursor_index = self.cursor_y * 8 + self.cursor_x
            cursor_param = None
            if cursor_index < len(params):
                cursor_param = params[cursor_index]
            if cursor_param is not None:
                cursor_value = f"{param_values[cursor_param]: >3}"
                stdscr.addstr(center_y - 4 + self.cursor_y, center_x - 16 + self.cursor_x * 4, cursor_value, curses.A_REVERSE)
    
                cursor_channel = self.banks[self.current_bank]["channels"][cursor_param]
                cursor_control_number = self.banks[self.current_bank]["control_numbers"][cursor_param]
                stdscr.addstr(
                    center_y + 5,
                    center_x - 16,
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
                new_value = self.get_param_value(
                    stdscr, center_y - 4 + self.cursor_y, center_x - 16 + self.cursor_x * 4, param_values[cursor_param]
                )[:3]
                new_value = clamp(int(new_value), 0, 127)
                param_values[cursor_param] = new_value
                self.on_parameter_change(
                    cursor_param, cursor_channel, cursor_control_number, new_value
                )
                curses.curs_set(2)
            elif key == ord("r"):  # Rename parameter
                curses.curs_set(0)
                new_name = self.get_param_value(
                    stdscr, self.cursor_y + 1, self.cursor_x * 4, cursor_param
                )[:3].upper()
                if len(new_name) == 3 and new_name.isalpha():
                    old_index = params.index(cursor_param)
                    params[old_index] = new_name
                    param_values[new_name] = param_values.pop(cursor_param)
                    self.banks[self.current_bank]["channels"][new_name] = self.banks[self.current_bank][
                        "channels"
                    ].pop(cursor_param)
                    self.banks[self.current_bank]["control_numbers"][new_name] = self.banks[
                        self.current_bank
                    ]["control_numbers"].pop(cursor_param)
                    cursor_param = new_name
                curses.curs_set(2)
            elif key == ord("n"):  # Enter control number
                curses.curs_set(0)
                new_control_number = self.get_param_value(
                    stdscr, center_y + 5, center_x + 4, str(cursor_control_number)
                )
                new_control_number = clamp(int(new_control_number), 0, 127)
                self.banks[self.current_bank]["control_numbers"][
                    cursor_param
                ] = new_control_number
                curses.curs_set(2)
            elif key == ord("c"):  # Enter channel
                curses.curs_set(0)
                new_channel = self.get_param_value(stdscr, 10, 9, str(cursor_channel))
                new_channel = clamp(int(new_channel), 0, 15)
                self.banks[self.current_bank]["channels"][cursor_param] = new_channel
                curses.curs_set(2)
            elif key == ord("q"):  # Quit
                stdscr.addstr(center_y + 7, center_x - 16, "Do you want to quit? (y/n): ")
                if stdscr.getch() == ord("y"):
                    exit()
            elif key == ord("b"):  # Switch bank
                # Get the new bank name from the user
                curses.curs_set(0)
                stdscr.addstr(center_y - 5, center_x - 16, " " * 10)
                new_bank_name = self.get_param_value(stdscr, center_y - 5, center_x - 11, "").upper()

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
