#!/usr/bin/env python3
import json
import os

# Load the original problems (73 from generate_problems.py)
with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\problems_original.json", 'r') as f:
    original_problems = json.load(f)

# Load the newly generated problems
with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\easy_problems.json", 'r') as f:
    easy_problems = json.load(f)

with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\medium_problems.json", 'r') as f:
    medium_problems = json.load(f)

with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\hard_problems.json", 'r') as f:
    hard_problems = json.load(f)

# Add difficulty field to generated problems
for problem in easy_problems:
    problem["difficulty"] = "easy"
    problem["hints"] = ["Try basic addition." if problem["slug"].startswith("sum-of-two-numbers") else 
                         "Try finding the maximum element." if problem["slug"].startswith("find-maximum") else 
                         "Count elements that are even."]

for problem in medium_problems:
    problem["difficulty"] = "medium"
    problem["hints"] = ["Try using a hash table." if problem["slug"].startswith("group-anagrams") else 
                         "Count frequencies and use a heap." if problem["slug"].startswith("top-k-frequent") else 
                         "Use prefix and suffix products."]

for problem in hard_problems:
    problem["difficulty"] = "hard"
    problem["hints"] = ["Sort arrays and use binary search." if problem["slug"].startswith("median-of-two-sorted") else 
                         "Use two pointers technique." if problem["slug"].startswith("interval-list-intersections") else 
                         "Use min heap to track rooms."]

# Combine all problems
combined_problems = original_problems + easy_problems + medium_problems + hard_problems

print(f"Total problems: {len(combined_problems)}")
print(f"  Original: {len(original_problems)}")
print(f"  Easy: {len(easy_problems)}")
print(f"  Medium: {len(medium_problems)}")
print(f"  Hard: {len(hard_problems)}")

# Save combined problems
output_path = r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\problems.json"
with open(output_path, "w") as f:
    json.dump(combined_problems, f, indent=2)

print(f"Saved combined problems to: {output_path}")

# Verify the combination
print("\nVerifying the combination...")

# Count by difficulty
difficulties = {}
for p in combined_problems:
    diff = p.get("difficulty", "unknown")
    difficulties[diff] = difficulties.get(diff, 0) + 1

print("Problems by difficulty:")
for diff, count in sorted(difficulties.items()):
    print(f"  {diff}: {count}")

# Check slugs
slugs = [p['slug'] for p in combined_problems]
unique_slugs = set(slugs)
print(f"\nTotal slugs: {len(slugs)}")
print(f"Unique slugs: {len(unique_slugs)}")
print(f"Duplicates: {len(slugs) - len(unique_slugs)}")