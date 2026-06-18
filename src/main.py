# import json
# from pydantic import BaseModel 

# value = [  
#     {
#         "name": "fn_add_numbers",
#         "description": "Add two numbers together and return their sum.",
#         "parameters": {
#         "a": "k",
#         "b": "d"
#         },
#         "returns": {
#         "type": "number"
#         }
#     },
# ]

# class func_definition(BaseModel):
#     name: str
#     description: str
#     parameters: dict
#     returns: dict


# def test(value: list):
#     try:
#         validate = func_definition.model_validate(value[0])
#     except Exception as e:
#         print(e)
#     print("Valide")

# test(value)

try:
    int("abc")
except ValueError as e:
    raise TypeError("conversion failed")

