"""Combine existing problems.json with newly generated problems."""
import json
import os

def combine_problems():
    # Load existing problems
    print("Loading existing problems...")
    with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\problems.json", 'r') as f:
        existing_problems = json.load(f)
    
    # Load newly generated problems
    print("Loading generated easy problems...")
    with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\easy_problems.json", 'r') as f:
        easy_problems = json.load(f)
    
    print("Loading generated medium problems...")
    with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\medium_problems.json", 'r') as f:
        medium_problems = json.load(f)
    
    print("Loading generated hard problems...")
    with open(r"C:\Users\Dell\OneDrive\Desktop\Projects\Fastapi\project - 2\codeforge-ai\backend\hard_problems.json", 'r') as f:
        hard_problems = json.load(f)
    
    # Add difficulty field to generated problems and fix missing fields
    print("Fixing generated problems...")
    
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
    combined_problems = existing_problems + easy_problems + medium_problems + hard_problems
    
    print(f"Total problems: {len(combined_problems)}")
    print(f"  Existing: {len(existing_problems)}")
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
    
    # Check sample problems
    print("\nSample new problems:")
    for i in range(min(3, len(easy_problems))):
        print(f"  Easy #{i+1}: {easy_problems[i]['title']}")
        print(f"    Test cases in description: {'Additional Test Cases' in easy_problems[i]['description']}")
    
    return True

if __name__ == "__main__":
    combine_problems()