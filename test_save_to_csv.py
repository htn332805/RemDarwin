#!/usr/bin/env python3
"""
Test script for save_to_csv function in fmp_fetcher.py
"""

import os
import csv
import shutil
from fmp_fetcher import save_to_csv

def test_list_of_dicts():
    """Test saving a list of dicts"""
    data = [
        {'name': 'Alice', 'age': 30, 'city': 'NYC'},
        {'name': 'Bob', 'age': 25, 'city': 'LA'}
    ]
    save_to_csv(data, 'test_list', 'test_output')
    # Verify file exists and content
    file_path = os.path.join('test_output', 'test_list.csv')
    assert os.path.exists(file_path), "CSV file not created for list of dicts"
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['name'] == 'Alice'
        assert rows[1]['name'] == 'Bob'
    print("✓ Test list of dicts passed")

def test_single_dict():
    """Test saving a single dict"""
    data = {'name': 'Charlie', 'age': 35, 'city': 'Chicago'}
    save_to_csv(data, 'test_single', 'test_output')
    # Verify
    file_path = os.path.join('test_output', 'test_single.csv')
    assert os.path.exists(file_path), "CSV file not created for single dict"
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['name'] == 'Charlie'
    print("✓ Test single dict passed")

def test_empty_data():
    """Test with empty data - should not create file"""
    data = []
    save_to_csv(data, 'test_empty', 'test_output')
    file_path = os.path.join('test_output', 'test_empty.csv')
    assert not os.path.exists(file_path), "CSV file created for empty data"
    print("✓ Test empty data passed")

def test_invalid_data():
    """Test with invalid data (not dicts)"""
    data = ['not', 'dicts']
    save_to_csv(data, 'test_invalid', 'test_output')
    file_path = os.path.join('test_output', 'test_invalid.csv')
    assert not os.path.exists(file_path), "CSV file created for invalid data"
    print("✓ Test invalid data passed")

def test_non_existent_dir():
    """Test with non-existent directory"""
    data = [{'item': 'test'}]
    save_to_csv(data, 'test_new_dir', 'test_output/new_subdir')
    file_path = os.path.join('test_output', 'new_subdir', 'test_new_dir.csv')
    assert os.path.exists(file_path), "CSV file not created in new directory"
    print("✓ Test non-existent directory passed")

def cleanup():
    """Clean up test files"""
    if os.path.exists('test_output'):
        shutil.rmtree('test_output')

if __name__ == "__main__":
    cleanup()  # Clean before tests
    test_list_of_dicts()
    test_single_dict()
    test_empty_data()
    test_invalid_data()
    test_non_existent_dir()
    cleanup()  # Clean after tests
    print("All tests passed!")