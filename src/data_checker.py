from typing import List
from pathlib import Path
import json

class DataChecker():
    def __init__(self, args: List):
        self.args = args
        self.data_source = {}
        self.tools = ["--functions_definition", "--input", "--output"]
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
        
