import re
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

# --- Tokenizer's regexes ---
# Codeblock start: ```name
codeblock_re = re.compile(r"^```(\w+)\s*$")
# Codeblock end: ```
endblock_re = re.compile(r"^```$")
# Scene header
header_re = re.compile(r"##\s(.+)")
# Choice line: - [Text](target) [optional: set var=value]
choice_re = re.compile(r"- \[(.+?)\]\((.+?)\)(?:\s+set\s+(\w+)\s*=\s*(.+))?")
# Dialogue line: **Name**: text
dialogue_re = re.compile(r"\*\*(.+?)\*\*: (.+)")
# Jump: > target ? condition
jump_re = re.compile(r">\s*(\w+)(?:\s*\?\s*(.+))?")
# Assignment: @ var = value
set_re = re.compile(r"@\s*(\w+)\s*=\s*(.+)")
# Macro: ![[name]]
macro_re = re.compile(r"!\[\[(.+)\]\]")

# --- Parser's regexes ---
# Character
char_show_re = re.compile(
    r"show\s+(\w+)\s+(\S+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)(?:\s+(\d+\.?\d*))?"
)
char_hide_re = re.compile(r"hide\s+(\w+)")
char_move_re = re.compile(
    r"move\s+(\w+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)(?:\s+(\d+\.?\d*))?"
)
char_expr_re = re.compile(r"expr\s+(\w+)\s+(\S+)")
# Transition
fade_out_re = re.compile(
    r"fade_out(?:\s+(\d+\.?\d*))?(?:\s+\((\d+),(\d+),(\d+)(?:,(\d+))?\))?"
)
fade_in_re = re.compile(
    r"fade_in(?:\s+(\d+\.?\d*))?(?:\s+\((\d+),(\d+),(\d+)(?:,(\d+))?\))?"
)


# --- Tokenizer ---
def tokenize(lines):
    tokens = []
    in_block = None
    block_content = []
    rgxs = [header_re, choice_re, dialogue_re, jump_re, set_re, macro_re]

    for line in lines:
        line = line.strip()
        if not line:
            logger.debug("Skipping empty line.")
            continue

        if not in_block:
            m = codeblock_re.match(line)
            if m:
                in_block = m.group(1)  # language tag (e.g. "char", "transition")
                logger.info(f"Starting codeblock: {in_block}")
                block_content = []
                continue
        else:
            # End of block
            if endblock_re.match(line):
                tokens.append(
                    {"type": "codeblock", "lang": in_block, "content": block_content}
                )
                logger.info(
                    f"Ending codeblock: {in_block}. Content lines: {len(block_content)}"
                )
                in_block = None
                continue
            block_content.append(line)
            logger.debug(f"Adding line to codeblock '{in_block}': {line}")
            continue

        for rgx in rgxs:
            if rgx_match := rgx.match(line):
                if rgx == header_re:
                    tokens.append({"type": "scene", "name": rgx_match.group(1)})
                elif rgx == choice_re:
                    tokens.append(
                        {
                            "type": "choice",
                            "text": rgx_match.group(1),
                            "target": rgx_match.group(2),
                            "set": (
                                (rgx_match.group(3), rgx_match.group(4))
                                if rgx_match.group(3)
                                else None
                            ),
                        }
                    )
                elif rgx == dialogue_re:
                    tokens.append(
                        {
                            "type": "dialogue",
                            "speaker": rgx_match.group(1),
                            "text": rgx_match.group(2),
                        }
                    )
                elif rgx == jump_re:
                    tokens.append(
                        {
                            "type": "jump",
                            "target": rgx_match.group(1),
                            "condition": rgx_match.group(2),
                        }
                    )
                elif rgx == set_re:
                    tokens.append(
                        {
                            "type": "set",
                            "var": rgx_match.group(1),
                            "value": rgx_match.group(2).strip(),
                        }
                    )
                elif rgx == macro_re:
                    tokens.append({"type": "macro", "name": rgx_match.group(1)})
                logger.debug(f"Hit: {tokens[-1]['type']} for line: {line}")
                break
        else:  # No regex matched for the line, treat as narration
            tokens.append({"type": "narration", "text": line})
            logger.debug(f"Hit: narration for line: {line}")

    logger.info(f"Tokenization complete. {len(tokens)} tokens generated.")
    return tokens


# --- Parser ---
def parse(tokens):
    scenes = {}
    current_scene = None
    for token in tokens:
        if token["type"] == "scene":
            current_scene = {"name": token["name"], "events": []}
            scenes[token["name"]] = current_scene
            logger.info(f"Creating new scene: {token['name']}")
        else:
            if not current_scene:
                logger.error("Event found outside of a scene. Raising ValueError.")
                raise ValueError("Event outside of a scene")
            current_scene["events"].append(token)
            logger.debug(
                f"Adding event type '{token['type']}' to scene '{current_scene['name']}'"
            )

    expanded_scenes = {}
    for scene_name, scene_data in scenes.items():
        logger.info(f"Expanding scene: {scene_name}")
        expanded_events = []
        for event in scene_data["events"]:
            if event["type"] == "macro":
                macro_name = event["name"]
                logger.info(
                    f"Attempting to expand macro '{macro_name}' in scene '{scene_name}'"
                )
                if macro_name not in scenes:
                    logger.error(
                        f"Macro '{macro_name}' not found in scene '{scene_name}'. Raising ValueError."
                    )
                    raise ValueError(
                        f"Macro '{macro_name}' not found in scene '{scene_name}'"
                    )
                # Substitute the macro token with the events from the target scene
                expanded_events.extend(scenes[macro_name]["events"])
                logger.debug(
                    f"Expanded macro '{macro_name}' with {len(scenes[macro_name]['events'])} events."
                )

            elif event["type"] == "codeblock":
                lang = event["lang"]
                logger.debug(f"Parsing codeblock of language: {lang}")
                for line in event["content"]:
                    # --- Character commands ---
                    if lang == "char":
                        if m := char_show_re.match(line):
                            expanded_events.append(
                                {
                                    "type": "char_show",
                                    "char_id": m.group(1),
                                    "image_name": m.group(2),
                                    "x": float(m.group(3)),
                                    "y": float(m.group(4)),
                                    "scale": float(m.group(5)) if m.group(5) else 1.0,
                                }
                            )
                            logger.debug(f"Parsed char_show for {m.group(1)}: {line}")
                        elif m := char_hide_re.match(line):
                            expanded_events.append(
                                {"type": "char_hide", "char_id": m.group(1)}
                            )
                            logger.debug(f"Parsed char_hide for {m.group(1)}: {line}")
                        elif m := char_move_re.match(line):
                            expanded_events.append(
                                {
                                    "type": "char_move",
                                    "char_id": m.group(1),
                                    "x": float(m.group(2)),
                                    "y": float(m.group(3)),
                                    "duration": (
                                        float(m.group(4)) if m.group(4) else 0.5
                                    ),
                                }
                            )
                            logger.debug(f"Parsed char_move for {m.group(1)}: {line}")
                        elif m := char_expr_re.match(line):
                            expanded_events.append(
                                {
                                    "type": "char_expr",
                                    "char_id": m.group(1),
                                    "image_name": m.group(2),
                                }
                            )
                            logger.debug(f"Parsed char_expr for {m.group(1)}: {line}")
                        else:
                            logger.warning(
                                f"Unknown 'char' command in codeblock: {line}"
                            )

                    # --- Transition commands ---
                    elif lang == "transition":
                        if m := fade_out_re.match(line):
                            duration = float(m.group(1)) if m.group(1) else 1.0
                            color = (
                                (
                                    int(m.group(2)),
                                    int(m.group(3)),
                                    int(m.group(4)),
                                    int(m.group(5)) if m.group(5) else 255,
                                )
                                if m.group(2)
                                else (0, 0, 0, 255)
                            )
                            expanded_events.append(
                                {
                                    "type": "fade_out",
                                    "duration": duration,
                                    "color": color,
                                }
                            )
                            logger.debug(f"Parsed fade_out: {line}")
                        elif m := fade_in_re.match(line):
                            duration = float(m.group(1)) if m.group(1) else 1.0
                            color = (
                                (
                                    int(m.group(2)),
                                    int(m.group(3)),
                                    int(m.group(4)),
                                    int(m.group(5)) if m.group(5) else 255,
                                )
                                if m.group(2)
                                else (0, 0, 0, 255)
                            )
                            expanded_events.append(
                                {
                                    "type": "fade_in",
                                    "duration": duration,
                                    "color": color,
                                }
                            )
                            logger.debug(f"Parsed fade_in: {line}")
                        else:
                            logger.warning(
                                f"Unknown 'transition' command in codeblock: {line}"
                            )

                    else:
                        # Unknown codeblock type: keep raw
                        expanded_events.append(event)
                        logger.warning(
                            f"Unknown codeblock language '{lang}'. Keeping raw token for line: {line}"
                        )

            else:
                expanded_events.append(event)
                logger.debug(f"Keeping raw event type: {event['type']}")

        logger.info(
            f"Finished expanding scene: {scene_name}. Total expanded events: {len(expanded_events)}"
        )
        expanded_scenes[scene_name] = {"name": scene_name, "events": expanded_events}

    logger.info(f"Parsing complete. Total expanded scenes: {len(expanded_scenes)}")
    return expanded_scenes


# --- Condition Evaluator ---
def parse_value(val):
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    try:
        return int(val)
    except ValueError:
        return val.strip('"').strip("'")

def check_condition(cond, state):
    if not cond:
        return True
    parts = cond.split()
    if len(parts) == 1:
        return bool(state.get(parts[0], False))
    elif len(parts) == 3:
        var, op, val = parts
        sval = state.get(var, 0)
        val = parse_value(val)
        if op == "==":
            return sval == val
        if op == "!=":
            return sval != val
        if op == ">":
            return sval > val
        if op == "<":
            return sval < val
        if op == ">=":
            return sval >= val
        if op == "<=":
            return sval <= val
    return False

if __name__ == "__main__":
    with open("script.md", "r") as f:
        script = f.read()

    tokens = tokenize(script.splitlines())
    graph = parse(tokens)
    print(graph)
