#!/usr/bin/env python3
import re

with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\add_solutions.py", 'r') as f:
    content = f.read()

keys = re.findall(r'"([^"]+)": \{', content)
print(f'Total solutions in updated file: {len(keys)}')
print('First 10:', keys[:10])
print('Last 10:', keys[-10:])