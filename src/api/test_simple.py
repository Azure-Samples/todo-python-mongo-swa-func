#!/usr/bin/env python3

import sys
import os

# Add the current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from todo.models import Settings, TodoListModel, CreateUpdateTodoList, TodoState
from datetime import datetime

def test_basic_functionality():
    """Test basic functionality without involving FastAPI or TestClient"""
    
    # Test Settings class (without Key Vault)
    settings = Settings()
    print("✓ Settings created successfully")
    
    # Test TodoListModel
    todo_list = TodoListModel(
        id="test-id",
        name="Test List",
        description="Test Description",
        createdDate=datetime.utcnow(),
        updatedDate=None
    )
    print("✓ TodoListModel created successfully")
    print(f"  List: {todo_list.name}")
    
    # Test CreateUpdateTodoList
    create_list = CreateUpdateTodoList(
        name="New List",
        description="New Description"
    )
    print("✓ CreateUpdateTodoList created successfully")
    print(f"  Create data: {create_list.name}")
    
    # Test TodoState enum
    state = TodoState.TODO
    print(f"✓ TodoState enum works: {state.value}")
    
    print("\nAll basic functionality tests passed! ✓")

if __name__ == "__main__":
    test_basic_functionality()