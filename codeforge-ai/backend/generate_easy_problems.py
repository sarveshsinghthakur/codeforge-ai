"""Generate 100 easy coding problems with ~100 test cases each."""
import json
import random
import os
from typing import List, Dict

# Problem templates for easy difficulty
EASY_PROBLEM_TEMPLATES = [
    {
        "title": "Sum of Two Numbers",
        "slug": "sum-of-two-numbers",
        "description": "Given two integers a and b, return their sum.",
        "topics": ["math"],
        "constraints": ["-1000 <= a, b <= 1000"],
        "starter_code": {
            "python": "class Solution:\n    def sumOfTwo(self, a: int, b: int) -> int:\n        pass",
            "javascript": "var sumOfTwo = function(a, b) {\n    \n};",
            "java": "class Solution {\n    public int sumOfTwo(int a, int b) {\n        \n    }\n}"
        },
        "complexity_time": "O(1)",
        "complexity_space": "O(1)"
    },
    {
        "title": "Find Maximum in Array",
        "slug": "find-maximum-in-array",
        "description": "Given an array of integers, find and return the maximum value.",
        "topics": ["array"],
        "constraints": ["1 <= nums.length <= 1000", "-10000 <= nums[i] <= 10000"],
        "starter_code": {
            "python": "class Solution:\n    def findMax(self, nums: List[int]) -> int:\n        pass",
            "javascript": "var findMax = function(nums) {\n    \n};",
            "java": "class Solution {\n    public int findMax(int[] nums) {\n        \n    }\n}"
        },
        "complexity_time": "O(n)",
        "complexity_space": "O(1)"
    },
    {
        "title": "Count Even Numbers",
        "slug": "count-even-numbers",
        "description": "Given an array of integers, count how many of them are even numbers.",
        "topics": ["array", "math"],
        "constraints": ["1 <= nums.length <= 1000", "-10000 <= nums[i] <= 10000"],
        "starter_code": {
            "python": "class Solution:\n    def countEvens(self, nums: List[int]) -> int:\n        pass",
            "javascript": "var countEvens = function(nums) {\n    \n};",
            "java": "class Solution {\n    public int countEvens(int[] nums) {\n        \n    }\n}"
        },
        "complexity_time": "O(n)",
        "complexity_space": "O(1)"
    }
]

def generate_test_cases(problem_slug: str) -> List[Dict]:
    """Generate ~100 test cases for a given problem."""
    test_cases = []
    
    if problem_slug == "sum-of-two-numbers":
        # Edge cases
        test_cases.extend([
            {"input": "a = 0, b = 0", "output": "0"},
            {"input": "a = -1000, b = 1000", "output": "0"},
            {"input": "a = 999, b = 1", "output": "1000"},
            {"input": "a = -500, b = -500", "output": "-1000"}
        ])
        # Random cases
        for _ in range(96):
            a = random.randint(-1000, 1000)
            b = random.randint(-1000, 1000)
            test_cases.append({
                "input": f"a = {a}, b = {b}", 
                "output": str(a + b)
            })
    
    elif problem_slug == "find-maximum-in-array":
        # Edge cases
        test_cases.extend([
            {"input": "nums = [1]", "output": "1"},
            {"input": "nums = [-10000, -9999, -1]", "output": "-1"},
            {"input": "nums = [10000, 9999, 1]", "output": "10000"}
        ])
        # Random cases
        for _ in range(97):
            nums = [random.randint(-10000, 10000) for _ in range(random.randint(1, 1000))]
            test_cases.append({
                "input": f"nums = {nums}", 
                "output": str(max(nums))
            })
    
    elif problem_slug == "count-even-numbers":
        # Edge cases
        test_cases.extend([
            {"input": "nums = [0]", "output": "1"},
            {"input": "nums = [1, 3, 5]", "output": "0"},
            {"input": "nums = [2, 4, 6]", "output": "3"}
        ])
        # Random cases
        for _ in range(97):
            nums = [random.randint(-10000, 10000) for _ in range(random.randint(1, 1000))]
            count = sum(1 for num in nums if num % 2 == 0)
            test_cases.append({
                "input": f"nums = {nums}", 
                "output": str(count)
            })
    
    return test_cases

def generate_easy_problems() -> List[Dict]:
    """Generate 100 easy problems with comprehensive test cases."""
    problems = []
    
    # Generate problems from templates
    for i in range(100):
        template = random.choice(EASY_PROBLEM_TEMPLATES)
        problem = template.copy()
        
        # Make each problem unique
        problem["title"] = f"{template['title']} {i+1}"
        problem["slug"] = f"{template['slug']}-{i+1}"
        
        # Generate test cases
        test_cases = generate_test_cases(template["slug"])
        problem["examples"] = test_cases[:3]  # First 3 as examples
        
        # Add remaining test cases to description
        remaining_cases = test_cases[3:]
        if remaining_cases:
            problem["description"] += "\n\nAdditional Test Cases:\n"
            for case in remaining_cases[:10]:  # Show first 10 in description
                problem["description"] += f"\nInput: {case['input']}\nOutput: {case['output']}"
            if len(remaining_cases) > 10:
                problem["description"] += f"\n\n...and {len(remaining_cases)-10} more test cases"
        
        # Set test input/output for the seed script
        problem["test_input"] = test_cases[0]["input"]
        problem["test_output"] = test_cases[0]["output"]
        
        problems.append(problem)
    
    return problems

if __name__ == "__main__":
    easy_problems = generate_easy_problems()
    output_path = os.path.join(os.path.dirname(__file__), "easy_problems.json")
    with open(output_path, "w") as f:
        json.dump(easy_problems, f, indent=2)
    print(f"Generated {len(easy_problems)} easy problems with comprehensive test cases.")
    print(f"Saved to: {output_path}")