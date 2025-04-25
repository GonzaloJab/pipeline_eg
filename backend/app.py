from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Task(BaseModel):
    title: str
    description: str = None
    completed: bool = False

tasks = []

@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    return tasks

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    tasks.append(task)
    return task

@app.delete("/tasks/{task_id}", response_model=Task)
async def delete_task(task_id: int):
    if task_id < 0 or task_id >= len(tasks):
        return {"error": "Task not found"}
    return tasks.pop(task_id)
