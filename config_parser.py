"""
Parse the config
"""

# pylint: disable=line-too-long
import json
import os.path
from typing import Any, List, Dict
from dataclasses import dataclass, field

printer_data: Dict[str, Dict[str, Any]] = {
    "POS-58": {
        "max_char_row": 32,
        "image_width": 384
    },
    "POS-80": {
        "max_char_row": 48,
        "image_width": 512
    },
    "EPSON TM-T82": {
        "max_char_row": 48,
        "image_width": 512
    }
}

@dataclass
class Printer:
    """
    Interface for the printer
    """
    printer_name: str
    printer_type: str
    profile: Dict[str, Any] = field(init=False)

    def __post_init__(self):
        if self.printer_type not in printer_data:
            raise ValueError(f"Undefined printer type: {self.printer_type}")

        self.profile = printer_data[self.printer_type]

@dataclass
class Config:
    """
    An object representation for the config
    """

    host: str
    port: int
    cors_origin: List[str]
    printers: List[Printer]

    @classmethod
    def write_default(cls) -> None:
        """
        Write default config if config parsing failed

        Returns
        -------
        None
        """
        with open("./config.json", "w", encoding="utf-8") as file:
            data = {
                "host": "0.0.0.0",
                "port": 9000,
                "cors_origin": ["*"],
                "printers": [{"printer_name": "POS-58", "printer_type": "POS-58"}],
            }
            json.dump(data, file)

    @classmethod
    def load(cls) -> "Config":
        """
        Load the config
        """
        if os.path.isfile('config.json'):
            cls.write_default()

        with open("./config.json", encoding="utf-8") as file:
            json_obj = json.load(file)

        assert "host" in json_obj and isinstance(
            json_obj["host"], str
        ), "Missing or invalid 'host'"
        assert "port" in json_obj and isinstance(
            json_obj["port"], int
        ), "Missing or invalid 'port'"
        assert "cors_origin" in json_obj and isinstance(
            json_obj["cors_origin"], list
        ), "Missing or invalid 'cors_origin'"
        assert "printers" in json_obj and isinstance(
            json_obj["printers"], list
        ), "Missing or invalid 'printers'"

        printers = [Printer(**printer) for printer in json_obj["printers"]]

        return cls(
            host=json_obj["host"],
            port=json_obj["port"],
            cors_origin=json_obj["cors_origin"],
            printers=printers,
        )
