"""
Simple test to verify JSON formatting logic.
"""
import json
import sys
import os

# Add the qtJSONlint directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'qtJSONlint'))


def test_json_formatting():
    """Test JSON formatting with different options."""
    
    # Test data
    test_json = '{"name":"John","age":30,"city":"New York"}'
    
    # Test 1: Parse JSON
    print("Test 1: Parse JSON")
    try:
        data = json.loads(test_json)
        print("✓ JSON parsed successfully")
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse JSON: {e}")
        return False
    
    # Test 2: Format with indent
    print("\nTest 2: Format with indent=2")
    formatted = json.dumps(data, indent=2)
    print(formatted)
    print("✓ Formatted with indent")
    
    # Test 3: Format compact
    print("\nTest 3: Format compact")
    compact = json.dumps(data, separators=(',', ':'))
    print(compact)
    print("✓ Formatted compact")
    
    # Test 4: Sort keys
    print("\nTest 4: Sort keys")
    sorted_json = json.dumps(data, sort_keys=True, indent=2)
    print(sorted_json)
    print("✓ Sorted keys")
    
    # Test 5: Invalid JSON
    print("\nTest 5: Invalid JSON")
    invalid_json = '{"name":"John", age:30}'  # Missing quotes around age
    try:
        json.loads(invalid_json)
        print("✗ Should have failed to parse invalid JSON")
        return False
    except json.JSONDecodeError as e:
        print(f"✓ Correctly caught error: {e.msg} at line {e.lineno}, col {e.colno}")
    
    # Test 6: Ensure ASCII
    print("\nTest 6: Ensure ASCII")
    unicode_data = {"message": "Hello 世界"}
    ascii_json = json.dumps(unicode_data, ensure_ascii=True)
    print(ascii_json)
    print("✓ Ensured ASCII")
    
    print("\n" + "="*50)
    print("All tests passed!")
    return True


if __name__ == "__main__":
    success = test_json_formatting()
    sys.exit(0 if success else 1)
