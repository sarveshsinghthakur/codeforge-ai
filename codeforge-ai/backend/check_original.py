#!/usr/bin/env python3
import json

# Load problems
with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\problems.json", 'r') as f:
    data = json.load(f)

print(f"Total problems: {len(data)}")
difficulties = {}
for p in data:
    diff = p.get("difficulty", "unknown")
    difficulties[diff] = difficulties.get(diff, 0) + 1

print("Problems by difficulty:")
for diff, count in sorted(difficulties.items()):
    print(f"  {diff}: {count}")

# Check slugs
slugs = [p['slug'] for p in data]
unique_slugs = set(slugs)
print(f"\nTotal slugs: {len(slugs)}")
print(f"Unique slugs: {len(unique_slugs)}")
print(f"Duplicates: {len(slugs) - len(unique_slugs)}")

# Show duplicates
from collections import Counter
slug_counts = Counter(slugs)
duplicates = [slug for slug, count in slug_counts.items() if count > 1]
print(f"Duplicate slugs: {len(duplicates)}")
if duplicates:
    print("Sample duplicates:", duplicates[:5])