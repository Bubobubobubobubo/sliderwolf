import json
import os
from typing import Dict, Any, Optional

# Constants
MAX_PARAMS = 64


class Bank:
    """Mechanism to load and retrieve parameter banks"""

    # Constants
    BANKS_FILE_PATH = os.path.join(
        os.path.expanduser("~"), ".local", "share", "sliderwolf", "banks.json"
    )

    def __init__(self) -> None:
        self.bank_data: Dict[str, Any] = self.load_banks()
        self.bank: Dict[str, Any] = self.bank_data["banks"]
        self.preferred_midi_port: Optional[str] = self.bank_data.get("preferred_midi_port", None)

    def save_banks(self) -> None:
        """
        Save the current bank as JSON in the BANKS_FILE_PATH
        folder.
        """
        try:
            os.makedirs(os.path.dirname(self.BANKS_FILE_PATH), exist_ok=True)
            with open(self.BANKS_FILE_PATH, "w") as f:
                json.dump(self.bank_data, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Warning: Failed to save banks to {self.BANKS_FILE_PATH}: {str(e)}")

    def load_banks(self) -> Dict[str, Any]:
        """
        Load the bank from the BANKS_FILE_PATH file, typically
        found in (./local/share/sliderwolf). If no file is found, it
        will return a default bank.
        """
        if os.path.exists(self.BANKS_FILE_PATH):
            with open(self.BANKS_FILE_PATH, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error loading banks from {self.BANKS_FILE_PATH}: {e}")
        else:
            os.makedirs(os.path.dirname(self.BANKS_FILE_PATH), exist_ok=True)
            return {
                "preferred_midi_port": None,
                "banks": {
                    "XXX": {
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
                },
            }
