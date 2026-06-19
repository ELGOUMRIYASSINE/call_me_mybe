from pydantic import BaseModel
from typing import List
from pathlib import Path
import json


class func_definition(BaseModel):
    name: str
    description: str
    parameters: dict
    returns: dict

class inputFormat(BaseModel):
    prompt: str

class DataChecker():
    def __init__(self, args: List):
        self.args = args
        self.data_source = {}
        self.tools = ["--functions_definition", "--input", "--output"]
        self.inputes_final = []
        self.func_def_final = []
        # self.opera
    def check(self):
        for tool in self.tools:
            if tool in self.args:
                next_value = next((self.args[i + 1] for i, x in enumerate(self.args) if x == tool), None)
                if next_value:
                    if Path(next_value).is_file() or "output" in next_value:
                        self.data_source[tool.replace("-", "")] = next_value
                    else:
                        raise FileNotFoundError(f"{next_value} this file does not existe")
        return self.data_source
    def valid_json(self):
        with open(self.data_source["functions_definition"], 'r') as funcDef, open(self.data_source["input"], 'r') as inputs:
            try:
                self.func_def_final = json.load(funcDef)
                self.inputes_final = json.load(inputs)
                for fun in self.func_def_final:
                    func_definition.model_validate(fun)
                for promp in self.inputes_final:
                    inputFormat.model_validate(promp)
            except Exception as e:
                print("conversion failed while validating json format")
