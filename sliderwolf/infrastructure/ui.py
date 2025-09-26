import contextlib
import curses
from typing import Any

from ..domain.interfaces import Renderer
from ..domain.models import Bank


class CursesRenderer(Renderer):
    def __init__(self) -> None:
        self._stdscr: Any = None
        self._screen_width = 0
        self._screen_height = 0

    def initialize(self) -> None:
        if self._stdscr:
            return

        self._stdscr = curses.initscr()
        curses.curs_set(2)
        self._stdscr.timeout(100)  # 100ms timeout for periodic updates
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        curses.noecho()
        curses.cbreak()
        self._stdscr.keypad(True)

        self._screen_height, self._screen_width = self._stdscr.getmaxyx()

    def cleanup(self) -> None:
        if self._stdscr:
            curses.nocbreak()
            self._stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            self._stdscr = None

    def _update_screen_dimensions(self) -> None:
        """Update screen dimensions - call this before each render"""
        if self._stdscr:
            self._screen_height, self._screen_width = self._stdscr.getmaxyx()

    def _get_centered_position(self) -> tuple[int, int]:
        """Calculate centered position for the main interface"""
        self._update_screen_dimensions()

        # Interface dimensions: 8x8 grid with 4 chars per cell = 32 width
        # Height needs space for grid (8) + bank name (1) + parameter info (1) + midi port (1) + margin = ~12
        interface_width = 32
        interface_height = 12

        start_y = max((self._screen_height - interface_height) // 2, 1)
        start_x = max((self._screen_width - interface_width) // 2, 1)

        return start_y, start_x

    def render_grid(
        self,
        bank: Bank,
        cursor_x: int,
        cursor_y: int,
        show_all_values: bool = False,
        show_cursor_value: bool = False,
    ) -> None:
        if not self._stdscr:
            return

        self._stdscr.erase()
        self._stdscr.border(0)

        start_y, start_x = self._get_centered_position()

        # Draw grid
        for y in range(8):
            for x in range(8):
                index = y * 8 + x
                if index < len(bank.parameters):
                    param = bank.parameters[index]

                    # Determine what to display: name or value
                    is_cursor_position = y == cursor_y and x == cursor_x

                    if show_all_values:
                        # Show all values when key is pressed
                        display_text = f"{param.value:3d}"
                    elif is_cursor_position and show_cursor_value:
                        # Show value on cursor position during flip cycle
                        display_text = f"{param.value:3d}"
                    else:
                        # Show names by default (including cursor when not flipped)
                        display_text = f"{param.name:3s}"

                    try:
                        if is_cursor_position:
                            self._stdscr.addstr(
                                start_y + y,
                                start_x + x * 4,
                                display_text,
                                curses.A_REVERSE,
                            )
                        else:
                            self._stdscr.addstr(
                                start_y + y, start_x + x * 4, display_text
                            )
                    except curses.error:
                        # Ignore if we can't draw (terminal too small or encoding issues)
                        pass

        # Show parameter info for cursor position
        cursor_index = cursor_y * 8 + cursor_x
        if cursor_index < len(bank.parameters):
            param = bank.parameters[cursor_index]
            info_text = (
                f"Channel: {param.channel.value} Control Number: {param.control_number}"
            )
            with contextlib.suppress(curses.error):
                self._stdscr.addstr(start_y + 9, start_x, info_text)

        self._stdscr.refresh()

    def render_status(self, bank_name: str, midi_port: str) -> None:
        if not self._stdscr:
            return

        start_y, start_x = self._get_centered_position()

        # Bank name
        try:
            self._stdscr.attron(curses.color_pair(1))
            self._stdscr.attron(curses.A_BOLD)
            self._stdscr.addstr(
                start_y - 1, start_x, f"BANK: {bank_name}", curses.A_STANDOUT
            )
            self._stdscr.attroff(curses.A_BOLD)
            self._stdscr.attroff(curses.color_pair(1))
        except curses.error:
            pass

        # MIDI port
        with contextlib.suppress(curses.error):
            self._stdscr.addstr(start_y + 10, start_x, f"MIDI Port: {midi_port}")

        self._stdscr.refresh()

    def render_help(self, show_help: bool) -> None:
        if not self._stdscr or not show_help:
            return

        self._update_screen_dimensions()  # Ensure we have current dimensions

        help_lines = [
            "Keys: ↑↓←→:Navigate  v:Value  +/-:Inc/Dec  r:Rename  c:Channel  n:Control#",
            "      b:Bank  x:Reset  m:MIDI Port  SPACE:Show Values  h:Help  q:Quit",
        ]

        # Position help at bottom of screen
        help_y = self._screen_height - len(help_lines) - 1

        for i, line in enumerate(help_lines):
            # Center the help text
            help_x = max(0, (self._screen_width - len(line)) // 2)
            with contextlib.suppress(curses.error):
                self._stdscr.addstr(help_y + i, help_x, line, curses.A_DIM)

        self._stdscr.refresh()

    def get_input(self) -> int:
        if not self._stdscr:
            return -1
        result = self._stdscr.getch()
        return int(result) if result is not None else -1

    def prompt_input(self, prompt: str, max_length: int) -> str:
        if not self._stdscr:
            return ""

        start_y, start_x = self._get_centered_position()

        # Save current state and set to blocking mode for prompt
        self._stdscr.timeout(-1)  # Set to blocking (no timeout)
        curses.echo()
        curses.curs_set(1)

        try:
            self._stdscr.addstr(start_y + 11, start_x, prompt)
            self._stdscr.refresh()
            raw_input = self._stdscr.getstr(
                start_y + 11, start_x + len(prompt), max_length
            )
            input_str = raw_input.decode("utf-8") if raw_input else ""
        except curses.error:
            input_str = ""
        finally:
            # Restore original state
            curses.noecho()
            curses.curs_set(2)
            self._stdscr.timeout(100)  # Restore 100ms timeout for main loop

        return input_str
