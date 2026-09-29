#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from seed import extract_test_cases_from_description

# Test the extraction function
sample_description = "Given two integers a and b, return their sum.\n\nAdditional Test Cases:\n\nInput: a = -500, b = -500\nOutput: -1000\nInput: a = 724, b = -321\nOutput: 403\nInput: a = -306, b = 988\nOutput: 682\n\n...and 87 more test cases"

test_cases = extract_test_cases_from_description(sample_description)

print("Extracted test cases:")
for i, tc in enumerate(test_cases):
    print(f"  {i+1}. Input: {tc['input']}")
    print(f"     Output: {tc['output']}")

print(f"\nTotal extracted: {len(test_cases)}")