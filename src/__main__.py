import json
import sys
from llm_sdk import Small_LLM_Model as sdk
from .data_checker import DataChecker
import numpy as np

class Engine():
    def __init__(self):
        self.data_source = {}
        self.prompts = {}
        self.functions_definition = {}
        self.statics = ['{"prompt":', ',"name": ', ',"parameters": ', '},']
        self.llm = sdk()

    def checker(self) -> None:
        try:
            if len(sys.argv) > 1:
                checker = DataChecker(sys.argv)
                self.data_source = checker.check()
                checker.valid_json()
                self.functions_definition = checker.func_def_final
                self.prompts = checker.inputes_final
            else:
                self.data_source["functions_definition"] = "data/input/functions_definition.json"
                self.data_source["input"] = "data/input/function_calling_tests.json"
                self.data_source["output"] = "data/output/function_calls.json"
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            print("Somthing Went Wrong => ", e.__str__())

    def load(self) -> None:
        with open(self.data_source['input'], 'r') as inpt, open(self.data_source["functions_definition"], 'r') as funcdef:
            try:
                self.prompts = json.load(inpt)
                self.functions_definition = json.load(funcdef)
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"File not found: '{e.filename}'."
                )
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON format in line {e.lineno}, column {e.colno}: {e.msg}"
                )
            except PermissionError as e:
                raise PermissionError(
                    f"Permission denied: '{e.filename}'."
                )
            except KeyError as e:
                raise KeyError(
                    f"Missing configuration key: {e}"
                )

    def get_valid_token(self):
        vocab = self.llm.get_path_to_vocab_file()
        valide_tokens = None
        valid_char = "abcdefghijklmnopqrstuvwxyz0123456789_{}\":,.-"
        try:
            tokens = None
            with open(vocab, "r") as file:
                tokens = json.load(file)
            valide_tokens = {
                token_id
                for token_str, token_id in tokens.items()
                if all(c in valid_char for c in token_str)
            }
        except FileNotFoundError:
            print("Vocab file not found!")
        return valide_tokens

    def functions_as_prompt(self):
        func_prompt = ""
        i = 0
        for function in self.functions_definition:
            func_prompt += f"- {function['name']}("
            for p_name, p_type in function["parameters"].items():
                if i != 0:
                    func_prompt += ", "
                func_prompt += f"{p_name}:{p_type}"
                i += 1
            func_prompt += f"): {function['description']} \n"
        return func_prompt
    
    def grep_prompt(self, prompt):
        general_prompt = ""
        start = '{"name": '
        example = '"name": "<function_name>", "parameters": {"<param1>": <value1>, "<param2>": <value2>}'
        general_prompt = f"""
You are a function calling assistant. Your task is to analyze a user request and respond with a single JSON object that calls the correct function with the correct arguments.
Available functions:
{self.functions_as_prompt()}
You must respond using exactly this JSON format and nothing else:
{example}
Do not include any explanation, extra text, or formatting outside the JSON object.

User request: {prompt["prompt"]}

Function call:
{start}
"""
        return general_prompt

    def main(self):
        self.checker()
        self.load()
        try:
            valide_tokens_ids = self.get_valid_token()
            with open("result.json", "w") as file:
                for prompt in self.prompts:
                    generated_prompt = self.grep_prompt(prompt)
                    i = 0
                    tracker = 0 
                    start = '{"name": '
                    file.write(start)
                    while i < 25:
                        logits = self.llm.get_logits_from_input_ids(self.llm.encode(generated_prompt)[0].tolist())
                        logits = np.array(logits)
                        masked_logits = np.full_like(logits, float('-inf'))

                        for token in valide_tokens_ids:
                                masked_logits[token] = logits[token]
                        next_token_id = int(np.argmax(masked_logits))
                        output = self.llm.decode(next_token_id)
                        start += output
                        file.write(output)
                        generated_prompt += output
                        if start[len(start) - 1] == "," and tracker == 0:
                            generated_prompt += ', "parameters": {'
                            start += ', "parameters": {'
                            tracker += 1
                        if start[len(start) - 1] == "}" and start[len(start) - 2] == "}":
                            i = 25
                        i += 1
                    # exit()

        except Exception as e:
            raise e

Engine1 = Engine()
Engine1.main()