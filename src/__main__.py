import json
import sys

from .data_checker import DataChecker

class Engine():
    def __init__(self):
        self.data_source = {}
        self.prompts = {}
        self.functions_definition = {}
        self.statics = ['{"prompt":', ',"name": ', ',"parameters": ', '},']
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

    def main(self):
        try:
            self.checker()
            print(self.functions_definition)
            print(self.prompts)
            # self.load()
        except Exception as e:
            print(f"Error -> {e}")
        # start constraining
        result = ""
        general_prompt = """You are a function calling assistant. Your task is to analyze a user request and respond with a single JSON object that calls the correct function with the correct arguments.

            Available functions:
            - fn_add_numbers(a: number, b: number): Add two numbers together and return their sum.
            - fn_greet(name: string): Generate a greeting message for a person by name.
            - fn_reverse_string(s: string): Reverse a string and return the reversed result.

            You must respond using exactly this JSON format and nothing else:
            {"name": "<function_name>", "parameters": {"<param1>": <value1>, "<param2>": <value2>}}

            Do not include any explanation, extra text, or formatting outside the JSON object.

            User request: "What is the sum of 2 and 3?"

            Function call:
            """
        # for prmpt in self.prompts:

        # print(self.prompts)
        # print("break")
        # print(self.functions_definition)

Engine1 = Engine()
Engine1.main()


# try:
#     with open("data/input/functions_definition.json", "r") as f:
#         dd = json.load(f)
#         print(dd)
# except json.decoder.JSONDecodeError:
#     print("Json format incorrect")

# from llm_sdk import Small_LLM_Model

# model = Small_LLM_Model()

# print(model.encode("yassine"))

# with open(model.get_path_to_vocab_file(), "r") as f:
#     vocab = json.load(f)

# # id_to_token = {v: k for k, v in vocab.items()}

# # print(id_to_token)
# prompt = """You are a function calling assistant. Your task is to analyze a user request and respond with a single JSON object that calls the correct function with the correct arguments.

# Available functions:
# - fn_add_numbers(a: number, b: number): Add two numbers together and return their sum.
# - fn_greet(name: string): Generate a greeting message for a person by name.
# - fn_reverse_string(s: string): Reverse a string and return the reversed result.

# You must respond using exactly this JSON format and nothing else:
# {"name": "<function_name>", "parameters": {"<param1>": <value1>, "<param2>": <value2>}}

# Do not include any explanation, extra text, or formatting outside the JSON object.

# User request: "What is the sum of 2 and 3?"

# Function call:
# """
# statics = ['{"name": "' '", "parameters": {']

# # state = True
# result = ""
# i = 0
# while i < 25:
#     logits = model.get_logits_from_input_ids(model.encode(prompt)[0].tolist())
#     result += model.decode(logits.index(max(logits)))
#     prompt += result  
#     i += 1

# print(result)
# # print(logits)

# # print(model.decode(logits.index(max(logits))))