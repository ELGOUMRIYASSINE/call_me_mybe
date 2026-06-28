import json
from pathlib import Path
from typing import List

from pydantic import BaseModel


class func_definition(BaseModel):
    """Describe one callable function from the input schema."""

    name: str
    description: str
    parameters: dict
    returns: dict


class inputFormat(BaseModel):
    """Describe one user prompt from the input file."""

    prompt: str


class DataChecker:
    """Load file paths and validate the JSON fixtures."""

    def __init__(self, args: List):
        self.args = args
        self.data_source = {}
        self.tools = ["--functions_definition", "--input", "--output"]
        self.defauls = {
            "--functions_definition": "data/input/functions_definition.json",
            "--input": "data/input/function_calling_tests.json",
            "--output": "data/output/result.json"
        }
        self.inputes_final = []
        self.func_def_final = []

    def check(self):
        if len(self.args) > 1:
            for tool in self.tools:
                if tool in self.args:
                    next_value = next(
                        (
                            self.args[index + 1]
                            for index, value in enumerate(self.args)
                            if value == tool
                        ),
                        None,
                    )
                    if next_value:
                        if Path(next_value).is_file():
                            self.data_source[tool.replace("-", "")] = next_value
                        else:
                            raise FileNotFoundError(
                                f"{next_value} this file does not existe"
                            )

        for tool in self.tools:
            if tool not in self.data_source:
                self.data_source[tool.replace("-", "")] = self.defauls[tool]
        return self.data_source

    def valid_json(self):
        if (
            not Path(self.data_source["functions_definition"]).is_file()
            or not Path(self.data_source["input"]).is_file()
        ):
            print(
                "[Error]: functions_definitions or function_calling_tests "
                "not provided"
            )
            exit()

        with open(self.data_source["functions_definition"], "r") as func_def, open(
            self.data_source["input"], "r"
        ) as inputs:
            try:
                self.func_def_final = json.load(func_def)
                self.inputes_final = json.load(inputs)
                for fun in self.func_def_final:
                    func_definition.model_validate(fun)
                for promp in self.inputes_final:
                    inputFormat.model_validate(promp)
            except Exception:
                print("conversion failed while validating json format")
