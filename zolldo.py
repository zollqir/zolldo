#!/usr/bin/env python3

import argparse
import json
import os
from datetime import datetime
from typing import Any, Optional, TypedDict

class Task(TypedDict):
  title: str
  due_date: datetime
  completed: bool
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
      for task in task_dict.values():
        task["due_date"] = datetime.fromisoformat(task["due_date"]) # convert ISO strings to datetimes
  else:
    task_dict = {}
  max_id = int(max(task_dict.keys())) if len(task_dict) > 0 else 0

def datetime_serializer(obj: Any) -> str:
  if isinstance(obj, datetime):
    return obj.isoformat()
  raise TypeError("Type is not serializable")
  
def save() -> None:
  '''Save tasks to file.'''
  global task_dict
  with open(TODO_FILENAME, "w") as file:
    json.dump(task_dict, file, default=datetime_serializer)

def gen_id(id: int | None) -> int:
  '''Generate a unique task id, using the given one if possible.'''
  global task_dict, max_id
  # if user did not supply an id, generate one
  if id is None:
    max_id += 1
    return max_id
  # user supplied a desired id
  else:
    if max_id < id:
      max_id = id
    return id  

def add_task(title: str, due_date: datetime, description: str = "", completed: bool = False, id: Optional[int] = None) -> tuple[Task, int]:
  '''Create a new task.'''
  global task_dict
  task: Task = {
    "title": title,
    "due_date": due_date,
    "completed": completed,
    "description": description
  }
  id_value = gen_id(id)
  task_dict[id_value] = task
  save()
  return task, id_value

def list_tasks(sort_by: Optional[str] = None, completed: Optional[bool] = None, reverse: bool = False) -> dict[int, Task]:
  '''Get tasks, optionally filtered by completion, and optionally sorted by either title or due date.'''
  global task_dict
  filtered_tasks = dict(task_dict)
  if completed is not None:
    filtered_tasks = {k: v for k, v in filtered_tasks.items() if v["completed"] == completed}
  if sort_by == "title":
    filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: item[1]["title"])}
  elif sort_by == "due_date":
    filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: item[1]["due_date"])}
  if reverse:
    filtered_tasks = dict(reversed(filtered_tasks.items()))
  return filtered_tasks

def update_task(id: int, title: Optional[str] = None, due_date: Optional[datetime] = None, description: Optional[str] = None, completed: Optional[bool] = None) -> tuple[Task, int]:
  '''Updates a task's title, due date, description, and/or completion status. Raises an exception if called with an invalid task id.'''
  global task_dict
  task = task_dict[id]
  
  if title is not None:
    task["title"] = title
  if due_date is not None:
    task["due_date"] = due_date
  if description is not None:
    task["description"] = description
  if completed is not None:
    task["completed"] = completed
  save()
  return task, id

def delete_task(id: int) -> None:
  '''Deletes a task. Raises an exception if called with an invalid task id.'''
  global task_dict
  del task_dict[id]
  save()

def delete_all_tasks() -> None:
  '''Deletes all tasks.'''
  global task_dict
  task_dict = {}
  save()

def validate_due_date(due_date: str) -> datetime:
  '''Validates and processes due date string. Raises an exception if the string is invalid.'''
  try:
    date = datetime.fromisoformat(due_date)
    if date.tzinfo is None: # assume timezone is same as system timezone
      date = date.astimezone()
    return date
  except ValueError:
    raise argparse.ArgumentError("Invalid due date format (format: any ISO datetime string such as 1970-01-01 or 1970-01-01T00:00).")

def validate_id(id: str) -> int:
  '''Validates a task ID. Raises an exception if the ID is not a positive integer.'''
  try:
    id_value = int(id)
    if id_value <= 0:
      raise ValueError
    return id_value
  except ValueError:
    raise argparse.ArgumentTypeError("Task id must be a positive integer.")
  
def validate_unused_id(id: str) -> int:
  '''Validates a task ID. Raises an exception if the ID is invalid, or if the ID is already in use.'''
  global task_dict
  id_value = validate_id(id)
  if id_value in task_dict:
    raise argparse.ArgumentError(f"ID {id} is already in use.")
  return id_value
  
def validate_used_id(id: str) -> int:
  '''Validates a task ID. Raises an exception if the ID is invalid, or if the ID is not already in use.'''
  global task_dict
  id_value = validate_id(id)
  if id_value not in task_dict:
    raise argparse.ArgumentError(f"ID {id} does not match any task.")
  return id_value

def stringify_task(task: Task, id: int) -> str:
  '''Converts a task into a human-readable string suitable for printing to the console.'''
  return f"""{'\x1b[32m' + "☑" + '\033[0m' if task["completed"] else "☐"} {task["title"]} - {id}{" - " + '\033[91m' + "OVERDUE" + '\033[0m' if task["due_date"] < datetime.now().astimezone() else ""}
    Description: {task["description"]}
    Due: {task["due_date"].strftime("%Y %b %d %H:%M:%S")}
"""

def cli() -> None:
  '''CLI interface of the program'''
  load()
  parser = argparse.ArgumentParser(
    prog="zolldo",
    description="A lightweight todo-list application CLI")
  subparsers = parser.add_subparsers(dest="command", required=True)
  
  # add
  add_parser = subparsers.add_parser("add", help="Add a new to-do task.")
  add_parser.add_argument("--title",            required=True, type=str,                                  help="Title of the task.")
  add_parser.add_argument("--due_date",         required=True, type=validate_due_date,                    help="Due date (format: any ISO datetime string such as 1970-01-01 or 1970-01-01T00:00).")
  add_parser.add_argument("--description",      required=False,type=str,                default="",       help="Description of the task.")
  add_parser.add_argument("--id",               required=False,type=validate_unused_id, default=None,     help="Specify a unique ID for the task.")
  add_completed_group = add_parser.add_mutually_exclusive_group()
  add_completed_group.add_argument("--completed",   required=False,action="store_true", dest="completed", help="Mark task as completed.")
  add_completed_group.add_argument("--uncompleted", required=False,action="store_false",dest="completed", help="Mark task as uncompleted (default).")
  add_completed_group.set_defaults(completed=False)
  
  # list
  list_parser = subparsers.add_parser("list", help="List all tasks.")
  list_parser.add_argument("--sort_by",               required=False, choices=["title", "due_date"],          help="Sort tasks by title or due date.")
  list_parser.add_argument("--reverse",               required=False, action="store_true", default=False,     help="Reverse the order of tasks displayed.")
  list_completed_group = list_parser.add_mutually_exclusive_group()
  list_completed_group.add_argument("--completed",    required=False, action="store_true", dest="completed",  help="Show only completed tasks.")
  list_completed_group.add_argument("--uncompleted",  required=False, action="store_false",dest="completed",  help="Show only uncompleted tasks.")
  list_completed_group.set_defaults(completed=None)
  
  # update
  update_parser = subparsers.add_parser("update", help="Update a task.")
  update_parser.add_argument("--id",                    required=True, type=validate_used_id,                   help="ID of the task to update.")
  update_parser.add_argument("--title",                 required=False,type=str,                                help="New title of the task.")
  update_parser.add_argument("--due_date",              required=False,type=validate_due_date,                  help="New due date (format: any ISO datetime string such as 1970-01-01 or 1970-01-01T00:00).")
  update_parser.add_argument("--description",           required=False,type=str,                                help="New description of the task.")
  update_completed_group = update_parser.add_mutually_exclusive_group()
  update_completed_group.add_argument("--completed",    required=False,action="store_true",  dest="completed",  help="Mark task as completed.")
  update_completed_group.add_argument("--uncompleted",  required=False,action="store_false", dest="completed",  help="Mark task as uncompleted.")
  update_completed_group.set_defaults(completed=None)
  
  # delete
  delete_parser = subparsers.add_parser("delete", help="Delete a task.")
  delete_group = delete_parser.add_mutually_exclusive_group(required=True)
  delete_group.add_argument("--id",  type=validate_used_id, help="ID of the task to delete.")
  delete_group.add_argument("--all", action="store_true",   help="Delete all tasks.")
  
  args = parser.parse_args()
  
  match args.command:
    case "add":
      task, id = add_task(title=args.title, due_date=args.due_date, description=args.description, completed=args.completed, id=args.id)
      print(f"""Task successfully added:
  {stringify_task(task, id)}""")
    case "list":
      tasks = list_tasks(sort_by=args.sort_by, completed=args.completed, reverse=args.reverse)
      for id, task in tasks.items():
        print(stringify_task(task, id))
    case "update":
      task, id = update_task(id=args.id, title=args.title, due_date=args.due_date, description=args.description, completed=args.completed)
      print(f"""Task successfully updated:
  {stringify_task(task, id)}""")
    case "delete":
      if args.all and input("are you sure? (y/n)") == "y":
        delete_all_tasks()
        print("Successfully deleted all tasks.")
      elif args.id:
        delete_task(args.id)
        print(f"Successfully deleted task {args.id}")

def main():
  cli()

if __name__ == "__main__":
  main()