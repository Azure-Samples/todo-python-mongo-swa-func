import asyncio
import os
from typing import List
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from todo.app import app, settings
from todo.models import CosmosService, TodoListModel, TodoItemModel, CreateUpdateTodoList, CreateUpdateTodoItem, TodoState
from datetime import datetime
import uuid

TEST_DB_NAME = "test_db"


@pytest.fixture(scope="session")
def event_loop():
    """
    Redefine the event_loop fixture to be session scoped.
    Requirement of pytest-asyncio if there are async fixtures
    with non-function scope.
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.new_event_loop()


# Mock Cosmos service for testing
class MockCosmosService:
    def __init__(self):
        self.lists = {}
        self.items = {}

    def generate_id(self) -> str:
        return str(uuid.uuid4())

    async def create_list(self, list_data: CreateUpdateTodoList) -> TodoListModel:
        id = self.generate_id()
        todo_list = TodoListModel(
            id=id,
            name=list_data.name,
            description=list_data.description,
            createdDate=datetime.utcnow(),
            updatedDate=None
        )
        self.lists[id] = todo_list
        return todo_list

    async def get_list(self, list_id: str) -> TodoListModel:
        return self.lists.get(list_id)

    async def get_lists(self, skip: int = 0, limit: int = None) -> List[TodoListModel]:
        lists = list(self.lists.values())
        if skip:
            lists = lists[skip:]
        if limit:
            lists = lists[:limit]
        return lists

    async def update_list(self, list_id: str, list_data: CreateUpdateTodoList) -> TodoListModel:
        if list_id not in self.lists:
            return None
        todo_list = self.lists[list_id]
        todo_list.name = list_data.name
        todo_list.description = list_data.description
        todo_list.updatedDate = datetime.utcnow()
        return todo_list

    async def delete_list(self, list_id: str) -> bool:
        if list_id in self.lists:
            del self.lists[list_id]
            return True
        return False

    async def create_item(self, list_id: str, item_data: CreateUpdateTodoItem) -> TodoItemModel:
        id = self.generate_id()
        todo_item = TodoItemModel(
            id=id,
            listId=list_id,
            name=item_data.name,
            description=item_data.description,
            state=item_data.state,
            dueDate=item_data.dueDate,
            completedDate=item_data.completedDate,
            createdDate=datetime.utcnow(),
            updatedDate=None
        )
        self.items[id] = todo_item
        return todo_item

    async def get_item(self, list_id: str, item_id: str) -> TodoItemModel:
        item = self.items.get(item_id)
        if item and item.listId == list_id:
            return item
        return None

    async def get_items(self, list_id: str, skip: int = 0, limit: int = None) -> List[TodoItemModel]:
        items = [item for item in self.items.values() if item.listId == list_id]
        if skip:
            items = items[skip:]
        if limit:
            items = items[:limit]
        return items

    async def get_items_by_state(self, list_id: str, state: TodoState, skip: int = 0, limit: int = None) -> List[TodoItemModel]:
        items = [item for item in self.items.values() if item.listId == list_id and item.state == state]
        if skip:
            items = items[skip:]
        if limit:
            items = items[:limit]
        return items

    async def update_item(self, list_id: str, item_id: str, item_data: CreateUpdateTodoItem) -> TodoItemModel:
        item = self.items.get(item_id)
        if item and item.listId == list_id:
            item.name = item_data.name
            item.description = item_data.description
            item.state = item_data.state
            item.dueDate = item_data.dueDate
            item.completedDate = item_data.completedDate
            item.updatedDate = datetime.utcnow()
            return item
        return None

    async def update_items_state(self, list_id: str, item_ids: List[str], state: TodoState) -> List[TodoItemModel]:
        results = []
        for item_id in item_ids:
            item = self.items.get(item_id)
            if item and item.listId == list_id:
                item.state = state
                item.updatedDate = datetime.utcnow()
                results.append(item)
        return results

    async def delete_item(self, list_id: str, item_id: str) -> bool:
        item = self.items.get(item_id)
        if item and item.listId == list_id:
            del self.items[item_id]
            return True
        return False


@pytest.fixture()
def app_client():
    # Replace cosmos service with mock
    mock_cosmos = MockCosmosService()
    app.state.cosmos = mock_cosmos
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
async def initialize_database():
    # No database initialization needed for mock
    yield
