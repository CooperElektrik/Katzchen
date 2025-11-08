from katzchen import parser
import json

if __name__ == "__main__":
    with open("scripts/example.md", "r") as f:
        script = f.read()

    tokens = parser.tokenize(script.splitlines())
    print(tokens)
    graph = parser.parse(tokens)
    print(
        json.dumps(
            graph
        , indent=4,default=str
        )
    )