#!/usr/bin/env python3
import json

# Read the first few easy problems
with open('easy_problems.json', 'r') as f:
    easy_problems = json.load(f)

# Check the first problem
first_problem = easy_problems[0]
print("First problem structure:")
print(f"Slug: {first_problem['slug']}")
print(f"Description contains 'Input:' {first_problem['description'].count('Input:')}")
print(f"Description contains 'Output:' {first_problem['description'].count('Output:')}")

# Show the first 500 characters of description
print("\nFirst 500 characters of description:")
print(first_problem['description'][:500])

print("\nExamples:")
for i, ex in enumerate(first_problem['examples'][:2]):
    print(f"  Example {i+1}: Input={ex['input']}, Output={ex['output']}")