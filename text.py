# test = "yassine"

# test = test[:2] + "\\" + test[2:]




# print(test)

def escape_detecter(output) -> str:
    valid_ecapes = ['"', "\\", "/"]
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

tests = [
    '"',            # 0 backslashes -> should escape
    '\\"',          # 1 backslash -> already escaped
    '\\\\"',        # 2 backslashes -> should escape
    '\\\\\\"',      # 3 backslashes -> already escaped
    '\\\\\\\\"',    # 4 backslashes -> should escape
    '\\\\\\\\\\"',  # 5 backslashes -> already escaped
]

for t in tests:
    print("-" * 40)
    print("Input :", repr(t))
    print("Output:", repr(escape_detecter(t)))

# print(escape_detecter("\\'"))