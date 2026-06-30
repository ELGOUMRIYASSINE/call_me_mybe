import json
from pathlib import Path
from typing import Any

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

    def __init__(self, args: list[str]) -> None:
        self.args = args
        self.data_source: dict[str, str] = {}
        self.tools: list[str] = ["--functions_definition", "--input", "--output"]
        self.defauls: dict[str, str] = {
            "--functions_definition": "data/input/functions_definition.json",
            "--input": "data/input/function_calling_tests.json",
            "--output": "data/output/result.json",
            "--model": ""
            
        }
        self.inputes_final: list[dict[str, Any]] = []
        self.func_def_final: list[dict[str, Any]] = []

    def check(self) -> dict[str, str]:
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
                        elif tool == "--output":
                            path = Path(next_value)
                            path.parent.mkdir(parents=True, exist_ok=True)
                        else:
                            print(f"{next_value} this file does not existe | or field to create")
                            raise SystemExit(1)

        for tool in self.tools:
            if tool.replace("-", "") not in self.data_source:
                self.data_source[tool.replace("-", "")] = self.defauls[tool]
        return self.data_source

    @staticmethod
    def escape_detecter(output) -> str:
        valid_ecapes = ['"', "\\"]
        if output == "\\":
            return output + "\\"
        i = 0
        while i < len(output):
            if i + 1 < len(output):
                next_index = output[i + 1]
            if output[i] == "\\":
                if not next_index in valid_ecapes and not output[i - 1] == "\\":
                    output = output[:i] + "\\" + output[i:]
                else:
                    i += 1
            elif output[i] == "\"":
                j = i - 1
                slashes_count = 0
                while j >= 0:
                    if output[j] == "\\":
                        slashes_count += 1
                    j -= 1
                if slashes_count % 2 == 0:
                    output = output[:i] + "\\" + output[i:]
            i += 1
        return output

                


    def valid_json(self) -> None:
        if (
            not Path(self.data_source["functions_definition"]).is_file()
            or not Path(self.data_source["input"]).is_file()
        ):
            print(
                "[Error]: functions_definitions or function_calling_tests "
                "not provided"
            )
            raise SystemExit(1)

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
