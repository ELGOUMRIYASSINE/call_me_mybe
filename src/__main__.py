import json
import sys
from llm_sdk import Small_LLM_Model as sdk
from .data_checker import DataChecker
import numpy as np
import string

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

    def get_next_func_token(self, func_tokens, old_token=None):
        tokens = []
        for func in func_tokens:
            if not old_token and not func[0] in tokens :
                tokens.append(func[0])
            else:
                for i, token in enumerate(func):
                    if token == old_token and not len(func) < i + 2:
                        tokens.append(func[i + 1])
                        break
        return tokens

    def get_valid_tokens(self):
        function_names = [func["name"] for func in self.functions_definition]
        functions_tokens = []
        string_tokens = []
        number_tokens = []
        number = "0123456789.,}"
        for func_name in function_names:
            functions_tokens.append(self.llm.encode(func_name)[0].tolist())
        with open(self.llm.get_path_to_vocab_file(), "r") as vocab_data:
            dict_vocab = json.load(vocab_data)
            dict_vocab = {
                self.llm.decode([token_id,]): token_id
                for _,  token_id in dict_vocab.items()
            }
            for token, ids in dict_vocab.items():
                if token:
                    if all(c in string.printable for c in token):
                        string_tokens.append(ids)
                    if all(c in number for c in token):
                        number_tokens.append(ids)
        return {"name": functions_tokens, "number": number_tokens, "string": string_tokens, "integer": number_tokens,}

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
    
    def next_token_getter(self, logits, valid_tokens):
        masked_tokens = np.full_like(logits, float('-inf'))
        valid_tokens = list(dict.fromkeys(valid_tokens)) # remove duplicate
        for token in valid_tokens:
            masked_tokens[token] = logits[token]
        return self.llm.decode(int(np.argmax(masked_tokens)))
    def state_printer(self, text):
        indent = 0
        for chr in text:
            if chr == "{":
                sys.stdout.write("{\n")
                indent += 1
                sys.stdout.write("   " * indent)
            elif chr == "}":
                sys.stdout.write("\n")
                indent -= 1
                sys.stdout.write("   " * indent)
                sys.stdout.write("}")
            elif chr == ",":
                sys.stdout.write(",\n")
                sys.stdout.write("   " * indent)
            else:
                sys.stdout.write(chr)
    def main(self):
        self.checker()
        valid_data = self.get_valid_tokens()
        tools = {
            "start": '"name":"',
            "start_close": '",',
            "start_params": '"parameters":{',
            "param_middle": ',',
            "param_start": '"',
            "param_end": '"',
            "param_close": "}"
        }
        function_names = [func["name"] for func in self.functions_definition]
        valid_functions_tokens = valid_data["name"]
        i = 0
        results = []
        for prompt in self.prompts:
            state = "name"
            general_prompt = self.grep_prompt(prompt) + tools["start"]
            prmp =  prompt["prompt"].replace('"', '\\"')
            result = "{"+ f'"prompt": "{prmp}",' + tools["start"]
            self.state_printer(result)
            valide_tokens = self.get_next_func_token(valid_functions_tokens)
            tokens = self.llm.get_logits_from_input_ids(self.llm.encode(general_prompt)[0].tolist())
            output = self.next_token_getter(tokens, valide_tokens)
            general_prompt += output
            result += output
            self.state_printer(output)
            name_founded = False
            while "}}" not in result:
                for func_name in function_names:
                    if func_name in result and state == "name":
                        general_prompt += tools["start_close"]
                        result += tools["start_close"]
                        self.state_printer(tools["start_close"])
                        state = "parameters"
                        name_founded = True
                    if state == "parameters":
                        general_prompt += tools["start_params"]
                        result += tools["start_params"]
                        self.state_printer(tools["start_params"])                        
                        func_obj = [obj for obj in self.functions_definition if obj["name"] == func_name][0]
                        i = 0
                        value = ""
                        for para_name, para_type in func_obj["parameters"].items():
                            valid_tokens = valid_data[para_type["type"]]
                            output = ""
                            if i != 0:
                                result += ","
                                general_prompt += ","
                            if para_type["type"] == "string":
                                result += f'"{para_name}":"'
                                general_prompt += f'"{para_name}":"'
                            else:
                                result += f'"{para_name}":'
                                general_prompt += f'"{para_name}":'
                            scape_detecter = False
                            token_counter = 0
                            while not "," in output and not "}" in output and token_counter <= 50:
                                tokens = self.llm.get_logits_from_input_ids(self.llm.encode(general_prompt)[0].tolist())
                                output = self.next_token_getter(tokens, valid_tokens)
                                token_counter += 1
                                if not "," in output and not "}" in output:
                                    if '"' in output:
                                        result += "\\"
                                        general_prompt += "\\"
                                    if scape_detecter:
                                        if output != '"':
                                            general_prompt += "\\"
                                            result += "\\"
                                        scape_detecter = False
                                    if output == "\\":
                                        scape_detecter = True
                                    general_prompt += output
                                    result += output
                            if para_type["type"] == "string":
                                general_prompt += f'"'
                                result += f'"'
                            elif para_type["type"] == "number" and not "." in result:
                                result += ".0"
                                general_prompt += ".0"
                                value += '"'
                            i += 1
                        general_prompt += "}}"
                        result += "}}"
                        general_prompt += "\n"
                        break
                if not name_founded:
                    tokens = self.llm.get_logits_from_input_ids(self.llm.encode(general_prompt)[0].tolist())
                    valide_tokens = self.get_next_func_token(valid_functions_tokens, self.llm.encode(output)[0].tolist()[0])
                    output = self.next_token_getter(tokens, valide_tokens)
                    result += output
                    general_prompt += output
            self.state_printer(result)
            results.append(json.loads(result))            
            i += 1
        with open("data/output/result.json", "w") as file:
            json.dump(results, file, indent=4)

        

Engine1 = Engine()
Engine1.main()