from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.cosmos import CosmosClient, PartitionKey
from pydantic import BaseModel, BaseSettings


class Settings(BaseSettings):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load secrets from keyvault
        if self.AZURE_KEY_VAULT_ENDPOINT:
            credential = DefaultAzureCredential()
            keyvault_client = SecretClient(self.AZURE_KEY_VAULT_ENDPOINT, credential)
            for secret in keyvault_client.list_properties_of_secrets():
                setattr(
                    self,
                    secret.name.replace("-", "_").upper(),
                    keyvault_client.get_secret(secret.name).value,
                )

    AZURE_COSMOS_ENDPOINT: str = ""
    AZURE_COSMOS_DATABASE_NAME: str = "Todo"
    AZURE_KEY_VAULT_ENDPOINT: Optional[str] = None
    APPLICATIONINSIGHTS_CONNECTION_STRING: Optional[str] = None
    APPLICATIONINSIGHTS_ROLENAME: Optional[str] = "API"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class TodoListModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    createdDate: Optional[datetime] = None
    updatedDate: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CreateUpdateTodoList(BaseModel):
    name: str
    description: Optional[str] = None


class TodoState(Enum):
    TODO = "todo"
    INPROGRESS = "inprogress"
    DONE = "done"


class TodoItemModel(BaseModel):
    id: str
    listId: str
    name: str
    description: Optional[str] = None
    state: Optional[TodoState] = None
    dueDate: Optional[datetime] = None
    completedDate: Optional[datetime] = None
    createdDate: Optional[datetime] = None
    updatedDate: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CreateUpdateTodoItem(BaseModel):
    name: str
    description: Optional[str] = None
    state: Optional[TodoState] = None
    dueDate: Optional[datetime] = None
    completedDate: Optional[datetime] = None


class CosmosService:
    def __init__(self, endpoint: str, database_name: str):
        credential = DefaultAzureCredential()
        self.client = CosmosClient(endpoint, credential)
        self.database = self.client.get_database_client(database_name)
        self.lists_container = self.database.get_container_client("TodoList")
        self.items_container = self.database.get_container_client("TodoItem")

    def generate_id(self) -> str:
        return str(uuid.uuid4())

    # TodoList operations
    def create_list(self, list_data: CreateUpdateTodoList) -> TodoListModel:
        item = {
            "id": self.generate_id(),
            "name": list_data.name,
            "description": list_data.description,
            "createdDate": datetime.utcnow().isoformat(),
            "updatedDate": None
        }
        response = self.lists_container.create_item(item)
        return TodoListModel(**response)

    def get_list(self, list_id: str) -> Optional[TodoListModel]:
        try:
            response = self.lists_container.read_item(list_id, list_id)
            return TodoListModel(**response)
        except Exception:
            return None

    def get_lists(self, skip: int = 0, limit: int = None) -> List[TodoListModel]:
        query = "SELECT * FROM c"
        items = list(self.lists_container.query_items(query, enable_cross_partition_query=True))
        
        if skip:
            items = items[skip:]
        if limit:
            items = items[:limit]
            
        return [TodoListModel(**item) for item in items]

    def update_list(self, list_id: str, list_data: CreateUpdateTodoList) -> Optional[TodoListModel]:
        try:
            existing = self.lists_container.read_item(list_id, list_id)
            existing.update({
                "name": list_data.name,
                "description": list_data.description,
                "updatedDate": datetime.utcnow().isoformat()
            })
            response = self.lists_container.replace_item(list_id, existing)
            return TodoListModel(**response)
        except Exception:
            return None

    def delete_list(self, list_id: str) -> bool:
        try:
            self.lists_container.delete_item(list_id, list_id)
            return True
        except Exception:
            return False

    # TodoItem operations
    def create_item(self, list_id: str, item_data: CreateUpdateTodoItem) -> TodoItemModel:
        item = {
            "id": self.generate_id(),
            "listId": list_id,
            "name": item_data.name,
            "description": item_data.description,
            "state": item_data.state.value if item_data.state else None,
            "dueDate": item_data.dueDate.isoformat() if item_data.dueDate else None,
            "completedDate": item_data.completedDate.isoformat() if item_data.completedDate else None,
            "createdDate": datetime.utcnow().isoformat(),
            "updatedDate": None
        }
        response = self.items_container.create_item(item)
        return TodoItemModel(**response)

    def get_item(self, list_id: str, item_id: str) -> Optional[TodoItemModel]:
        try:
            response = self.items_container.read_item(item_id, list_id)
            return TodoItemModel(**response)
        except Exception:
            return None

    def get_items(self, list_id: str, skip: int = 0, limit: int = None) -> List[TodoItemModel]:
        query = "SELECT * FROM c WHERE c.listId = @listId"
        parameters = [{"name": "@listId", "value": list_id}]
        items = list(self.items_container.query_items(query, parameters=parameters, enable_cross_partition_query=True))
        
        if skip:
            items = items[skip:]
        if limit:
            items = items[:limit]
            
        return [TodoItemModel(**item) for item in items]

    def get_items_by_state(self, list_id: str, state: TodoState, skip: int = 0, limit: int = None) -> List[TodoItemModel]:
        query = "SELECT * FROM c WHERE c.listId = @listId AND c.state = @state"
        parameters = [
            {"name": "@listId", "value": list_id},
            {"name": "@state", "value": state.value}
        ]
        items = list(self.items_container.query_items(query, parameters=parameters, enable_cross_partition_query=True))
        
        if skip:
            items = items[skip:]
        if limit:
            items = items[:limit]
            
        return [TodoItemModel(**item) for item in items]

    def update_item(self, list_id: str, item_id: str, item_data: CreateUpdateTodoItem) -> Optional[TodoItemModel]:
        try:
            existing = self.items_container.read_item(item_id, list_id)
            existing.update({
                "name": item_data.name,
                "description": item_data.description,
                "state": item_data.state.value if item_data.state else existing.get("state"),
                "dueDate": item_data.dueDate.isoformat() if item_data.dueDate else existing.get("dueDate"),
                "completedDate": item_data.completedDate.isoformat() if item_data.completedDate else existing.get("completedDate"),
                "updatedDate": datetime.utcnow().isoformat()
            })
            response = self.items_container.replace_item(item_id, existing)
            return TodoItemModel(**response)
        except Exception:
            return None

    def update_items_state(self, list_id: str, item_ids: List[str], state: TodoState) -> List[TodoItemModel]:
        results = []
        for item_id in item_ids:
            try:
                existing = self.items_container.read_item(item_id, list_id)
                existing.update({
                    "state": state.value,
                    "updatedDate": datetime.utcnow().isoformat()
                })
                response = self.items_container.replace_item(item_id, existing)
                results.append(TodoItemModel(**response))
            except Exception:
                continue
        return results

    def delete_item(self, list_id: str, item_id: str) -> bool:
        try:
            self.items_container.delete_item(item_id, list_id)
            return True
        except Exception:
            return False
