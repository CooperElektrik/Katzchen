import re

codeblock_re = re.compile(r"^```(\w+)\s*$")
endblock_re = re.compile(r"^```$")

# --- Tokenizer ---
def tokenize(lines):
    tokens = []
    in_block = None
    block_content = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if not in_block:
            m = codeblock_re.match(line)
            if m:
                in_block = m.group(1)  # language tag (e.g. "char", "transition")
                block_content = []
                continue
        else:
            # End of block
            if endblock_re.match(line):
                tokens.append({
                    "type": "codeblock",
                    "lang": in_block,
                    "content": block_content
                })
                in_block = None
                continue
            block_content.append(line)
            continue

        # Scene header
        if line.startswith("##"):
            name = line[2:].strip()
            tokens.append({"type": "scene", "name": name})

        # Choice line: - [Text](target) [optional: set var=value]
        elif line.startswith("- ["):
            match = re.match(
                r"- \[(.+?)\]\((.+?)\)(?:\s+set\s+(\w+)\s*=\s*(.+))?", line
            )
            if match:
                tokens.append(
                    {
                        "type": "choice",
                        "text": match.group(1),
                        "target": match.group(2),
                        "set": (
                            (match.group(3), match.group(4)) if match.group(3) else None
                        ),
                    }
                )

        # Dialogue line: **Name**: text
        elif line.startswith("**"):
            match = re.match(r"\*\*(.+?)\*\*: (.+)", line)
            if match:
                tokens.append(
                    {
                        "type": "dialogue",
                        "speaker": match.group(1),
                        "text": match.group(2),
                    }
                )

        # Jump: > target ? condition
        elif line.startswith(">"):
            match = re.match(r">\s*(\w+)(?:\s*\?\s*(.+))?", line)
            if match:
                tokens.append(
                    {
                        "type": "jump",
                        "target": match.group(1),
                        "condition": match.group(2),
                    }
                )

        # Assignment: @ var = value
        elif line.startswith("@"):
            match = re.match(r"@\s*(\w+)\s*=\s*(.+)", line)
            if match:
                tokens.append(
                    {
                        "type": "set",
                        "var": match.group(1),
                        "value": match.group(2).strip(),
                    }
                )

        # Macro: {{namee}}
        elif line.startswith("{{") and line.endswith("}}"):
            macro_name = line[2:-2].strip()
            tokens.append({"type": "macro", "name": macro_name})

        # Narration fallback
        else:
            tokens.append({"type": "narration", "text": line})

    return tokens


# --- Parser ---
def parse(tokens):
    scenes = {}
    current_scene = None
    for token in tokens:
        if token["type"] == "scene":
            current_scene = {"name": token["name"], "events": []}
            scenes[token["name"]] = current_scene
        else:
            if not current_scene:
                raise ValueError("Event outside of a scene")
            current_scene["events"].append(token)

    expanded_scenes = {}
    for scene_name, scene_data in scenes.items():
        expanded_events = []
        for event in scene_data["events"]:
            if event["type"] == "macro":
                macro_name = event["name"]
                if macro_name not in scenes:
                    raise ValueError(
                        f"Macro '{macro_name}' not found in scene '{scene_name}'"
                    )
                # Substitute the macro token with the events from the target scene
                expanded_events.extend(scenes[macro_name]["events"])

            elif event["type"] == "codeblock":
                lang = event["lang"]
                for line in event["content"]:
                    # --- Character commands ---
                    if lang == "char":
                        if m := re.match(r"show\s+(\w+)\s+(\S+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)(?:\s+(\d+\.?\d*))?", line):
                            expanded_events.append({
                                "type": "char_show",
                                "char_id": m.group(1),
                                "image_name": m.group(2),
                                "x": float(m.group(3)),
                                "y": float(m.group(4)),
                                "scale": float(m.group(5)) if m.group(5) else 1.0
                            })
                        elif m := re.match(r"hide\s+(\w+)", line):
                            expanded_events.append({
                                "type": "char_hide",
                                "char_id": m.group(1)
                            })
                        elif m := re.match(r"move\s+(\w+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)(?:\s+(\d+\.?\d*))?", line):
                            expanded_events.append({
                                "type": "char_move",
                                "char_id": m.group(1),
                                "x": float(m.group(2)),
                                "y": float(m.group(3)),
                                "duration": float(m.group(4)) if m.group(4) else 0.5
                            })
                        elif m := re.match(r"expr\s+(\w+)\s+(\S+)", line):
                            expanded_events.append({
                                "type": "char_expr",
                                "char_id": m.group(1),
                                "image_name": m.group(2)
                            })

                    # --- Transition commands ---
                    elif lang == "transition":
                        if m := re.match(r"fade_out(?:\s+(\d+\.?\d*))?(?:\s+\((\d+),(\d+),(\d+)(?:,(\d+))?\))?", line):
                            duration = float(m.group(1)) if m.group(1) else 1.0
                            color = (
                                int(m.group(2)), int(m.group(3)), int(m.group(4)),
                                int(m.group(5)) if m.group(5) else 255
                            ) if m.group(2) else (0, 0, 0, 255)
                            expanded_events.append({
                                "type": "fade_out",
                                "duration": duration,
                                "color": color
                            })
                        elif m := re.match(r"fade_in(?:\s+(\d+\.?\d*))?(?:\s+\((\d+),(\d+),(\d+)(?:,(\d+))?\))?", line):
                            duration = float(m.group(1)) if m.group(1) else 1.0
                            color = (
                                int(m.group(2)), int(m.group(3)), int(m.group(4)),
                                int(m.group(5)) if m.group(5) else 255
                            ) if m.group(2) else (0, 0, 0, 255)
                            expanded_events.append({
                                "type": "fade_in",
                                "duration": duration,
                                "color": color
                            })

                    else:
                        # Unknown codeblock type: keep raw
                        expanded_events.append(event)

            else:
                expanded_events.append(event)

        expanded_scenes[scene_name] = {"name": scene_name, "events": expanded_events}

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
