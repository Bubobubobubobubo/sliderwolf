# SliderWolf

![sliderwolf](sliderwolf_picture.png)

SliderWolf is a TUI application that allows users to control MIDI parameter  banks using a simple grid like interface. It is a keyboard-centric application meant to be used along with other music creation tools. It is heavily inspired by a very popular hardware MIDI controller device that I cannot afford. It supports creating and switching between multiple banks, renaming parameters, and changing parameter values, MIDI channels, and control numbers. Banks are persistent, and their state is saved across sessions.

## Features
- TUI interface for quick and efficient editing of MIDI parameter banks
- Grid layout for parameter visualization and navigation (looks fancy)
- Edit parameter values, MIDI channels, and control numbers
- Auto-save application state and persistent storage between sessions

## Installation

SliderWolf requires Python 3.12 or newer. Choose one of the installation methods below:

### Method 1: Install from Source (Recommended)

```shell
git clone https://github.com/Bubobubobubobubo/sliderwolf
cd sliderwolf
uv sync
uv pip install -e .
```

After installation, you can run SliderWolf from anywhere:

```shell
sliderwolf  # or use the short alias: swolf
```

Alternatively, you can run the `uv` command:

```shell
uv run python -m sliderwolf
```

### Method 2: Development Setup

For development or if you prefer running directly:

```shell
git clone https://github.com/Bubobubobubobubo/sliderwolf
cd sliderwolf
uv sync
uv run python -m sliderwolf
```

### Method 3: Direct Installation with pip

If you don't have `uv` installed:

```shell
git clone https://github.com/Bubobubobubobubo/sliderwolf
cd sliderwolf
pip install -e .
sliderwolf
```

## Usage

Once installed, simply run:

```shell
sliderwolf  # Full command
# or
swolf       # Short alias
```

Use the arrow keys to navigate the grid, and the following keys to perform actions:

- `v`: Change the value of the currently selected parameter
- `+`: Increment the value of the currently selected parameter
- `-`: Decrement the value of the currently selected parameter
- `r`: Rename the currently selected parameter
- `n`: Edit the control number of the currently selected parameter
- `c`: Edit the channel of the currently selected parameter
- `b`: Switch to another bank or create a new one
- `x`: Reset the current parameter bank
- `q`: Quit the application

When prompted to input values, type the desired value and press Enter. If you don't want to make changes, just press Enter without typing anything.

## Architecture

SliderWolf follows a clean architecture pattern with clear separation of concerns:

```
sliderwolf/
├── app.py                   # Main entry point
├── domain/                  # Core logic
│   ├── models.py            # Parameter, Bank, MIDIMessage, AppState
│   └── interfaces.py        # Abstract interfaces for ports
├── application/             # Use cases and operations
│   └── services.py          # BankService, MIDIService, ParameterService
├── infrastructure/          # External concerns (I/O, persistence)
│   ├── storage.py           # File-based bank repository
│   ├── midi.py              # MIDI port implementation
│   └── ui.py                # Terminal UI renderer
└── presentation/            # User interface and input handling
    └── controllers.py       # Main UI controller and input handler
```

The architecture ensures:
- **Domain layer** contains pure logic with no external dependencies
- **Application layer** orchestrates use cases and coordinates between layers
- **Infrastructure layer** handles external systems (files, MIDI, terminal)
- **Presentation layer** manages user interaction and display logic

## Contributing

If you would like to contribute to SliderWolf, feel free to fork the repository and submit a pull request with your changes. We're always open to improvements and new ideas.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
