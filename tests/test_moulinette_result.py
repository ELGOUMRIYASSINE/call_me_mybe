import json
import pytest

def load_result():
    with open('data/output/result.json') as f:
        return json.load(f)

def test_moulinette_result():
    expected_output = {"key": "value"}  # Replace with the actual expected output
    result = load_result()
    assert result == expected_output