"""
Parse the config
"""

# pylint: disable=line-too-long
import json
from typing import List
from dataclasses import dataclass


@dataclass
class Config:
    """
    An object representation for the config
    """

    printer_name: str
    host: str
    port: int
    cors_origin: List[str]

    @classmethod
    def load(cls) -> "Config":
        """
        Load the config
        """
        with open("./config.json", encoding="utf-8") as file:
            json_obj = json.load(file)

        assert "printer_name" in json_obj and isinstance(
            json_obj["printer_name"], str
        ), "Missing or invalid 'printer_name'"
        assert "host" in json_obj and isinstance(
            json_obj["host"], str
        ), "Missing or invalid 'host'"
        assert "port" in json_obj and isinstance(
            json_obj["port"], int
        ), "Missing or invalid 'port'"
        assert "cors_origin" in json_obj and isinstance(
            json_obj["cors_origin"], list
        ), "Missing or invalid 'cors_origin'"
        assert all(
            isinstance(domain, str) for domain in json_obj["cors_origin"]
        ), "'cors_origin' must be a list of strings"

        return cls(
            printer_name=json_obj["printer_name"],
            host=json_obj["host"],
            port=json_obj["port"],
            cors_origin=json_obj["cors_origin"],
        )
