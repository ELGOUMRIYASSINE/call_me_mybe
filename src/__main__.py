"""Generate function-call JSON results from prompts."""

import json
import string
import sys
from pathlib import Path
import numpy as np
from llm_sdk import Small_LLM_Model as sdk
from .data_checker import DataChecker


class Engine:
    """Run the model and build one function call per user prompt."""

    def __init__(self):
        self.data_source = {}
        self.prompts = {}
        self.functions_definition = {}
        self.llm = sdk()

    def checker(self) -> None:
        """Load the input files and validate their content."""
        try:
            checker = DataChecker(sys.argv)
            self.data_source = checker.check()
            checker.valid_json()
            self.functions_definition = checker.func_def_final
            self.prompts = checker.inputes_final
        except (json.JSONDecodeError, FileNotFoundError):
            print("Somthing Went Wrong With Your provided file or default files")
            raise SystemExit(1)

    def get_next_func_token(self, func_tokens, old_token=None):
        """Return the next valid token ids for function names."""
        tokens = []
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

    def get_valid_tokens(self):
        """Split the vocabulary into name, string, and number tokens."""
        function_names = [func["name"] for func in self.functions_definition]
        function_tokens = []
        string_tokens = []
        number_tokens = []
        number_chars = set("0123456789.,}-")

        for func_name in function_names:
            function_tokens.append(self.llm.encode(func_name)[0].tolist())

        with open(self.llm.get_path_to_vocab_file(), "r") as vocab_data:
            vocab = json.load(vocab_data)
            decoded_vocab = {
                self.llm.decode([token_id]): token_id
                for token_id in vocab.values()
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

    def functions_as_prompt(self):
        """Turn the function schema into a readable list for the prompt."""
        lines = []
        for function in self.functions_definition:
            parameters = ", ".join(
                f"{name}:{spec['type']}" for name, spec in function["parameters"].items()
            )
            lines.append(
                f"- {function['name']}({parameters}): {function['description']}"
            )
        return "\n".join(lines)

    def grep_prompt(self, prompt):
        """Build the instruction prompt for one user request."""
        example = (
            '{"name": "<function_name>", "parameters": '
            '{"<param1>": <value1>, "<param2>": <value2>}}'
        )
        return (
            "You are a function calling assistant. Your task is to analyze "
            "a user request and respond with a single JSON object that calls "
            "the correct function with the correct arguments.\n"
            "Available functions:\n"
            f"{self.functions_as_prompt()}\n"
            "You must respond using exactly this JSON format and nothing else:\n"
            f"{example}\n"
            "Do not include any explanation, extra text, or formatting "
            "outside the JSON object.\n\n"
            f'User request: {prompt["prompt"]}\n\n'
            "Function call:\n"
        )

    def next_token_getter(self, logits, valid_tokens):
        """Pick the best token from the allowed token ids."""
        masked_tokens = np.full_like(logits, float("-inf"))
        valid_tokens = list(dict.fromkeys(valid_tokens))
        for token in valid_tokens:
            masked_tokens[token] = logits[token]
        return self.llm.decode(int(np.argmax(masked_tokens)))

    def state_printer(self, text):
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

    def main(self):
        """Generate the final JSON output file."""
        self.checker()
        valid_data = self.get_valid_tokens()
        tools = {
            "start": '"name":"',
            "start_close": '",',
            "start_params": '"parameters":{',
        }
        function_names = [func["name"] for func in self.functions_definition]
        valid_functions_tokens = valid_data["name"]
        results = []

        for prompt in self.prompts:
            state = "name"
            general_prompt = self.grep_prompt(prompt) + tools["start"]
            prompt_text = prompt["prompt"].replace('"', '\\"')
            result = (
                '{'
                + '"prompt": '
                + json.dumps(prompt_text)
                + ','
                + tools["start"]
            )
            # result = '{' + f'"prompt": "{prompt_text}",' + tools["start"]
            valid_tokens = self.get_next_func_token(valid_functions_tokens)
            tokens = self.llm.get_logits_from_input_ids(
                self.llm.encode(general_prompt)[0].tolist()
            )
            output = self.next_token_getter(tokens, valid_tokens)
            general_prompt += output
            result += output
            name_found = False

            while "}}" not in result:
                for function_name in function_names:
                    if function_name in result and state == "name":
                        general_prompt += tools["start_close"]
                        result += tools["start_close"]
                        state = "parameters"
                        name_found = True

                    if state == "parameters":
                        general_prompt += tools["start_params"]
                        result += tools["start_params"]
                        func_obj = [
                            obj
                            for obj in self.functions_definition
                            if obj["name"] == function_name
                        ][0]
                        for index, (param_name, param_type) in enumerate(
                            func_obj["parameters"].items()
                        ):
                            valid_tokens = valid_data[param_type["type"]]
                            output = ""
                            if index != 0:
                                result += ","
                                general_prompt += ","
                            if param_type["type"] == "string":
                                result += f'"{param_name}":"'
                                general_prompt += f'"{param_name}":"'
                            else:
                                result += f'"{param_name}":'
                                general_prompt += f'"{param_name}":'

                            escape_detected = False
                            token_counter = 0
                            while (
                                "," not in output
                                and "}" not in output
                                and token_counter <= 50
                            ):
                                tokens = self.llm.get_logits_from_input_ids(
                                    self.llm.encode(general_prompt)[0].tolist()
                                )
                                output = self.next_token_getter(tokens, valid_tokens)
                                token_counter += 1
                                if "," not in output and "}" not in output:
                                    if '"' in output:
                                        result += "\\"
                                        general_prompt += "\\"
                                    if escape_detected:
                                        if output != '"':
                                            general_prompt += "\\"
                                            result += "\\"
                                        escape_detected = False
                                    if output == "\\":
                                        escape_detected = True
                                    general_prompt += output
                                    result += output

                            if param_type["type"] == "string":
                                general_prompt += '"'
                                result += '"'
                            elif param_type["type"] == "number" and "." not in result:
                                result += ".0"
                                general_prompt += ".0"

                        general_prompt += "}}"
                        result += "}}"
                        general_prompt += "\n"
                        break

                if not name_found:
                    tokens = self.llm.get_logits_from_input_ids(
                        self.llm.encode(general_prompt)[0].tolist()
                    )
                    valid_tokens = self.get_next_func_token(
                        valid_functions_tokens,
                        self.llm.encode(output)[0].tolist()[0],
                    )
                    output = self.next_token_getter(tokens, valid_tokens)
                    result += output
                    general_prompt += output

            self.state_printer(result)
            results.append(json.loads(result))

        # create missing directories
        path = Path(self.data_source["output"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_source["output"], "w") as file:
            json.dump(results, file, indent=4)


if __name__ == "__main__":
    Engine().main()
