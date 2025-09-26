import json
import os
from typing import Dict, Optional
from ..domain.interfaces import BankRepository
from ..domain.models import Bank, Parameter, MIDIChannel


class FileBankRepository(BankRepository):
    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            self._file_path = os.path.join(
                os.path.expanduser("~"), ".local", "share", "sliderwolf", "banks.json"
            )
        else:
            self._file_path = file_path

    def load_banks(self) -> Dict[str, Bank]:
        data = self._load_data()
        banks = {}

        for bank_name, bank_data in data["banks"].items():
            parameters = []
            for i in range(64):
                param_name = bank_data["params"][i] if i < len(bank_data["params"]) else f"P{i:02}"
                value = bank_data["values"].get(param_name, 0)
                channel = MIDIChannel.from_int(bank_data["channels"].get(param_name, 0))
                control_number = bank_data["control_numbers"].get(param_name, 0)

                parameters.append(Parameter(
                    name=param_name,
                    value=value,
                    channel=channel,
                    control_number=control_number
                ))

            banks[bank_name] = Bank(name=bank_name, parameters=parameters)

        return banks

    def save_banks(self, banks: Dict[str, Bank]) -> None:
        data = self._load_data()

        # Convert banks to old format for compatibility
        data["banks"] = {}
        for bank_name, bank in banks.items():
            data["banks"][bank_name] = {
                "params": [param.name for param in bank.parameters],
                "values": {param.name: param.value for param in bank.parameters},
                "channels": {param.name: param.channel.value for param in bank.parameters},
                "control_numbers": {param.name: param.control_number for param in bank.parameters}
            }

        self._save_data(data)

    def get_preferred_midi_port(self) -> Optional[str]:
        data = self._load_data()
        return data.get("preferred_midi_port")

    def set_preferred_midi_port(self, port: str) -> None:
        data = self._load_data()
        data["preferred_midi_port"] = port
        self._save_data(data)

    def _load_data(self) -> dict:
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading banks from {self._file_path}: {e}")

        return self._get_default_data()

    def _save_data(self, data: dict) -> None:
        try:
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(self._file_path, "w") as f:
                json.dump(data, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Warning: Failed to save banks to {self._file_path}: {str(e)}")

    def _get_default_data(self) -> dict:
        return {
            "preferred_midi_port": None,
            "banks": {
                "XXX": {
                    "params": [f"P{index:02}" for index in range(64)],
                    "values": {f"P{index:02}": 0 for index in range(64)},
                    "channels": {f"P{index:02}": 0 for index in range(64)},
                    "control_numbers": {f"P{index:02}": 0 for index in range(64)}
                }
            }
        }
