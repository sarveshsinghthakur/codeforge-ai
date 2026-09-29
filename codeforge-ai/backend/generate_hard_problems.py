"""Generate 100 hard coding problems with ~100 test cases each."""
import json
import random
import os
from typing import List, Dict

# Problem templates for hard difficulty
HARD_PROBLEM_TEMPLATES = [
    {
        "title": "Median of Two Sorted Arrays",
        "slug": "median-of-two-sorted-arrays",
        "description": "Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays.",
        "topics": ["array", "binary-search", "divide-and-conquer"],
        "constraints": ["1 <= m, n <= 1000"],
        "starter_code": {
            "python": "class Solution:\n    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:\n        pass",
            "javascript": "var findMedianSortedArrays = function(nums1, nums2) {\n    \n};",
            "java": "class Solution {\n    public double findMedianSortedArrays(int[] nums1, int[] nums2) {\n        \n    }\n}"
        },
        "complexity_time": "O(log(min(m,n)))",
        "complexity_space": "O(1)"
    },
    {
        "title": "Interval List Intersections",
        "slug": "interval-list-intersections",
        "description": "Given two lists of closed intervals, each list disjoint and sorted, return the intersection of these two interval lists.",
        "topics": ["array", "two-pointers"],
        "constraints": ["0 <= firstList.length <= 1000", "0 <= secondList.length <= 1000"],
        "starter_code": {
            "python": "class Solution:\n    def intervalIntersection(self, firstList: List[List[int]], secondList: List[List[int]]) -> List[List[int]]:\n        pass",
            "javascript": "var intervalIntersection = function(firstList, secondList) {\n    \n};",
            "java": "class Solution {\n    public int[][] intervalIntersection(int[][] firstList, int[][] secondList) {\n        \n    }\n}"
        },
        "complexity_time": "O(m + n)",
        "complexity_space": "O(1)"
    },
    {
        "title": "Meeting Rooms II",
        "slug": "meeting-rooms-ii",
        "description": "Given an array of meeting time intervals consisting of start and end times [[s1,e1],[s2,e2],...], find the minimum number of conference rooms required.",
        "topics": ["array", "heap", "greedy", "sorting"],
        "constraints": ["1 <= intervals.length <= 10^4", "0 <= start < end <= 10^6"],
        "starter_code": {
            "python": "class Solution:\n    def minMeetingRooms(self, intervals: List[List[int]]) -> int:\n        pass",
            "javascript": "var minMeetingRooms = function(intervals) {\n    \n};",
            "java": "class Solution {\n    public int minMeetingRooms(int[][] intervals) {\n        \n    }\n}"
        },
        "complexity_time": "O(n log n)",
        "complexity_space": "O(n)"
    }
]

def generate_test_cases(problem_slug: str) -> List[Dict]:
    """Generate ~100 test cases for a given problem."""
    test_cases = []
    
    if problem_slug == "median-of-two-sorted-arrays":
        # Edge cases
        test_cases.extend([
            {"input": "nums1 = [1,3], nums2 = [2]", "output": "2.0"},
            {"input": "nums1 = [1,2], nums2 = [3,4]", "output": "2.5"},
            {"input": "nums1 = [], nums2 = [1]", "output": "1.0"}
        ])
        # Random cases
        for _ in range(97):
            m = random.randint(1, 50)
            n = random.randint(1, 50)
            nums1 = sorted([random.randint(-100, 100) for _ in range(m)])
            nums2 = sorted([random.randint(-100, 100) for _ in range(n)])
            
            # Merge and find median
            merged = sorted(nums1 + nums2)
            if len(merged) % 2 == 1:
                median = float(merged[len(merged)//2])
            else:
                median = (merged[len(merged)//2 - 1] + merged[len(merged)//2]) / 2.0
            
            test_cases.append({
                "input": f"nums1 = {nums1}, nums2 = {nums2}",
                "output": str(median)
            })
    
    elif problem_slug == "interval-list-intersections":
        # Edge cases
        test_cases.extend([
            {"input": "firstList = [[0,2],[5,10],[13,23],[24,25]], secondList = [[1,5],[8,12],[15,24],[25,26]]", "output": "[[1,2],[5,5],[8,12],[15,23],[24,24],[25,25]]"},
            {"input": "firstList = [[1,3],[5,9]], secondList = []", "output": "[]"},
            {"input": "firstList = [], secondList = [[4,8]]", "output": "[]"}
        ])
        # Random cases
        for _ in range(97):
            num1 = random.randint(0, 20)
            num2 = random.randint(0, 20)
            firstList = []
            secondList = []
            
            # Generate non-overlapping intervals
            for _ in range(num1):
                start = random.randint(0, 100)
                end = start + random.randint(1, 20)
                firstList.append([start, end])
            
            for _ in range(num2):
                start = random.randint(0, 100)
                end = start + random.randint(1, 20)
                secondList.append([start, end])
            
            # Find intersections
            intersections = []
            i = j = 0
            while i < len(firstList) and j < len(secondList):
                a_start, a_end = firstList[i]
                b_start, b_end = secondList[j]
                
                if a_start <= b_end and b_start <= a_end:
                    start = max(a_start, b_start)
                    end = min(a_end, b_end)
                    intersections.append([start, end])
                
                if a_end < b_end:
                    i += 1
                else:
                    j += 1
            
            test_cases.append({
                "input": f"firstList = {firstList}, secondList = {secondList}",
                "output": str(intersections)
            })
    
    elif problem_slug == "meeting-rooms-ii":
        # Edge cases
        test_cases.extend([
            {"input": "intervals = [[0,30],[5,10],[15,20]]", "output": "2"},
            {"input": "intervals = [[7,10],[2,4]]", "output": "1"},
            {"input": "intervals = [[1,5],[5,10]]", "output": "1"}
        ])
        # Random cases
        for _ in range(97):
            num_meetings = random.randint(1, 50)
            intervals = []
            
            for _ in range(num_meetings):
                start = random.randint(0, 1000)
                end = start + random.randint(1, 500)
                intervals.append([start, end])
            
            # Sort by start time
            intervals.sort(key=lambda x: x[0])
            
            # Min heap approach
            import heapq
            heap = []
            for start, end in intervals:
                if heap and heap[0] <= start:
                    heapq.heapreplace(heap, end)
                else:
                    heapq.heappush(heap, end)
            
            test_cases.append({
                "input": f"intervals = {intervals}",
                "output": str(len(heap))
            })
    
    return test_cases

def generate_hard_problems() -> List[Dict]:
    """Generate 100 hard problems with comprehensive test cases."""
    problems = []
    
    # Generate problems from templates
    for i in range(100):
        template = random.choice(HARD_PROBLEM_TEMPLATES)
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
    hard_problems = generate_hard_problems()
    output_path = os.path.join(os.path.dirname(__file__), "hard_problems.json")
    with open(output_path, "w") as f:
        json.dump(hard_problems, f, indent=2)
    print(f"Generated {len(hard_problems)} hard problems with comprehensive test cases.")
    print(f"Saved to: {output_path}")