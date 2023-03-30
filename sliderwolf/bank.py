import json
import os

class Bank():
    """Mechanism to load and retrieve parameter banks"""

    # Constants 
    BANKS_FILE_PATH = os.path.join(
            os.path.expanduser("~"),
            ".local", "share", "FD5",
            "banks.json")

    def __init__(self):
        self.bank = self.load_banks()

    def save_banks(self):
        """
        Save the current bank as JSON in the BANKS_FILE_PATH
        folder. 
        """
        with open(self.BANKS_FILE_PATH, "w") as f:
            json.dump(self.bank, f)

    def load_banks(self):
        """
        Load the bank from the BANKS_FILE_PATH file, typically
        found in (./local/share/DE5). If no file is found, it
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
            "default": {
                "params": [f"P{index:02}" for index in range(64)],
                "values": {param: 0 for param in [f"P{index:02}" for index in range(64)]},
                "channels": {param: 0 for param in [f"P{index:02}" for index in range(64)]},
                "control_numbers": {param: 0 for param in [f"P{index:02}" for index in range(64)]}
            }
        }
