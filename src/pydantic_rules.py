from typing import Literal

from pydantic import BaseModel


class ParameterSpec(BaseModel):
    """Type for one parameter description in function definitions."""

    type: Literal["string", "number", "integer"]


class FunctionDefinition(BaseModel):
    """Type for one function definition item loaded from JSON."""

    name: str
    description: str
    parameters: dict[str, ParameterSpec]


class PromptItem(BaseModel):
    """Type for one prompt item loaded from JSON."""

    prompt: str


class ValidTokenData(BaseModel):
    """Collections of allowed tokens by decoding state."""

    name: list[list[int]]
    number: list[int]
    string: list[int]
    integer: list[int]


class func_definition(BaseModel):
    """Describe one callable function from the input schema."""

    name: str
    description: str
    parameters: dict
    returns: dict


class inputFormat(BaseModel):
    """Describe one user prompt from the input file."""

    prompt: str
