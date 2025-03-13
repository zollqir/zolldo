#!/usr/bin/env python3

import json
import os
from typing import Optional, TypedDict
from datetime import datetime

class Task(TypedDict):
  title: str
  due_date: str
  is_completed: bool
  description: str

TODO_FILENAME = "todo.json"

task_dict: dict[int, Task] = [] # dict of id -> Task
max_id = 0 # largest id currently in use

def load() -> None:
  '''Load tasks from file.'''
  global task_dict, max_id
  if os.path.exists(TODO_FILENAME):
    with open(TODO_FILENAME, "r") as file:
      task_dict = json.load(file)
      task_dict = {int(k): v for k, v in task_dict.items()} # use ints rather than strs as keys
  else:
    task_dict = {}
  max_id = int(max(task_dict.keys())) if len(task_dict) > 0 else 0

def save() -> None:
  '''Save tasks to file.'''
  global task_dict
  with open(TODO_FILENAME, "w") as file:
    json.dump(task_dict, file)

def gen_id(id: int | None) -> int:
  '''Generate a unique task id, using the given one if possible. Raises an exception if supplied with an id that is already in use.'''
  global task_dict, max_id
  # if user did not supply an id, generate one
  if id is None:
    max_id += 1
    return max_id
  # if user supplied a desired id, and it is not already in use, use it
  elif id and id > 0 and id not in task_dict.keys():
    if max_id < id:
      max_id = id
    return id  
  # user supplied an id that was already in use
  else:
    raise Exception(f"ID {id} is already in use!")


def add_task(title: str, due_date: str, description: str = "", id: Optional[int] = None) -> Task:
  '''Create a new task.'''
  global task_dict
  task: Task = {
    "title": title,
    "due_date": due_date,
    "is_completed": False,
    "description": description
  }
  task_dict[gen_id(id)] = task
  save()
  return task

def list_tasks(sort_by: Optional[str] = None, completed: Optional[bool] = None) -> dict[int, Task]:
  '''Get tasks, optionally filtered by completion, and sorted by either title or due date.'''
  global task_dict
  filtered_tasks = dict(task_dict)
  if completed is not None:
    filtered_tasks = {k: v for k, v in filtered_tasks.items() if v["is_completed"] == completed}
  if sort_by == "title":
    filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: item[1]["title"])}
  elif sort_by == "due_date":
    filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: datetime.strptime(item[1]["due_date"], "%Y-%m-%d-%H:%M"))}
  return filtered_tasks

load()
add_task("task b", "2025-04-13-02:31", "description b")
add_task("task c", "2025-04-13-02:30", "description c")
add_task("task a", "2025-04-13-02:29", "description a")
task_dict[1]["is_completed"] = True
print("Unsorted: ")
print(list_tasks())
print("Unsorted, without completed: ")
print(list_tasks(completed=False))
print("Unsorted, without uncompleted: ")
print(list_tasks(completed=True))
print("Sorted by title: ")
print(list_tasks(sort_by="title"))
print("Sorted by title, without completed: ")
print(list_tasks(sort_by="title", completed=False))
print("Sorted by title, without uncompleted: ")
print(list_tasks(sort_by="title", completed=True))
print("Sorted by due date: ")
print(list_tasks(sort_by="due_date"))
print("Sorted by due date, without completed: ")
print(list_tasks(sort_by="due_date", completed=False))
print("Sorted by due date, without uncompleted: ")
print(list_tasks(sort_by="due_date", completed=True))