# call_me_mybe

## How to run

From the repository root:

1. Install dependencies:

```bash
uv sync
```

2. Run the project:

```bash
uv run -m src
```

Optional Makefile shortcuts:

- `make install` -> runs `uv sync`
- `make run` -> runs `uv run -m src`

## Where to put prompts and function definitions

Use the `data` folder files below:

- `data/input/function_calling_tests.json`
	- Put your prompts here.
	- Expected shape: a JSON list of objects with a `prompt` field.

- `data/input/functions_definition.json`
	- Put your function definitions here.
	- Each function should include `name`, `description`, `parameters`, and `returns`.

- `data/output/result.json`
	- Generated results are written here when you run the project.

This project converts natural-language prompts into structured function-call JSON using constrained decoding. Instead of trusting the model to freely emit valid JSON, the code limits generation to token sets that match function names and parameter types.

## Current repository structure

```text
.
├── makefile
├── pyproject.toml
├── llm_sdk/
│   └── __init__.py
├── src/
│   ├── __main__.py
│   ├── data_checker.py
│   ├── constrained_tools.py
│   └── pydantic_rules.py
└── data/
		├── input/
		│   ├── functions_definition.json
		│   └── function_calling_tests.json
		└── output/
				└── result.json
```

## Module responsibilities

- `src/__main__.py`
	- Orchestrates loading, prompt construction, constrained token generation, and writing output.
- `src/data_checker.py`
	- Parses CLI flags, applies default paths, validates JSON files, and checks schema compatibility.
- `src/constrained_tools.py`
	- Builds valid token pools and applies greedy masked decoding helpers.
- `src/pydantic_rules.py`
	- Defines Pydantic models for function definitions, prompt items, and parameter type constraints.
- `llm_sdk/__init__.py`
	- Provides `Small_LLM_Model`, a Hugging Face based wrapper used by the app.

## What the program does

For each prompt from `data/input/function_calling_tests.json`, the engine:

1. Loads function definitions from `data/input/functions_definition.json`.
2. Validates both input files against expected schema.
3. Loads the configured local model (`Qwen/Qwen3-0.6B` by default).
4. Builds a strict instruction prompt that asks for one JSON function call.
5. Computes allowed token sets for:
	 - function names,
	 - string values,
	 - number/integer values.
6. Generates tokens greedily while masking all tokens outside the currently valid set.
7. Writes all generated results to `data/output/result.json`.

## Constrained decoding overview

- Function selection is constrained using tokenized function names from the schema.
- Parameter values are constrained by declared type:
	- `string` -> printable tokens,
	- `number` -> numeric-like tokens,
	- `integer` -> currently reuses number token pool.
- Output JSON is assembled incrementally and finalized per prompt.

This approach is heuristic, lightweight, and designed for this project's fixed function-call output format.

## Algorithm walkthrough

The generation loop behaves like a small state machine with two phases:

1. Function name phase
	- Start building output with `{` + `"prompt"` + `"name":"`.
	- Build valid first tokens from all allowed function names.
	- Select the next token greedily, but only from the currently allowed set.
	- Keep extending the function name token by token until one full function name is recognized.

2. Parameters phase
	- Append `"parameters":{`.
	- Resolve the selected function schema and iterate through its parameters in order.
	- For each parameter:
	  - Choose the token pool from type (`string`, `number`, `integer`).
	  - Generate value tokens greedily from that restricted pool.
	  - Stop parameter generation on `,` or `}` boundary tokens (or after a token cap).
	  - Escape string content when needed so JSON stays parseable.
	- Close JSON object with `}}` and parse it into a Python dictionary.

At each decoding step, logits are masked so every disallowed token gets `-inf`, then argmax picks the highest remaining token. This means output quality depends on both model probabilities and how good the allowed token pools are.

## Input format

### Function definitions

Each function object is expected to include:

- `name`: string
- `description`: string
- `parameters`: object where each parameter has a supported `type`
- `returns`: object (used by validation schema)

Example:

```json
{
	"name": "fn_add_numbers",
	"description": "Add two numbers together and return their sum.",
	"parameters": {
		"a": {"type": "number"},
		"b": {"type": "number"}
	},
	"returns": {"type": "number"}
}
```

Supported parameter types in current code:

- `string`
- `number`
- `integer`

### Prompt input

The prompt file must be a list of objects with a `prompt` field:

```json
[
	{"prompt": "Add 4 and 7"}
]
```

## Output format

The output file is a JSON array. Each item contains:

- `prompt`
- `name` (selected function)
- `parameters` (generated arguments)

Example:

```json
[
	{
		"prompt": "Add 4 and 7",
		"name": "fn_add_numbers",
		"parameters": {
			"a": 4,
			"b": 7
		}
	}
]
```

## Run and development commands

From the repository root:

- `make install` -> install dependencies using `uv sync`
- `make run` -> run the app with default files (`uv run -m src`)
- `make lint` -> run `flake8` and `mypy`
- `make lint-strict` -> run strict mypy checks
- `make clean` -> remove Python cache artifacts

Run with explicit overrides:

```bash
uv run -m src \
	--functions_definition data/input/functions_definition.json \
	--input data/input/function_calling_tests.json \
	--output data/output/result.json \
	--model Qwen/Qwen3-0.6B
```

## Notes and limitations

- Type-based token filtering is heuristic, not grammar-complete.
- Integer generation currently shares the number token pool.
- The current decoding loop targets one specific JSON function-call shape.
- Empty prompts are skipped.

## Design decisions

- Greedy decoding with token masking
	- Chosen for simplicity and deterministic output under constraints.
	- Easier to debug than beam search or sampling in this project scope.

- Type-driven token pools instead of full JSON grammar
	- Kept implementation lightweight and fast to iterate.
	- Accepts weaker guarantees in exchange for lower complexity.

- Pydantic validation before model execution
	- Fails early on malformed inputs and keeps runtime logic cleaner.
	- Prevents decoding from running on invalid schemas.

- Single-call output contract
	- The prompt and parser are optimized for exactly one function call per input prompt.
	- Reduces ambiguity and keeps output formatting predictable.

## Challenges and trade-offs

- Token-level constraints are approximate
	- Character-based pools (`string.printable`, numeric chars) are heuristic and not a full parser.

- Integer vs number precision
	- `integer` currently reuses number tokens, so strict integer-only enforcement is limited.

- Boundary detection during parameter generation
	- Stopping on `,` / `}` is practical but can be fragile for unusual tokenization patterns.

- Tight coupling to one JSON shape
	- Current state machine is specialized for `{name, parameters}` and is not yet a general constrained JSON engine.
