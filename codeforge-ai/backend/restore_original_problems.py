#!/usr/bin/env python3
import json
import os

# Read the generate_problems.py to extract the original problems
print("Reading generate_problems.py...")
with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\generate_problems.py", 'r') as f:
    content = f.read()

# Extract the problems list from the Python file
# The file has a variable assignment: problems = [...]
import ast
try:
    # Parse the file as Python code
    tree = ast.parse(content)
    
    # Find the 'problems' assignment
    problems = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'problems':
                    # Evaluate the list
                    problems = ast.literal_eval(node.value)
                    break
    
    if problems is None:
        print("Could not find 'problems' variable in generate_problems.py")
    else:
        print(f"Found {len(problems)} original problems")
        
        # Save to a new JSON file
        output_path = r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\problems_original.json"
        with open(output_path, 'w') as f:
            json.dump(problems, f, indent=2)
        print(f"Saved original problems to: {output_path}")
        
        # Check slugs
        slugs = [p['slug'] for p in problems]
        print(f"Unique slugs: {len(set(slugs))}")
        
except Exception as e:
    print(f"Error: {e}")