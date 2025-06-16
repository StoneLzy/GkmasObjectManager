"""
adv/adventure.py
Adventure (story script) plugin for GkmasResource.
"""

import json
import re

from ..media import GkmasDummyMedia
from ..utils import make_caption_map
from .parser import GkadvCommandParser

parser = GkadvCommandParser()


class GkmasAdventure(GkmasDummyMedia):
    """Handler for adventure story scripts."""

    commands: list[dict]

    def _init_mimetype(self):
        self.mimetype = "text"
        self.default_converted_format = "json"

    def _get_commands(self) -> list[dict]:
        if not hasattr(self, "commands"):
            self.commands = [
                parser.process(line)
                for line in self._get_raw().decode("utf-8").splitlines()
            ]
        return self.commands

    def get_caption_map(self) -> dict[str, str]:
        """For voice archive captioning in frontend only."""
        return make_caption_map(self._get_commands())

    def _convert(self, raw: bytes) -> bytes:
        # only for compatibility with GkmasResource
        return bytes(
            json.dumps(
                self._get_commands(),
                indent=4,
                ensure_ascii=False,
            ),
            "utf-8",
        )
