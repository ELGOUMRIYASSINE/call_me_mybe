# call_me_mybe

This project turns a natural-language prompt into a single function-call JSON object. It uses a local language model, but the application logic is responsible for constraining the output so the result matches the function schema instead of producing free-form text.

The repository is intentionally small:

- `src/__main__.py` contains the generation engine.
- `src/data_checker.py` validates input files and command-line arguments.
- `data/input/functions_definition.json` defines the available functions.
- `data/input/function_calling_tests.json` provides the prompts to solve.
- `data/output/result.json` is the generated output file.

## What the program does

For each prompt in the input file, the program asks the model to choose one function from the available schema and then builds the JSON call one token at a time. Instead of trusting the model to emit valid JSON on its own, the code restricts each generation step to a set of allowed tokens derived from:

- the available function names,
- the declared parameter types,
- and the vocabulary exposed by the model.

This is the core constrained-decoding idea of the project.

## Algorithm

The generation flow is:

1. Load the function definitions and prompts from JSON.
2. Validate that the input files exist and have the expected structure.
3. Load the local LLM specified by `--model` or by the default model.
4. Build a prompt that lists all available functions and forces a JSON-only answer.
5. Encode the function names and inspect the model vocabulary to compute allowed token sets.
6. Generate the output in a state machine:
	 - first choose the function name,
	 - then switch to the parameter object,
	 - then generate each parameter value according to its declared type (string, number, integer => only suported types),
	 - then close the JSON object.
7. Collect one result per prompt and write the final list to the output file.

The decoder does not sample freely. At each step it masks out invalid tokens and keeps only the tokens that can continue the expected JSON structure. The next token is selected greedily from that restricted set.

## Constrained decoding strategy

The project uses a practical form of constrained decoding rather than a full symbolic parser.

### Function-name constraint

The code tokenizes every function name from the schema and keeps only tokens that can continue one of those names. This makes the first generated field effectively choose the target function.

### Type constraint

Parameter values are generated with token filters based on the declared type:

- `string`: tokens that decode to printable characters,
- `number`: tokens that look like numeric text and punctuation used in numeric literals,
- `integer`: currently handled with the same token pool as `number`.

This is a heuristic, not a formal grammar. It works well enough for the current JSON fixtures, but it is still dependent on the model vocabulary and on the output shape expected by the code.

### JSON assembly

The JSON result is built incrementally as a string while the model generates tokens. The program also keeps a mirrored prompt string so the next model call can see the partial completion.

## Design decisions

### Keep the application logic separate from the model

The repository treats the model as a dependency, not as the source of truth. The app decides what is valid, what order fields appear in, and when the JSON object is complete.

### Use JSON fixtures as the interface

Function definitions and test prompts live in JSON files. That makes the project easy to run, easy to swap with new datasets, and easy to inspect without touching code.

### Validate early

`DataChecker` verifies that the input files exist and that the loaded objects match the expected schema before generation starts. This avoids failing halfway through decoding.

### Default paths with CLI overrides

The project has sensible defaults for the function definitions, prompts, output file, and model name, but each of them can be overridden from the command line.

### Greedy masked decoding

The implementation uses the highest-scoring token from the allowed set at each step. This keeps the control flow simple and deterministic, which is useful when the goal is schema compliance rather than creative text generation.

## Input format

### Function definitions

Each function entry must provide:

- a `name`,
- a short `description`,
- a `parameters` object where every parameter declares a type,
- and a `returns` object.

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

### Prompts

The input prompt file is a list of objects with a single `prompt` field:

```json
[
	{"prompt": "Add 4 and 7"}
]
```

## Output format

The program writes a JSON array to the output file. Each item contains the original prompt together with the generated function call.

Example shape:

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

## Running the project

The Makefile provides the main entrypoints:

- `make install` to install dependencies with `uv`.
- `make run` to execute the application.
- `make lint` to run style and type checks.

You can also override the data files or model at runtime:

```bash
uv run -m src --functions_definition data/input/functions_definition.json --input data/input/function_calling_tests.json --output data/output/result.json --model Qwen/Qwen3-0.6B
```

## Limitations

- The numeric and string token filters are heuristic.
- The code assumes the model vocabulary is accessible from the local SDK.
- The generation loop is tailored to the current JSON shape and function-call structure.
- Empty prompts are rejected.

## Project goal

The goal of the project is not to build a general-purpose agent. The goal is to show how a local LLM can be forced to emit structured function-call JSON through constrained decoding and lightweight schema validation.
