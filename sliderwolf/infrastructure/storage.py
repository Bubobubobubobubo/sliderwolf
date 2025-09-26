import contextlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ..domain.interfaces import BankRepository
from ..domain.models import Bank, MIDIChannel, Parameter


class FileBankRepository(BankRepository):
    def __init__(self, file_path: str | None = None):
        if file_path is None:
            self._file_path = (
                Path.home() / ".local" / "share" / "sliderwolf" / "banks.json"
            )
        else:
            self._file_path = Path(file_path)
        self._last_saved_data: dict[str, Any] | None = None

    def load_banks(self) -> dict[str, Bank]:
        data = self._load_data()
        banks = {}

        for bank_name, bank_data in data["banks"].items():
            parameters = []
            for i in range(64):
                param_name = (
                    bank_data["params"][i]
                    if i < len(bank_data["params"])
                    else f"P{i:02}"
                )
                value = bank_data["values"].get(param_name, 0)
                channel = MIDIChannel.from_int(bank_data["channels"].get(param_name, 0))
                control_number = bank_data["control_numbers"].get(param_name, 0)

                parameters.append(
                    Parameter(
                        name=param_name,
                        value=value,
                        channel=channel,
                        control_number=control_number,
                    )
                )

            banks[bank_name] = Bank(name=bank_name, parameters=parameters)

        return banks

    def save_banks(self, banks: dict[str, Bank]) -> None:
        data = self._load_data()

        # Convert banks to old format for compatibility
        data["banks"] = {}
        for bank_name, bank in banks.items():
            data["banks"][bank_name] = {
                "params": [param.name for param in bank.parameters],
                "values": {param.name: param.value for param in bank.parameters},
                "channels": {
                    param.name: param.channel.value for param in bank.parameters
                },
                "control_numbers": {
                    param.name: param.control_number for param in bank.parameters
                },
            }

        # Only save if data actually changed
        if data != self._last_saved_data:
            self._save_data(data)
            self._last_saved_data = data

    def get_preferred_midi_port(self) -> str | None:
        data = self._load_data()
        return data.get("preferred_midi_port")

    def set_preferred_midi_port(self, port: str) -> None:
        data = self._load_data()
        data["preferred_midi_port"] = port
        self._save_data(data)

    def _load_data(self) -> dict[str, Any]:
        if self._file_path.exists():
            try:
                with self._file_path.open() as f:
                    data: dict[str, Any] = json.load(f)
                    self._last_saved_data = data
                    return data
            except (OSError, json.JSONDecodeError) as e:
                print(f"Error loading banks from {self._file_path}: {e}")

        data = self._get_default_data()
        self._last_saved_data = data
        return data

    def _save_data(self, data: dict[str, Any]) -> None:
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write using temporary file
            temp_fd, temp_path = tempfile.mkstemp(
                suffix=".tmp", dir=self._file_path.parent, prefix="banks_"
            )

            try:
                with os.fdopen(temp_fd, "w") as f:
                    json.dump(data, f, indent=2)

                # Atomic move
                shutil.move(temp_path, self._file_path)

            except Exception:
                # Clean up temp file on failure
                with contextlib.suppress(OSError):
                    Path(temp_path).unlink()
                raise

        except OSError as e:
            print(f"Warning: Failed to save banks to {self._file_path}: {str(e)}")

    def _get_default_data(self) -> dict[str, Any]:
        return {
            "preferred_midi_port": None,
            "banks": {
                "XXX": {
                    "params": [f"P{index:02}" for index in range(64)],
                    "values": {f"P{index:02}": 0 for index in range(64)},
                    "channels": {f"P{index:02}": 0 for index in range(64)},
                    "control_numbers": {f"P{index:02}": 0 for index in range(64)},
                }
            },
        }
