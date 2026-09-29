#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from seed import extract_test_cases_from_description

# Test with a more complex description from the actual generated problems
with open('easy_problems.json', 'r') as f:
    import json
    easy_problems = json.load(f)

# Get the first problem
test_description = easy_problems[0]['description']

print("Testing with first generated problem:")
print(f"Description length: {len(test_description)}")
print(f"Contains Additional Test Cases: {'Additional Test Cases' in test_description}")

if 'Additional Test Cases:' in test_description:
    print("\nExtracted test cases:")
    test_cases = extract_test_cases_from_description(test_description)
    
    for i, tc in enumerate(test_cases[:5]):  # Show first 5
        print(f"  {i+1}. Input: {tc['input']}")
        print(f"     Output: {tc['output']}")
    
    if len(test_cases) > 5:
        print(f"  ...and {len(test_cases) - 5} more")
    
    print(f"\nTotal extracted: {len(test_cases)}")
else:
    print("No Additional Test Cases section found")