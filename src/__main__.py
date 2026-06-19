import json
import sys
from llm_sdk import Small_LLM_Model as sdk
from .data_checker import DataChecker

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
        func_prompt = None
        i = 0
        for function in self.functions_definition:
            func_prompt += f"- {function["name"]}("
            for parameter in function["parameters"]:
                if i == 0:
                    func_prompt += ","
                func_prompt += f"{parameter}:{parameter["type"]}"
            i += 1
    def main(self):
        try:
            self.checker()
            self.load()
            valide_tokens_ids = self.get_valid_token()
            for prompt in self.prompts:
                general_prompt = f''' You are a function calling assistant. Your task is to analyze a user request and respond with a single JSON object that calls the correct function with the correct arguments.

                                    Available functions:
                                    - fn_add_numbers(a: number, b: number): Add two numbers together and return their sum.
                                    - fn_greet(name: string): Generate a greeting message for a person by name.
                                    - fn_reverse_string(s: string): Reverse a string and return the reversed result.

                                    You must respond using exactly this JSON format and nothing else:
                                    {"name": "<function_name>", "parameters": {"<param1>": <value1>, "<param2>": <value2>}}

                                    Do not include any explanation, extra text, or formatting outside the JSON object.

                                    User request: {prompt["prompt"]}

                                    Function call:
                                '''

        except Exception as e:
            print(f"Error -> {e}")
        # start constraining
        # result = ""
        
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