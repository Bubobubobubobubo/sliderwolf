import json
import os


class Bank:
    """Mechanism to load and retrieve parameter banks"""

    # Constants
    BANKS_FILE_PATH = os.path.join(
        os.path.expanduser("~"), ".local", "share", "sliderwolf", "banks.json"
    )

    def __init__(self):
        self.bank_data = self.load_banks()
        self.bank = self.bank_data["banks"]
        self.preferred_midi_port = self.bank_data.get("preferred_midi_port", None)

    def save_banks(self):
        """
        Save the current bank as JSON in the BANKS_FILE_PATH
        folder.
        """
        with open(self.BANKS_FILE_PATH, "w") as f:
            json.dump(self.bank_data, f)

    def load_banks(self):
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
                },
            }
