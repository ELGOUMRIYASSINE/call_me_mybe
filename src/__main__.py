import json
import sys

from .data_checker import DataChecker

class Engine():
    def __init__(self):
        self.data_source = {}
    def checker(self):
        try:
            if len(sys.argv) > 1:
                checker = DataChecker(sys.argv)
                self.data_source = checker.check()
            else:
                self.data_source["functions_definition"] = "functions_definition.json"
                self.data_source["input"] = "function_calling_tests.json"
                self.data_source["output"] = "function_calls.json"
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            print("Somthing Went Wrong => ", e.__str__())

Engine1 = Engine()
Engine1.checker()


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