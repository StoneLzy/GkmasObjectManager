"""
adv/adventure.py
Adventure (story script) plugin for GkmasResource.
"""

import json

from ..media import GkmasDummyMedia
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
        """
        Returns a mapping of voicelines' *in-archive aliases* to their captions.
        For voice archive captioning in frontend only.
        """

        # Filtering and parsing logic copied from sovits_dataset.py;
        # not reused to avoid messing up with reading local cache.
        caption_map = {}

        commands = self._get_commands()
        commands = sorted(
            filter(lambda cmd: cmd["cmd"] in ["message", "voice"], commands),
            key=lambda cmd: cmd["clip"]["_startTime"],
        )

        for cmd1, cmd2 in zip(commands, commands[1:]):
            if cmd1["cmd"] == "message" and cmd2["cmd"] == "voice":
                alias = cmd2["voice"].split("_")[-1]
                caption = cmd1.get("text", "").strip().replace(r"\n", "")
                caption_map[alias] = caption

        return caption_map

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
