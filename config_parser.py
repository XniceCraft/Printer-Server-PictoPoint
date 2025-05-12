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
    cors_domain: List[str]

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
        assert "cors_domain" in json_obj and isinstance(
            json_obj["cors_domain"], list
        ), "Missing or invalid 'cors_domain'"
        assert all(
            isinstance(domain, str) for domain in json_obj["cors_domain"]
        ), "'cors_domain' must be a list of strings"

        return cls(
            printer_name=json_obj["printer_name"],
            host=json_obj["host"],
            port=json_obj["port"],
            cors_domain=json_obj["cors_domain"],
        )
