import os

def tester_agent(project_path, api_url, model, api_provider="openai", token=None):
    """Create test files - FIXED SIGNATURE"""
    test_files = []
    
    # Create test_main.py
    test_main_path = os.path.join(project_path, "test_main.py")
    with open(test_main_path, "w") as f:
        f.write('''#!/usr/bin/env python3
"""
Tests for main module
"""

import pytest
from main import main

def test_main_output(capsys):
    """Test main function output"""
    main()
    captured = capsys.readouterr()
    assert "Hello" in captured.out
    assert "AI Dev IDE" in captured.out

def test_main_function():
    """Test main function exists"""
    assert callable(main)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
''')
    test_files.append("test_main.py")
    
    # Create test_utils.py
    test_utils_path = os.path.join(project_path, "test_utils.py")
    with open(test_utils_path, "w") as f:
        f.write('''#!/usr/bin/env python3
"""
Tests for utils module
"""

import pytest
from utils import format_text, calculate_average

def test_format_text():
    """Test text formatting"""
    assert format_text("  hello world  ") == "Hello World"
    assert format_text("python") == "Python"
    assert format_text("") == ""

def test_calculate_average():
    """Test average calculation"""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20, 30]) == 20.0
    assert calculate_average([]) == 0
    assert calculate_average([5]) == 5.0

def test_calculate_average_negative():
    """Test average with negative numbers"""
    assert calculate_average([-1, 0, 1]) == 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
''')
    test_files.append("test_utils.py")
    
    return test_files