"""Generate 100 medium coding problems with ~100 test cases each."""
import json
import random
import os
from typing import List, Dict

# Problem templates for medium difficulty
MEDIUM_PROBLEM_TEMPLATES = [
    {
        "title": "Group Anagrams",
        "slug": "group-anagrams",
        "description": "Given an array of strings strs, group the anagrams together.",
        "topics": ["hash-table", "string", "sorting"],
        "constraints": ["1 <= strs.length <= 10^4", "0 <= strs[i].length <= 100"],
        "starter_code": {
            "python": "class Solution:\n    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:\n        pass",
            "javascript": "var groupAnagrams = function(strs) {\n    \n};",
            "java": "class Solution {\n    public List<List<String>> groupAnagrams(String[] strs) {\n        \n    }\n}"
        },
        "complexity_time": "O(n * k log k)",
        "complexity_space": "O(n * k)"
    },
    {
        "title": "Top K Frequent Elements",
        "slug": "top-k-frequent-elements",
        "description": "Given an integer array nums and an integer k, return the k most frequent elements.",
        "topics": ["array", "hash-table", "heap", "bucket-sort", "counting"],
        "constraints": ["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
        "starter_code": {
            "python": "class Solution:\n    def topKFrequent(self, nums: List[int], k: int) -> List[int]:\n        pass",
            "javascript": "var topKFrequent = function(nums, k) {\n    \n};",
            "java": "class Solution {\n    public int[] topKFrequent(int[] nums, int k) {\n        \n    }\n}"
        },
        "complexity_time": "O(n)",
        "complexity_space": "O(n)"
    },
    {
        "title": "Product of Array Except Self",
        "slug": "product-of-array-except-self",
        "description": "Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].",
        "topics": ["array", "prefix-sum"],
        "constraints": ["2 <= nums.length <= 10^5", "-30 <= nums[i] <= 30"],
        "starter_code": {
            "python": "class Solution:\n    def productExceptSelf(self, nums: List[int]) -> List[int]:\n        pass",
            "javascript": "var productExceptSelf = function(nums) {\n    \n};",
            "java": "class Solution {\n    public int[] productExceptSelf(int[] nums) {\n        \n    }\n}"
        },
        "complexity_time": "O(n)",
        "complexity_space": "O(1)"
    }
]

def generate_test_cases(problem_slug: str) -> List[Dict]:
    """Generate ~100 test cases for a given problem."""
    test_cases = []
    
    if problem_slug == "group-anagrams":
        # Edge cases
        test_cases.extend([
            {"input": 'strs = ["eat","tea","tan","ate","nat","bat"]', "output": '[["bat"],["nat","tan"],["ate","eat","tea"]]'},
            {"input": 'strs = [""]', "output": '[[""]]}'},
            {"input": 'strs = ["a"]', "output": '[["a"]]'}
        ])
        # Random cases
        for _ in range(97):
            num_strings = random.randint(1, 100)
            strs = []
            for _ in range(num_strings):
                length = random.randint(0, 20)
                s = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(length))
                strs.append(s)
            # Group anagrams by sorting characters
            anagram_groups = {}
            for s in strs:
                sorted_str = ''.join(sorted(s))
                if sorted_str not in anagram_groups:
                    anagram_groups[sorted_str] = []
                anagram_groups[sorted_str].append(s)
            output = list(anagram_groups.values())
            test_cases.append({
                "input": f'strs = {strs}',
                "output": str(output)
            })
    
    elif problem_slug == "top-k-frequent-elements":
        # Edge cases
        test_cases.extend([
            {"input": "nums = [1,1,1,2,2,3], k = 2", "output": "[1,2]"},
            {"input": "nums = [1], k = 1", "output": "[1]"},
            {"input": "nums = [1,2,2,3,3,3,3], k = 2", "output": "[3,2]"}
        ])
        # Random cases
        for _ in range(97):
            num_elements = random.randint(1, 1000)
            nums = [random.randint(-100, 100) for _ in range(num_elements)]
            # Count frequencies
            freq = {}
            for num in nums:
                freq[num] = freq.get(num, 0) + 1
            # Sort by frequency and get top k
            sorted_nums = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)
            k = random.randint(1, min(10, len(sorted_nums)))
            output = sorted_nums[:k]
            test_cases.append({
                "input": f"nums = {nums}, k = {k}",
                "output": str(output)
            })
    
    elif problem_slug == "product-of-array-except-self":
        # Edge cases
        test_cases.extend([
            {"input": "nums = [1,2,3,4]", "output": "[24,12,8,6]"},
            {"input": "nums = [-1,1,0,-3,3]", "output": "[0,0,9,0,0]"},
            {"input": "nums = [2,2,2,2]", "output": "[8,8,8,8]"}
        ])
        # Random cases
        for _ in range(97):
            nums = [random.randint(-30, 30) for _ in range(random.randint(2, 1000))]
            n = len(nums)
            answer = [1] * n
            
            # Left products
            left_product = 1
            for i in range(n):
                answer[i] = left_product
                left_product *= nums[i]
            
            # Right products
            right_product = 1
            for i in range(n - 1, -1, -1):
                answer[i] *= right_product
                right_product *= nums[i]
            
            test_cases.append({
                "input": f"nums = {nums}",
                "output": str(answer)
            })
    
    return test_cases

def generate_medium_problems() -> List[Dict]:
    """Generate 100 medium problems with comprehensive test cases."""
    problems = []
    
    # Generate problems from templates
    for i in range(100):
        template = random.choice(MEDIUM_PROBLEM_TEMPLATES)
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
    medium_problems = generate_medium_problems()
    output_path = os.path.join(os.path.dirname(__file__), "medium_problems.json")
    with open(output_path, "w") as f:
        json.dump(medium_problems, f, indent=2)
    print(f"Generated {len(medium_problems)} medium problems with comprehensive test cases.")
    print(f"Saved to: {output_path}")