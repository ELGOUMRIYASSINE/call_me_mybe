import string
import sys
import json
from typing import Any

import numpy as np


def get_next_func_token(
    func_tokens: list[list[int]],
    old_token: int | None = None,
) -> list[int]:
    """Return the next valid token ids for function names."""
    tokens: list[int] = []
    for func in func_tokens:
        if old_token is None:
            first_token = func[0]
            if first_token not in tokens:
                tokens.append(first_token)
            continue

        for index, token in enumerate(func[:-1]):
            if token == old_token:
                tokens.append(func[index + 1])
                break
    return tokens


def get_valid_tokens(llm_obj: Any, functions_definition: list) -> dict:
    """Split the vocabulary into name, string, and number tokens."""
    function_names = [func["name"] for func in functions_definition]
    function_tokens: list[list[int]] = []
    string_tokens: list[int] = []
    number_tokens: list[int] = []
    number_chars = set("0123456789.,}-")

    for func_name in function_names:
        function_tokens.append(llm_obj.encode(func_name)[0].tolist())

    with open(llm_obj.get_path_to_vocab_file(), "r") as vocab_data:
        vocab = json.load(vocab_data)
        decoded_vocab = {
            llm_obj.decode([token_id]): token_id
            for token_id in vocab.values()
            if isinstance(token_id, int)
        }

        for token, token_id in decoded_vocab.items():
            if not token:
                continue
            if all(character in string.printable for character in token):
                string_tokens.append(token_id)
            if all(character in number_chars for character in token):
                number_tokens.append(token_id)

    return {
        "name": function_tokens,
        "number": number_tokens,
        "string": string_tokens,
        "integer": number_tokens,
    }


def next_token_getter(
    llm_obj: Any, logits: list[float], valid_tokens: list[int]
) -> Any:
    """Pick the best token from the allowed token ids."""
    masked_tokens = np.full_like(logits, float("-inf"))
    valid_tokens = list(dict.fromkeys(valid_tokens))
    for token in valid_tokens:
        masked_tokens[token] = logits[token]
    return llm_obj.decode([int(np.argmax(masked_tokens))])


def state_printer(text: str) -> None:
    """Print a JSON-like string with a simple indentation style."""
    indent = 0
    for character in text:
        if character == "{":
            sys.stdout.write("{\n")
            indent += 1
            sys.stdout.write("   " * indent)
        elif character == "}":
            sys.stdout.write("\n")
            indent -= 1
            sys.stdout.write("   " * indent)
            sys.stdout.write("}")
        elif character == ",":
            sys.stdout.write(",\n")
            sys.stdout.write("   " * indent)
        else:
            sys.stdout.write(character)


def functions_as_prompt(functions_definition: list) -> str:
    """Turn the function schema into a readable list for the prompt."""
    lines = []
    for function in functions_definition:
        parameters = ", ".join(
            f"{name}:{spec.type}"
            for name, spec in function.parameters.items()
        )
        lines.append(
            f"- {function.name}({parameters}): {function.description}"
        )
    return "\n".join(lines)
