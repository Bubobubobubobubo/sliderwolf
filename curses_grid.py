import curses
import random
import os
import json
from typing import Any

# Constants 
BANKS_FILE_PATH = os.path.join(
        os.path.expanduser("~"),
        ".local", "share", "FD5",
        "banks.json")

def save_banks(bank_location: str):
    """
    Save the current bank as JSON in the BANKS_FILE_PATH
    folder. 
    """
    with open(BANKS_FILE_PATH, "w") as f:
        json.dump(banks, f)

def load_banks(bank_location: str):
    """
    Load the bank from the BANKS_FILE_PATH file, typically
    found in (./local/share/DE5). If no file is found, it
    will return a default bank.
    """
    if os.path.exists(BANKS_FILE_PATH):
        with open(BANKS_FILE_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error loading banks from {BANKS_FILE_PATH}: {e}")
    else:
        os.makedirs(os.path.dirname(BANKS_FILE_PATH), exist_ok=True)

    return {
        "default": {
            "params": [f"P{index:02}" for index in range(64)],
            "values": {param: 0 for param in [f"P{index:02}" for index in range(64)]},
            "channels": {param: 0 for param in [f"P{index:02}" for index in range(64)]},
            "control_numbers": {param: 0 for param in [f"P{index:02}" for index in range(64)]}
        }
    }



def get_param_value(stdscr, y, x, default_value):
    """
    Get a parameter value and update the screen accordingly.
    """
    stdscr.move(y, x)
    curses.echo()
    value = stdscr.getstr(y, x, 3).decode('utf-8')
    curses.noecho()
    return value or default_value


def clamp(value: Any, min_value: Any, max_value: Any):
    """
    Clamp a value between a minimum and a maximum
    """
    return max(min(value, max_value), min_value)

def on_parameter_change(param_name, channel, control_number, value):
    print(f"Parameter {param_name} (Channel: {channel}, Control Number: {control_number}) changed to {value}")

def main(stdscr):
    """
    Main event loop for the Curses application. Draws the screen, update information.
    The mechanism will also be in charge of auto-saving application state every now
    and then.
    """
    global banks, current_bank
    application_loop: int = 0

    # Load banks from file
    current_bank = "dadou"
    banks = load_banks(bank_location=BANKS_FILE_PATH)

    # Set up the screen
    curses.curs_set(2)
    stdscr.nodelay(0)
    stdscr.timeout(-1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE)

    # Initialize the cursor position
    cursor_y, cursor_x = 0, 0

    while True:
        stdscr.clear()

        # Show current bank
        stdscr.attron(curses.color_pair(1))
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(0, 0, f"BANK: {current_bank}")
        stdscr.attroff(curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        # Draw the 8x8 grid
        params = banks[current_bank]["params"]
        param_values = banks[current_bank]["values"]

        for y in range(8):
            for x in range(8):
                index = y * 8 + x
                param = params[index]
                stdscr.addstr(y + 1, x * 4, param)

        # Draw the cursor
        cursor_index = cursor_y * 8 + cursor_x
        cursor_param = params[cursor_index]
        cursor_value = f"{param_values[cursor_param]: >3}"
        stdscr.addstr(cursor_y + 1, cursor_x * 4, cursor_value, curses.A_REVERSE)

        # Show channel and control number at the bottom
        cursor_channel = banks[current_bank]["channels"][cursor_param]
        cursor_control_number = banks[current_bank]["control_numbers"][cursor_param]
        stdscr.addstr(10, 0, f"Channel: {cursor_channel} Control Number: {cursor_control_number}")

        # Capture user input
        key = stdscr.getch()

        # Update cursor position based on arrow keys
        if key == curses.KEY_UP and cursor_y > 0:
            cursor_y -= 1
        elif key == curses.KEY_DOWN and cursor_y < 7:
            cursor_y += 1
        elif key == curses.KEY_LEFT and cursor_x > 0:
            cursor_x -= 1
        elif key == curses.KEY_RIGHT and cursor_x < 7:
            cursor_x += 1
        elif key == ord('v'):  # Change value
            curses.curs_set(0)
            stdscr.nodelay(0)
            new_value = get_param_value(stdscr, cursor_y + 1, cursor_x * 4, param_values[cursor_param])[:3]
            new_value = clamp(int(new_value), 0, 127)
            param_values[cursor_param] = new_value
            on_parameter_change(cursor_param, cursor_channel, cursor_control_number, new_value)
            stdscr.nodelay(1)
            curses.curs_set(2)
        elif key == ord('r'):  # Rename parameter
            curses.curs_set(0)
            stdscr.nodelay(0)
            new_name = get_param_value(stdscr, cursor_y + 1, cursor_x * 4, cursor_param)[:3].upper()
            if len(new_name) == 3 and new_name.isalpha():
                old_index = params.index(cursor_param)
                params[old_index] = new_name
                param_values[new_name] = param_values.pop(cursor_param)
                banks[current_bank]["channels"][new_name] = banks[current_bank]["channels"].pop(cursor_param)
                banks[current_bank]["control_numbers"][new_name] = banks[current_bank]["control_numbers"].pop(cursor_param)
                cursor_param = new_name
            stdscr.nodelay(1)
            curses.curs_set(2)
        elif key == ord('n'):  # Enter control number
            curses.curs_set(0)
            stdscr.nodelay(0)
            new_control_number = get_param_value(stdscr, 10, 16, str(cursor_control_number))
            new_control_number = clamp(int(new_control_number), 0, 127)
            banks[current_bank]["control_numbers"][cursor_param] = new_control_number
            stdscr.nodelay(1)
            curses.curs_set(2)
        elif key == ord('c'):  # Enter channel
            curses.curs_set(0)
            stdscr.nodelay(0)
            new_channel = get_param_value(stdscr, 10, 9, str(cursor_channel))
            new_channel = clamp(int(new_channel), 0, 15)
            banks[current_bank]["channels"][cursor_param] = new_channel
            stdscr.nodelay(1)
            curses.curs_set(2)
        elif key == ord('q'):  # Quit
            stdscr.addstr("\nDo you want to quit? (y/n): ")
            if stdscr.getch() == ord('y'):
                exit()
         elif key == ord('b'):  # Switch bank
            # Get the new bank name from the user
            curses.curs_set(0)
            stdscr.nodelay(0)
            stdscr.addstr(0, 5, " " * 10)
            new_bank_name = get_param_value(stdscr, 0, 6, "").upper()

            if new_bank_name.isalpha():
                if new_bank_name not in banks:
                    # Initialize a new bank if it doesn't exist
                    banks[new_bank_name] = {
                        "params": [f"P{index:02}" for index in range(64)],
                        "values": {param: 0 for param in [f"P{index:02}" for index in range(64)]},
                        "channels": {param: 0 for param in [f"P{index:02}" for index in range(64)]},
                        "control_numbers": {param: 0 for param in [f"P{index:02}" for index in range(64)]}
                    }
                current_bank = new_bank_name

            stdscr.nodelay(1)
            curses.curs_set(2)

        # Save every few cycles around
        if application_loop % 5 == 0:
            save_banks(BANKS_FILE_PATH)

        # Refresh and increment the rate
        stdscr.refresh()
        application_loop += 1

if __name__ == "__main__":
    curses.wrapper(main)

