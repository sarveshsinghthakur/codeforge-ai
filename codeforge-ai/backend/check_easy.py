import json

with open('easy_problems.json', 'r') as f:
    data = json.load(f)
    print(f'Generated {len(data)} easy problems')
    print('Sample problem:')
    print(f'Title: {data[0]["title"]}')
    print(f'Slug: {data[0]["slug"]}')
    print(f'Description length: {len(data[0]["description"])}')
    print(f'Has test cases: {"test_input" in data[0]}')
    if "test_input" in data[0]:
        print(f"Test input: {data[0]['test_input']}")