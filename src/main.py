import json
import sys

sys.path.append("/goinfre/yelgoumr/call_me_mybe")
from llm_sdk import Small_LLM_Model as sdk
# from .data_checker import DataChecker
import numpy as np


llm = sdk()

# Dynamic function names
function_names = [
    "fn_add_number",
    "fn_subtract_number", 
    "fn_multiply_number",
    "fn_divide_number"
]

# Convert each function name to token IDs
function_token_sequences = {}
for func_name in function_names:
    # Use your encode method
    tokens = llm.encode(func_name)
    print(tokens)
    for token in tokens[0].tolist():
        print(llm.decode(token))
    exit()
    token_ids = tokens[0].tolist()  # Convert from tensor to list
    function_token_sequences[func_name] = token_ids
    
    print(f"{func_name} -> {token_ids}")
    print(f"  Decoded: {llm.decode(token_ids)}")


# # to analyze a user request and respond with a single JSON object that calls the correct function with the correct arguments.
# generated_prompt = """
# You are a function calling assistant. Your task is to give me all the functionwe have and i will give you the available functions
# here is available functions :
# 1: fn_add_numbers
# 2: fn_greet
# 3: fn_reverse_string
# 4: fn_get_square_root
# 5: fn_substitute_string_with_regex

# answer just giving me function in a line !

# answer:

# """
# result = ""
# tokens = {}
# while "fn_substitute_string_with_regex" not in result:
#     logits = llm.get_logits_from_input_ids(llm.encode(generated_prompt)[0].tolist())
#     output = llm.decode(np.argmax(logits))
#     print(output)
#     tokens[output] = int(np.argmax(logits))
#     result += output
#     generated_prompt += output

# print(result)
# print(tokens)
