from datetime import datetime
from http import HTTPStatus
from typing import List, Optional
from urllib.parse import urljoin

from fastapi import HTTPException, Response, Request
from starlette.requests import Request

from .app import app
from .models import (CreateUpdateTodoItem, CreateUpdateTodoList, TodoItemModel,
                     TodoListModel, TodoState)


@app.get("/lists", response_model=List[TodoListModel])
async def get_lists(
    top: Optional[int] = None, skip: Optional[int] = None
) -> List[TodoListModel]:
    """
    Get all Todo lists

    Optional arguments:

    - **top**: Number of lists to return
    - **skip**: Number of lists to skip
    """
    return app.state.cosmos.get_lists(skip=skip or 0, limit=top)


@app.post("/lists", response_model=TodoListModel, status_code=201)
async def create_list(body: CreateUpdateTodoList, request: Request, response: Response) -> TodoListModel:
    """
    Create a new Todo list
    """
    todo_list = app.state.cosmos.create_list(body)
    response.headers["Location"] = urljoin(str(request.base_url), f"lists/{todo_list.id}")
    return todo_list


@app.get("/lists/{list_id}", response_model=TodoListModel)
async def get_list(list_id: str) -> TodoListModel:
    """
    Get Todo list by ID
    """
    todo_list = app.state.cosmos.get_list(list_id)
    if not todo_list:
        raise HTTPException(status_code=404, detail="Todo list not found")
    return todo_list


@app.put("/lists/{list_id}", response_model=TodoListModel)
async def update_list(
    list_id: str, body: CreateUpdateTodoList
) -> TodoListModel:
    """
    Updates a Todo list by unique identifier
    """
    todo_list = app.state.cosmos.update_list(list_id, body)
    if not todo_list:
        raise HTTPException(status_code=404, detail="Todo list not found")
    return todo_list


@app.delete("/lists/{list_id}", response_class=Response, status_code=204)
async def delete_list(list_id: str) -> None:
    """
    Deletes a Todo list by unique identifier
    """
    success = app.state.cosmos.delete_list(list_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo list not found")


@app.post("/lists/{list_id}/items", response_model=TodoItemModel, status_code=201)
async def create_list_item(
    list_id: str, body: CreateUpdateTodoItem, request: Request, response: Response
) -> TodoItemModel:
    """
    Creates a new Todo item within a list
    """
    item = app.state.cosmos.create_item(list_id, body)
    response.headers["Location"] = urljoin(str(request.base_url), f"lists/{list_id}/items/{item.id}")
    return item


@app.get("/lists/{list_id}/items", response_model=List[TodoItemModel])
async def get_list_items(
    list_id: str,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> List[TodoItemModel]:
    """
    Gets Todo items within the specified list

    Optional arguments:

    - **top**: Number of lists to return
    - **skip**: Number of lists to skip
    """
    return app.state.cosmos.get_items(list_id, skip=skip or 0, limit=top)


@app.get("/lists/{list_id}/items/state/{state}", response_model=List[TodoItemModel])
async def get_list_items_by_state(
    list_id: str,
    state: TodoState,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> List[TodoItemModel]:
    """
    Gets a list of Todo items of a specific state

    Optional arguments:

    - **top**: Number of lists to return
    - **skip**: Number of lists to skip
    """
    return app.state.cosmos.get_items_by_state(list_id, state, skip=skip or 0, limit=top)


@app.put("/lists/{list_id}/items/state/{state}", response_model=List[TodoItemModel])
async def update_list_items_state(
    list_id: str,
    state: TodoState,
    body: List[str] = None,
) -> List[TodoItemModel]:
    """
    Changes the state of the specified list items
    """
    if not body:
        raise HTTPException(status_code=400, detail="No items specified")
    return app.state.cosmos.update_items_state(list_id, body, state)


@app.get("/lists/{list_id}/items/{item_id}", response_model=TodoItemModel)
async def get_list_item(
    list_id: str, item_id: str
) -> TodoItemModel:
    """
    Gets a Todo item by unique identifier
    """
    item = app.state.cosmos.get_item(list_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Todo item not found")
    return item


@app.put("/lists/{list_id}/items/{item_id}", response_model=TodoItemModel)
async def update_list_item(
    list_id: str,
    item_id: str,
    body: CreateUpdateTodoItem,
) -> TodoItemModel:
    """
    Updates a Todo item by unique identifier
    """
    item = app.state.cosmos.update_item(list_id, item_id, body)
    if not item:
        raise HTTPException(status_code=404, detail="Todo item not found")
    return item


@app.delete("/lists/{list_id}/items/{item_id}", response_class=Response, status_code=204)
async def delete_list_item(
    list_id: str, item_id: str
) -> None:
    """
    Deletes a Todo item by unique identifier
    """
    success = app.state.cosmos.delete_item(list_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo item not found")
