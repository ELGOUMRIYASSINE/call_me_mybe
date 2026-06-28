import json
import pytest

def test_constrained_decoding_result():
    with open('data/output/result.json') as f:
        result = json.load(f)
    
    expected_output = {}  # Replace with the expected output
    assert result == expected_output