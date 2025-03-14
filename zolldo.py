#!/usr/bin/env python3

import json
import os
from typing import Optional, TypedDict

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
  '''Get tasks, optionally filtered by completion, and optionally sorted by either title or due date.'''
  global task_dict
  filtered_tasks = dict(task_dict)
  if completed is not None:
    filtered_tasks = {k: v for k, v in filtered_tasks.items() if v["is_completed"] == completed}
  if sort_by == "title":
    filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: item[1]["title"])}
  elif sort_by == "due_date":
    filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: item[1]["due_date"])}
  return filtered_tasks

def update_task(task_id: int, title: Optional[str] = None, due_date: Optional[str] = None, description: Optional[str] = None, is_completed: Optional[bool] = None) -> Task:
  '''Updates a task's title, due date, description, and/or completion status. Implicitly raises an exception if called with an invalid task id.'''
  global task_dict
  task = task_dict[task_id]
  if title is not None:
    task["title"] = title
  if due_date is not None:
    task["due_date"] = due_date
  if description is not None:
    task["description"] = description
  if is_completed is not None:
    task["is_completed"] = is_completed
  save()
  return task

def delete_task(task_id: int) -> None:
  '''Deletes a task. Implicitly raises an exception if called with an invalid task id.'''
  global task_dict
  del task_dict[task_id]
  save()

def delete_all_tasks() -> None:
  '''Deletes all tasks.'''
  global task_dict
  task_dict = {}
  save()

def main():
  load()

if __name__ == "__main__":
  main()