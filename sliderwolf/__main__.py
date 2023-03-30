from .bank import Bank
from .utils import clamp
from .application import Application
import curses

if __name__ == "__main__":
    app = Application()
    curses.wrapper(app.application_loop)
