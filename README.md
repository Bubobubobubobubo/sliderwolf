# SliderWolf

![sliderwolf](sliderwolf_picture.png)

SliderWolf is a terminal-based application that allows users to edit MIDI parameters in a simple grid-like interface. It supports creating and switching between multiple banks, renaming parameters, and changing parameter values, MIDI channels, and control numbers.

## Features
- Terminal-based interface for quick and efficient editing
- 8x8 grid layout for easy parameter visualization and navigation
- Support for multiple banks with custom parameter names
- Edit parameter values, MIDI channels, and control numbers
- Auto-saving of application state

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

## Contributing

If you would like to contribute to SliderWolf, feel free to fork the repository and submit a pull request with your changes. We're always open to improvements and new ideas.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
