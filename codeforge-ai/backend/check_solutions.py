#!/usr/bin/env python3
import re

with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\add_solutions.py", 'r') as f:
    content = f.read()

# Find all solution keys
keys = re.findall(r'"([^"]+)": \{', content)
print(f'Number of solutions in add_solutions.py: {len(keys)}')
print('Keys:', keys[:20])