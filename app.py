from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Define a Pydantic model for a Task
class Task(BaseModel):
    title: str
    description: str = None
    completed: bool = False

# In-memory storage for tasks (will be reset on server restart)
tasks = []

# Route to get all tasks
@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    return tasks

# Route to create a new task
@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    tasks.append(task)
    return task

# Route to delete a task by index
@app.delete("/tasks/{task_id}", response_model=Task)
async def delete_task(task_id: int):
    if task_id < 0 or task_id >= len(tasks):
        return {"error": "Task not found"}
    return tasks.pop(task_id)
