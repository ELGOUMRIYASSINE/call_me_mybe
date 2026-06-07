from llm_sdk import Small_LLM_Model
import json

model = Small_LLM_Model()

print(model.encode("yassine"))

with open(model.get_path_to_vocab_file(), "r") as f:
    vocab = json.load(f)

id_to_token = {v: k for k, v in vocab.items()}

# print(id_to_token)
logits = model.get_logits_from_input_ids(model.encode("sum of 2 + 3 + ")[0].tolist())
print(model.decode(logits.index(max(logits))))