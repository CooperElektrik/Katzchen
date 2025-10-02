from parser import parse_value, parse, tokenize, check_condition

def play(scenes, start_scene, state=None):
    if state is None:
        state = {}
    scene = scenes[start_scene]

    while scene:
        i = 0
        while i < len(scene["events"]):
            event = scene["events"][i]

            if event["type"] == "dialogue":
                print(f"{event['speaker']}: {event['text']}")
                input()
                i += 1

            elif event["type"] == "narration":
                print(event["text"])
                input()
                i += 1

            elif event["type"] == "set":
                state[event["var"]] = parse_value(event["value"])
                i += 1

            elif event["type"] == "jump":
                if check_condition(event["condition"], state):
                    scene = scenes[event["target"]]
                    break
                else:
                    i += 1

            elif event["type"] == "choice":
                # gather consecutive choices
                choices = []
                while (
                    i < len(scene["events"]) and scene["events"][i]["type"] == "choice"
                ):
                    choices.append(scene["events"][i])
                    i += 1

                print("\nChoose:")
                for idx, c in enumerate(choices, 1):
                    print(f"  {idx}. {c['text']}")
                while True:
                    sel = input("> ")
                    if sel.isdigit() and 1 <= int(sel) <= len(choices):
                        chosen = choices[int(sel) - 1]
                        if chosen["set"]:
                            var, val = chosen["set"]
                            state[var] = parse_value(val)
                        scene = scenes[chosen["target"]]
                        break
                    else:
                        print("Invalid choice, try again.")
                break  # jump ends current scene
            else:
                print(f"Unrecognized event type {event['type']}. Are you using the correct version of the script? Skipping...")
                i += 1
        else:
            scene = None


if __name__ == "__main__":

    with open("script.md", "r") as f:
        script = f.read()

    tokens = tokenize(script.splitlines())
    graph = parse(tokens)

    play(graph, "Start")
