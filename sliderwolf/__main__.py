from .bank import Bank
from .utils import clamp
from .application import Application
import curses
import sys

if __name__ == "__main__":
    try:
        app = Application()
        curses.wrapper(app.application_loop)
    except KeyboardInterrupt:
        if 'app' in locals():
            app._cleanup()
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        if 'app' in locals():
            app._cleanup()
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
