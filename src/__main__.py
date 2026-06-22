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


    def get_valid_token(self, step, result=None, index=0):
        vocab = self.llm.get_path_to_vocab_file()
        valide_tokens = None
        functions_tokens = ["fn","_add","_numbers","_g","reet","_reverse","_string","_get","_square","_root","_sub","stitute","_with","_regex"]       
        string = "abcdefghijklmnopqrstuvwxyz"
        number = "0123456789."
        function_names = [func["name"] for func in self.functions_definition]
        if step == "name":
            return functions_tokens
        elif step == "parameter":
            func_name = ""
            for func in function_names:
                if func in result:
                    func_name = func
            for name, type in self.functions_definition[func_name]["parameters"].items():
                if not name in result:
                    if type == "number":
                        return number
                    elif type == "string":
                        return string
        try:
            tokens = None

            with open(vocab, "r") as file:
                tokens = json.load(file)
            valide_tokens = {
                token_id
                for token_str, token_id in tokens.items()
                if all(c in valid_chars for c in token_str)
            }
        except FileNotFoundError:
            print("Vocab file not found!")
        return valide_tokens

    def functions_as_prompt(self):
        func_prompt = ""
        for function in self.functions_definition:
            func_prompt += f"- {function['name']}("
            i = 0
            for p_name, p_type in function["parameters"].items():
                if i != 0:
                    func_prompt += ", "
                func_prompt += f"{p_name}:{p_type}"
                i += 1
            func_prompt += f"): {function['description']} \n"
        return func_prompt
    
    def grep_prompt(self, prompt):
        general_prompt = ""
        example = '{"name": "<function_name>", "parameters": {"<param1>": <value1>, "<param2>": <value2>}}'
        general_prompt = f"""
You are a function calling assistant. Your task is to analyze a user request and respond with a single JSON object that calls the correct function with the correct arguments.
Available functions:
{self.functions_as_prompt()}
You must respond using exactly this JSON format and nothing else:
{example}
Do not include any explanation, extra text, or formatting outside the JSON object.

User request: {prompt["prompt"]}

Function call:

"""
        return general_prompt

    def main(self):
        self.checker()
        stages = ["name", "parameters"]
        function_names = [func["name"] for func in self.functions_definition]
        print(function_names)
        exit()
        valide_tokens = self.get_valid_token("name")
        for i in stages:
            pass
            # i need to restrict tokens based on the available function that i have


        

Engine1 = Engine()
Engine1.main()


#  valide_tokens_ids = self.get_valid_token(step)
#                         logits = self.llm.get_logits_from_input_ids(self.llm.encode(generated_prompt)[0].tolist())
#                         logits = np.array(logits)
#                         masked_logits = np.full_like(logits, float('-inf'))
#                         # i need to know in wish part i'm to restrict tokens
#                         for token in valide_tokens_ids:
#                                 masked_logits[token] = logits[token]
#                         next_token_id = int(np.argmax(masked_logits))