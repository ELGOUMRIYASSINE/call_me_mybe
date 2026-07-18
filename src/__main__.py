"""Generate function-call JSON results from prompts."""
import json
import sys
from typing import Any, cast
from llm_sdk import Small_LLM_Model as sdk
from .data_checker import DataChecker
from .pydantic_rules import FunctionDefinition, PromptItem
from .constrained_tools import (
    get_next_func_token,
    get_valid_tokens,
    next_token_getter,
    state_printer,
    functions_as_prompt,
)


class Engine:
    """Run the model and build one function call per user prompt."""

    def __init__(self) -> None:
        self.data_source: dict[str, str] = {}
        self.prompts: list[PromptItem] = []
        self.functions_definition: list[FunctionDefinition] = []
        self.llm: sdk | None = None

    @staticmethod
    def _encode_to_ids(llm_obj: sdk, text: str) -> list[int]:
        """Return a flat list of token ids "
        "regardless of tensor/list internals."""
        encoded_ids = cast(Any, llm_obj.encode(text)).tolist()
        if encoded_ids and isinstance(encoded_ids[0], list):
            return cast(list[int], encoded_ids[0])
        return cast(list[int], encoded_ids)

    def checker(self) -> None:
        """Load the input files and validate their content."""
        try:
            checker = DataChecker(sys.argv)
            self.data_source = checker.check()
            try:
                self.llm = sdk(self.data_source["model"])
            except Exception:
                print("Error: Invalide llm")
                exit()
            checker.valid_json()
            self.functions_definition = [
                FunctionDefinition.model_validate(item)
                for item in checker.func_def_final
            ]
            # print("All files are valid and ready to be processed.")
            # exit()
            self.prompts = [
                PromptItem.model_validate(item)
                for item in checker.inputes_final
            ]
        except (json.JSONDecodeError, FileNotFoundError, Exception):
            print(
                "Somthing Went Wrong With Your provided file or default files"
            )
            # raise SystemExit(1)
            exit()

    def grep_prompt(self, prompt: PromptItem) -> str:
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
            f"{functions_as_prompt(self.functions_definition)}\n"
            "You must respond using exactly this "
            "JSON format and nothing else:\n"
            f"{example}\n"
            "Do not include any explanation, extra text, or formatting "
            "outside the JSON object.\n\n"
            f"User request: {prompt.prompt}\n\n"
            "Function call:\n"
        )

    def main(self) -> None:
        """Generate the final JSON output file."""
        self.checker()
        llm_obj = self.llm
        if llm_obj is None:
            raise SystemExit(1)
        functions_definition_raw = [
            function.model_dump() for function in self.functions_definition
        ]
        valid_data = get_valid_tokens(llm_obj, functions_definition_raw)
        tools = {
            "start": '"name":"',
            "start_close": '",',
            "start_params": '"parameters":{',
        }
        function_names = [func.name for func in self.functions_definition]
        valid_functions_tokens = valid_data["name"]
        results: list[dict[str, Any]] = []

        for prompt in self.prompts:
            if not prompt.prompt:
                print("Warning: empty string founded (passed)")
                continue
            state = "name"
            general_prompt = self.grep_prompt(prompt) + tools["start"]
            prompt_text = prompt.prompt.replace('"', '\\"')
            result = (
                '{'
                + '"prompt": '
                + json.dumps(prompt_text)
                + ','
                + tools["start"]
            )
            # result = '{' + f'"prompt": "{prompt_text}",' + tools["start"]
            valid_tokens = get_next_func_token(valid_functions_tokens)
            tokens = llm_obj.get_logits_from_input_ids(
                self._encode_to_ids(llm_obj, general_prompt)
            )
            output = next_token_getter(llm_obj, tokens, valid_tokens)
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
                            if obj.name == function_name
                        ][0]
                        for index, (param_name, param_type) in enumerate(
                            func_obj.parameters.items()
                        ):
                            valid_tokens = valid_data[param_type.type]
                            output = ""
                            if index != 0:
                                result += ","
                                general_prompt += ","
                            if param_type.type == "string":
                                result += f'"{param_name}":"'
                                general_prompt += f'"{param_name}":"'
                            else:
                                result += f'"{param_name}":'
                                general_prompt += f'"{param_name}":'

                            token_counter = 0
                            while (
                                "," not in output
                                and "}" not in output
                                and token_counter <= 50
                            ):
                                tokens = llm_obj.get_logits_from_input_ids(
                                    self._encode_to_ids(llm_obj,
                                                        general_prompt)
                                )
                                output = next_token_getter(
                                    llm_obj, tokens, valid_tokens
                                )
                                token_counter += 1
                                if "," not in output and "}" not in output:
                                    output = DataChecker.escape_detecter(
                                        output
                                    )
                                    general_prompt += output
                                    result += output

                            if param_type.type == "string":
                                general_prompt += '"'
                                result += '"'
                            elif (param_type.type == "number"
                                  and "." not in result):
                                result += ".0"
                                general_prompt += ".0"

                        general_prompt += "}}"
                        result += "}}"
                        general_prompt += "\n"
                        break

                if not name_found:
                    tokens = llm_obj.get_logits_from_input_ids(
                        self._encode_to_ids(llm_obj, general_prompt)
                    )
                    output_ids = self._encode_to_ids(llm_obj, output)
                    old_token = output_ids[0] if output_ids else None
                    valid_tokens = get_next_func_token(
                        valid_functions_tokens,
                        old_token,
                    )
                    output = next_token_getter(llm_obj, tokens, valid_tokens)
                    result += output
                    general_prompt += output

            state_printer(result)
            results.append(json.loads(result))

        # create missing directories
        with open(self.data_source["output"], "w") as file:
            json.dump(results, file, indent=4)


if __name__ == "__main__":
    Engine().main()
