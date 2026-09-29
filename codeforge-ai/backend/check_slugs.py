#!/usr/bin/env python3
import json

# Load existing problems
print("Loading existing problems...")
with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\problems.json", 'r') as f:
    existing_problems = json.load(f)

print(f"Existing problems: {len(existing_problems)}")
print("Existing slugs:", [p['slug'] for p in existing_problems[:10]])

# Load easy problems
print("\nLoading easy problems...")
with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\easy_problems.json", 'r') as f:
    easy_problems = json.load(f)

print(f"Easy problems: {len(easy_problems)}")
print("Easy slugs:", [p['slug'] for p in easy_problems[:10]])

# Check for duplicates
print("\nChecking for duplicates...")
all_slugs = [p['slug'] for p in existing_problems] + [p['slug'] for p in easy_problems]
unique_slugs = set(all_slugs)
duplicate_slugs = [slug for slug in all_slugs if all_slugs.count(slug) > 1]

print(f"Total slugs: {len(all_slugs)}")
print(f"Unique slugs: {len(unique_slugs)}")
print(f"Duplicate slugs: {len(duplicate_slugs)}")

if duplicate_slugs:
    print("\nDuplicate slugs found:")
    for slug in duplicate_slugs[:10]:
        print(f"  {slug}")