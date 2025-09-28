import re

# --- Tokenizer ---
def tokenize(lines):
    tokens = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Scene header
        if line.startswith("##"):
            name = line[2:].strip()
            tokens.append({"type": "scene", "name": name})

        # Choice line: - [Text](target) [optional: set var=value]
        elif line.startswith("- ["):
            match = re.match(r"- \[(.+?)\]\((.+?)\)(?:\s+set\s+(\w+)\s*=\s*(.+))?", line)
            if match:
                tokens.append({
                    "type": "choice",
                    "text": match.group(1),
                    "target": match.group(2),
                    "set": (match.group(3), match.group(4)) if match.group(3) else None
                })

        # Dialogue line: **Name**: text
        elif line.startswith("**"):
            match = re.match(r"\*\*(.+?)\*\*: (.+)", line)
            if match:
                tokens.append({
                    "type": "dialogue",
                    "speaker": match.group(1),
                    "text": match.group(2)
                })

        # Jump: > target ? condition
        elif line.startswith(">"):
            match = re.match(r">\s*(\w+)(?:\s*\?\s*(.+))?", line)
            if match:
                tokens.append({
                    "type": "jump",
                    "target": match.group(1),
                    "condition": match.group(2)
                })

        # Assignment: @ var = value
        elif line.startswith("@"):
            match = re.match(r"@\s*(\w+)\s*=\s*(.+)", line)
            if match:
                tokens.append({
                    "type": "set",
                    "var": match.group(1),
                    "value": match.group(2).strip()
                })

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
    return scenes


# --- Condition Evaluator ---
def parse_value(val):
    if val.lower() == "true": return True
    if val.lower() == "false": return False
    try:
        return int(val)
    except ValueError:
        return val.strip('"').strip("'")
    
