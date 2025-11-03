"""

Much simpler now.

"""

import re
import logging
import json
from enum import StrEnum
from typing import Any, Union, TypeAlias
from dataclasses import dataclass

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

re_choice = re.compile(r"^>\[!question\] (.+)$")
re_choice_option = re.compile(r"^>- \[\[#(.+)\]\]$")
re_speaker = re.compile(r"^>\[!quote\] (.+)$")
re_follow_last = re.compile(r"^>(.*)$")
re_media = re.compile(r"^\!\[\[(.+)\]\]$")
re_code = re.compile("^```$")
re_no_fmt = re.compile(r"^(.+)$") # Either narration or code

def tokenize(lines: list[str]) -> list[dict]:
    tokens = []
    rgxs = [re_choice, re_choice_option, re_speaker, re_follow_last, re_media, re_code, re_no_fmt]

    for line in lines:
        line = line.strip()
        if not line:
            logger.debug("Skipping empty line.")
            continue

        for rgx in rgxs:
            if rgx_match := rgx.match(line):
                logger.debug(f"Hit: {rgx} for line: {line}")
                if rgx == re_choice:             
                    tokens.append({"type": "choice", "text": rgx_match.group(1)})
                elif rgx == re_choice_option:
                    tokens.append({"type": "choice_option", "target": rgx_match.group(1)})
                elif rgx == re_speaker:
                    tokens.append({"type": "speaker", "text": rgx_match.group(1)})
                elif rgx == re_follow_last:
                    tokens.append({"type": "follow_last", "text": rgx_match.group(1)})
                elif rgx == re_media:
                    tokens.append({"type": "media", "name": rgx_match.group(1)})
                elif rgx == re_code:
                    tokens.append({"type": "code"})
                elif rgx == re_no_fmt:
                    tokens.append({"type": "no_fmt", "text": rgx_match.group(1)})
                logger.debug(f"Hit: {tokens[-1]['type']} for line: {line}")
                break
    return tokens

class EventType(StrEnum):
    CHOICE = "choice"
    SPEAKER = "speaker"
    MEDIA = "media"
    CODE = "code"
    NARRATION = "narration"

@dataclass
class ChoiceEvent:
    quesiton: str
    options: list[str]

@dataclass
class DialogueEvent:
    speaker: str
    text: list[str]

@dataclass
class MediaEvent:
    name: str

@dataclass
class CodeEvent:
    code: list[str]

@dataclass
class NarrationEvent:
    text: str

Event: TypeAlias = Union[ChoiceEvent, DialogueEvent, MediaEvent, CodeEvent, NarrationEvent]

def parse(tokens: list[dict]) -> dict:

    events: list[dict[str, Any]] = []
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        i += 1

        if token["type"] == "code":
            active = CodeEvent(code=[])
            while i < len(tokens) and tokens[i]["type"] != "code":
                active.code.append(tokens[i]["text"])
                i += 1
            if i < len(tokens):
                i += 1
            events.append(active)
            continue

        if token["type"] == "choice":
            active = ChoiceEvent(quesiton=token["text"], options=[])
            while i < len(tokens) and tokens[i]["type"] == "choice_option":
                active.options.append(tokens[i]["target"])
                i += 1
            events.append(active)
            continue
            
        if token["type"] == "speaker":
            active = DialogueEvent(speaker=token["text"], text=[])
            while i < len(tokens) and tokens[i]["type"] == "follow_last":
                active.text.append(tokens[i]["text"])
                i += 1
            events.append(active)
            continue

        if token["type"] == "media":
            events.append(MediaEvent(name=token["name"]))
        elif token["type"] == "no_fmt":
            events.append(NarrationEvent(text=token["text"]))
    
    return events

if __name__ == "__main__":
    with open("script.md", "r") as f:
        script = f.read()

    tokens = tokenize(script.splitlines())
    print(tokens)
    graph = parse(tokens)
    print(
        json.dumps(
            graph
        , indent=4,default=str
        )
    )