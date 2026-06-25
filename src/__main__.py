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


    def get_valid_tokens(self, step, result=None):
        function_names = [func["name"] for func in self.functions_definition]
        functions_tokens = []
        parameters_name_tokens = []
        for func_name in function_names:
            functions_tokens.extend(self.llm.encode(func_name)[0].tolist())
        string = "abcdefghijklmnopqrstuvwxyz"
        number = "0123456789."
        valide_tokens = None
        if step == "name":
            valide_tokens =  functions_tokens
        elif step == "parameters":
            func_name = ""
            for func in function_names:
                if func in result:
                    func_name = func
            func_obj = [obj for obj in self.functions_definition if obj["name"] == func_name][0]
            for name, type in func_obj["parameters"].items():
                if not f'"{name}":' in result:
                    if type["type"] == "number":
                        valide_tokens =  number
                    elif type["type"] == "string":
                        valide_tokens =  string
                    break
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
        print(self.llm.encode("abcdefghijklmnopqrstuvwxyz")[0].tolist())
        exit()
        self.checker()
        stages = ["name", "parameters"]
        tools = {
            "start": '{"name": "',
            "start_close": '",',
            "start_params": '"parameters": ',
            "param_start": '"',
            "param_close": "}"
        }
        function_names = [func["name"] for func in self.functions_definition]
        # for i in stages:
        state = "name"
        for prompt in self.prompts:
            general_prompt = self.grep_prompt(prompt) + tools["start"]
            valide_tokens = self.get_valid_tokens(state)
            tokens = self.llm.get_logits_from_input_ids(self.llm.encode(general_prompt)[0].tolist())
            tokens = np.array(tokens)
            print(tokens)
            exit()
            for func_name in function_names:
                if func_name in general_prompt:
                    pass  
                #    state = "parameters"
            print(general_prompt)
            exit()



        

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