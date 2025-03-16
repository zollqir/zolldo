#!/usr/bin/env python3

import argparse
import json
import os
import platform
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox
from typing import Any, Optional, TypedDict


class Task(TypedDict):
  title: str
  due_date: datetime
  completed: bool
  description: str


TODO_FILENAME = "todo.json"


class TaskManager:
  def __init__(self):
    '''Loads tasks from file.'''
    self.task_dict: dict[int, Task] = {}
    self.max_id = 0

    if os.path.exists(TODO_FILENAME):
      with open(TODO_FILENAME, "r") as file:
        self.task_dict = json.load(file)
        self.task_dict = {int(k): v for k, v in self.task_dict.items()}  # use ints rather than strs as keys
        for task in self.task_dict.values():
          task["due_date"] = datetime.fromisoformat(task["due_date"])  # convert ISO strings to datetimes
    else:
      self.task_dict = {}
    self.max_id = int(max(self.task_dict.keys())) if len(self.task_dict) > 0 else 0

  @staticmethod
  def datetime_serializer(obj: Any) -> str:
    '''Helper function for TaskManager.save().'''
    if isinstance(obj, datetime):
      return obj.isoformat()
    raise TypeError("Type is not serializable")

  def save(self) -> None:
    '''Save tasks to file.'''
    with open(TODO_FILENAME, "w") as file:
      json.dump(self.task_dict, file, default=self.datetime_serializer)

  def gen_id(self, id: Optional[int]) -> int:
    '''Generate a unique task id, using the given one if possible.'''
    # if user did not supply an id, generate one
    if id is None:
      self.max_id += 1
      return self.max_id
    # user supplied a desired id
    else:
      if self.max_id < id:
        self.max_id = id
      return id

  def add_task(self, title: str, due_date: datetime, description: str = "",
               completed: bool = False, id: Optional[int] = None) -> tuple[Task, int]:
    '''Create a new task.'''
    task: Task = {
      "title": title,
      "due_date": due_date,
      "completed": completed,
      "description": description
    }
    id_value = self.gen_id(id)
    self.task_dict[id_value] = task
    self.save()
    return task, id_value

  def list_tasks(self, sort_by: Optional[str] = None, completed: Optional[bool]
                 = None, reverse: bool = False) -> dict[int, Task]:
    '''Get tasks, optionally filtered by completion, and optionally sorted by either title or due date.'''
    filtered_tasks = dict(self.task_dict)
    if completed is not None:
      filtered_tasks = {k: v for k, v in filtered_tasks.items() if v["completed"] == completed}
    if sort_by == "title":
      filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: item[1]["title"])}
    elif sort_by == "due_date":
      filtered_tasks = {k: v for k, v in sorted(filtered_tasks.items(), key=lambda item: item[1]["due_date"])}
    if reverse:
      filtered_tasks = dict(reversed(filtered_tasks.items()))
    return filtered_tasks

  def update_task(self,
                  id: int,
                  title: Optional[str] = None,
                  due_date: Optional[datetime] = None,
                  description: Optional[str] = None,
                  completed: Optional[bool] = None) -> tuple[Task, int]:
    '''Updates a task's title, due date, description, and/or completion status. Raises an exception if called with an invalid task id.'''
    task = self.task_dict[id]
    if title is not None:
      task["title"] = title
    if due_date is not None:
      task["due_date"] = due_date
    if description is not None:
      task["description"] = description
    if completed is not None:
      task["completed"] = completed
    self.save()
    return task

  def delete_task(self, id: int) -> None:
    '''Deletes a task. Raises an exception if called with an invalid task id.'''
    del self.task_dict[id]
    self.save()

  def delete_all_tasks(self) -> None:
    '''Deletes all tasks.'''
    self.task_dict = {}
    self.save()

  def validate_title(self, title: str) -> str:
    '''Validates that title is a non-empty string. Raises an exception if it is an empty string.'''
    if title == "":
      raise argparse.ArgumentError(None, "Title must be at least 1 character.")
    return title
  
  def validate_due_date(self, due_date: str) -> datetime:
    '''Validates and processes due date string. Raises an exception if the string is invalid.'''
    try:
      date = datetime.fromisoformat(due_date)
      if date.tzinfo is None:  # assume timezone is same as system timezone
        date = date.astimezone()
      return date
    except ValueError:
      raise argparse.ArgumentError(None,
        "Invalid due date format (format: any ISO datetime string such as 1970-01-01 or 1970-01-01T00:00).")

  def validate_id(self, id: str) -> int:
    '''Validates a task ID. Raises an exception if the ID is not a positive integer.'''
    try:
      id_value = int(id)
      if id_value <= 0:
        raise ValueError
      return id_value
    except ValueError:
      raise argparse.ArgumentError(None, "Task id must be a positive integer.")

  def validate_unused_id(self, id: str) -> int:
    '''Validates a task ID. Raises an exception if the ID is invalid, or if the ID is already in use.'''
    id_value = self.validate_id(id)
    if id_value in self.task_dict:
      raise argparse.ArgumentError(None, f"ID {id} is already in use.")
    return id_value

  def validate_used_id(self, id: str) -> int:
    '''Validates a task ID. Raises an exception if the ID is invalid, or if the ID is not already in use.'''
    id_value = self.validate_id(id)
    if id_value not in self.task_dict:
      raise argparse.ArgumentError(None, f"ID {id} does not match any task.")
    return id_value


def stringify_task(task: Task, id: int) -> str:
  '''Converts a task into a human-readable string suitable for printing to the console.'''
  # autopep8: off
  return f"""{'\x1b[32m' + "☑" + '\033[0m' if task["completed"] else "☐"} {task["title"]} - {id}{" - " + '\033[91m' + "OVERDUE" + '\033[0m' if task["due_date"] < datetime.now().astimezone() else ""}
    Description: {task["description"]}
    Due: {task["due_date"].strftime("%Y %b %d %H:%M:%S")}"""
  # autopep8: on

def gui(manager: TaskManager) -> None:
  '''GUI interface of the program.'''
  root = tk.Tk()
  root.title("Zolldo - To-Do List")
  root.geometry("550x1000")
  
  # sort & filter dropdowns
  sort_frame = tk.Frame(root)
  sort_var = tk.StringVar(value="")
  sort_options =[ "", "title", "title, reversed", "due_date", "due_date, reversed"]
  tk.Label(sort_frame, text="Sort:", width=4).pack(side="left")
  sort_combobox = ttk.Combobox(sort_frame, textvariable=sort_var, values=sort_options, state="readonly")
  sort_combobox.pack(side="left")
  sort_frame.pack()
  
  filter_frame = tk.Frame(root)
  filter_var = tk.StringVar(value="")
  filter_options = [ "", "completed", "uncompleted"]
  tk.Label(filter_frame, text="Filter:", width=4).pack(side="left")
  filter_combobox = ttk.Combobox(filter_frame, textvariable=filter_var, values=filter_options, state="readonly")
  filter_combobox.pack(side="left")
  filter_frame.pack()
  
  # task list
  task_frame = tk.Frame(root)
  task_frame.pack(fill=tk.BOTH, expand=True)
  canvas = tk.Canvas(task_frame, borderwidth=0)
  canvas.pack(fill=tk.BOTH, expand=True)
  scrollable_frame = tk.Frame(canvas)
  canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
  scrollbar = tk.Scrollbar(canvas, orient="vertical", command=canvas.yview)
  scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
  canvas.configure(yscrollcommand=scrollbar.set)
  scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
  canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))
  
  if platform.system() == "Linux":
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
  else:
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-int(e.delta / 120), "units"))
  
  # add task input fields
  mandatory_input_frame = tk.Frame(root)
  tk.Label(mandatory_input_frame, text="Title:", width=18).pack(side="left")
  title_entry = tk.Entry(mandatory_input_frame)
  title_entry.pack(side="left")
  
  tk.Label(mandatory_input_frame, text="Due Date:", width=18).pack(side="left")
  due_date_entry = tk.Entry(mandatory_input_frame)
  due_date_entry.pack(side="left")
  
  mandatory_input_frame.pack()
  
  optional_input_frame = tk.Frame(root)
  tk.Label(optional_input_frame, text="Description (optional):", width=18).pack(side="left")
  desc_entry = tk.Entry(optional_input_frame)
  desc_entry.pack(side="left")
  
  tk.Label(optional_input_frame, text="ID (optional)", width=18).pack(side="left")
  id_entry = tk.Entry(optional_input_frame)
  id_entry.pack(side="left")
  
  optional_input_frame.pack()
  
  checkbox_vars = {}
  
  def add_task_gui() -> None:
    '''Adds a task from the GUI.'''
    title_str = title_entry.get().strip()
    due_date_str = due_date_entry.get().strip()
    description = desc_entry.get().strip()
    id_str = id_entry.get().strip()
    
    try:
      title = manager.validate_title(title_str)
      due_date = manager.validate_due_date((due_date_str))
      id = manager.validate_unused_id(id_str) if id_str else None
      manager.add_task(title, due_date, description, False, id)
      refresh_list()
      clear_inputs()
    except argparse.ArgumentError as e:
      messagebox.showerror("Error", str(e))
  
  def toggle_completion_gui(id: int) -> None:
    '''Toggles a task's completion from the GUI. We use this rather than update_task because it avoids re-rendering.'''
    manager.update_task(id, completed=not manager.task_dict[id]["completed"])
  
  def delete_task_gui(id: int, frame: tk.Frame) -> None:
    '''Deletes a task from the GUI.'''
    frame.pack_forget()
    frame.destroy()
    del checkbox_vars[id]
    manager.delete_task(id)
  
  def delete_all_tasks_gui() -> None:
    '''Deletes all tasks from the GUI.'''
    if messagebox.askyesno("Confirm", "Are you sure you want to delete all tasks?"):
      for id in checkbox_vars:
        del checkbox_vars[id]
      manager.delete_all_tasks()
      refresh_list()
  
  add_button = tk.Button(root, text="Add Task", command=add_task_gui)
  add_button.pack()
  
  delete_all_button = tk.Button(root, text="Delete All", fg="red", command=delete_all_tasks_gui)
  delete_all_button.pack()
  
  def edit_task_field(id: int, field: str, entry: tk.Entry) -> None:
    '''Replaces a label with an entry widget for editing.'''
    
    new_value = entry.get().strip()
    
    try:
      match field:
        case "title":
          manager.update_task(id, title=manager.validate_title(new_value))
        case "due_date":
          manager.update_task(id, due_date=manager.validate_due_date(new_value))
        case "description":
          manager.update_task(id, description=new_value)
    except argparse.ArgumentError as e:
      entry.delete(0, tk.END)
      entry.insert(0, manager.task_dict[id][field])
      messagebox.showerror("Error", str(e))
      

  def refresh_list() -> None:
    '''Display tasks on the GUI.'''
    for widget in scrollable_frame.winfo_children():
      widget.destroy()
    
    sort_split = sort_var.get().split(",")
    sort_by = sort_split[0] if len(sort_split) > 0 else None
    reverse = sort_split[1] == " reversed" if len(sort_split) > 1 else False
    filter_value = filter_var.get()
    completed = None if filter_value  == "" else filter_value == filter_options[1] # "completed"
    tasks = manager.list_tasks(sort_by, completed, reverse)
    for id, task in tasks.items():
      frame = tk.Frame(scrollable_frame)
      frame.pack(fill="x", pady=2)
      frame.columnconfigure(0, weight=1)
      frame.columnconfigure(1, weight=1)
      frame.columnconfigure(2, weight=6)
      frame.columnconfigure(3, weight=6)
      frame.columnconfigure(4, weight=1)
      
      # checkbox
      checkbox_vars[id] = tk.BooleanVar(value=task["completed"])
      checkbox = tk.Checkbutton(frame, variable=checkbox_vars[id], command=lambda id=id: toggle_completion_gui(id))
      checkbox.grid(row=0, column=0)
      
      # ID
      tk.Label(frame, text=f"{id}").grid(row=0, column=1)
      
      # title
      title_label = tk.Entry(frame)
      title_label.insert(0, task["title"])
      title_label.grid(row=0, column=2, sticky=tk.EW)
      title_label.bind("<Return>",   lambda e, id=id, entry=title_label: edit_task_field(id, "title", entry))
      title_label.bind("<FocusOut>", lambda e, id=id, entry=title_label: edit_task_field(id, "title", entry))
      
      # due date
      due_date_label = tk.Entry(frame)
      due_date_label.insert(0, task["due_date"])
      if task["due_date"] < datetime.now().astimezone():
        due_date_label.config(fg="red")
      due_date_label.grid(row=0, column=3, sticky=tk.EW)
      due_date_label.bind("<Return>",   lambda e, id=id, entry=due_date_label: edit_task_field(id, "due_date", entry))
      due_date_label.bind("<FocusOut>", lambda e, id=id, entry=due_date_label: edit_task_field(id, "due_date", entry))
      
      # delete button
      delete_button = tk.Button(frame, text="X", fg="red", command=lambda id=id, frame=frame: delete_task_gui(id, frame))
      delete_button.grid(row=0, column=4, padx=10)
      
      # description
      desc_label = tk.Entry(frame)
      desc_label.insert(0, task["description"])
      desc_label.grid(row=1, column=2, rowspan=3, columnspan=2, pady=2, sticky=tk.NSEW)
      desc_label.bind("<Return>",   lambda e, id=id, entry=desc_label: edit_task_field(id, "description", entry))
      desc_label.bind("<FocusOut>", lambda e, id=id, entry=desc_label: edit_task_field(id, "description", entry))
  
  def clear_inputs() -> None:
    '''Clears the input fields.'''
    
    title_entry.delete(0, tk.END)
    due_date_entry.delete(0, tk.END)
    desc_entry.delete(0, tk.END)
    id_entry.delete(0, tk.END)
  
  title_entry.bind(   "<Return>", lambda e: add_task_gui())
  due_date_entry.bind("<Return>", lambda e: add_task_gui())
  desc_entry.bind(    "<Return>", lambda e: add_task_gui())
  id_entry.bind(      "<Return>", lambda e: add_task_gui())
  
  sort_combobox.bind(  "<<ComboboxSelected>>", lambda e: refresh_list())
  filter_combobox.bind("<<ComboboxSelected>>", lambda e: refresh_list())
  
  refresh_list()
  root.mainloop()

def cli() -> None:
  '''CLI interface of the program.'''
  manager = TaskManager()
  parser = argparse.ArgumentParser(
    prog="zolldo",
    description="A lightweight todo-list application CLI")
  subparsers = parser.add_subparsers(dest="command", required=True)

  # autopep8: off
  # add
  add_parser = subparsers.add_parser("add", help="Add a new to-do task.")
  add_parser.add_argument("--title",                required=True, type=manager.validate_title,                   help="Title of the task.")
  add_parser.add_argument("--due_date",             required=True, type=manager.validate_due_date,                help="Due date (format: any ISO datetime string such as 1970-01-01 or 1970-01-01T00:00).")
  add_parser.add_argument("--description",          required=False,type=str,                        default="",   help="Description of the task.")
  add_parser.add_argument("--id",                   required=False,type=manager.validate_unused_id, default=None, help="Specify a unique ID for the task.")
  add_completed_group = add_parser.add_mutually_exclusive_group()
  add_completed_group.add_argument("--completed",   required=False,action="store_true", dest="completed",         help="Mark task as completed.")
  add_completed_group.add_argument("--uncompleted", required=False,action="store_false",dest="completed",         help="Mark task as uncompleted (default).")
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
  update_parser.add_argument("--id",                    required=True, type=manager.validate_used_id,           help="ID of the task to update.")
  update_parser.add_argument("--title",                 required=False,type=manager.validate_title,             help="New title of the task.")
  update_parser.add_argument("--due_date",              required=False,type=manager.validate_due_date,          help="New due date (format: any ISO datetime string such as 1970-01-01 or 1970-01-01T00:00).")
  update_parser.add_argument("--description",           required=False,type=str,                                help="New description of the task.")
  update_completed_group = update_parser.add_mutually_exclusive_group()
  update_completed_group.add_argument("--completed",    required=False,action="store_true",  dest="completed",  help="Mark task as completed.")
  update_completed_group.add_argument("--uncompleted",  required=False,action="store_false", dest="completed",  help="Mark task as uncompleted.")
  update_completed_group.set_defaults(completed=None)

  # delete
  delete_parser = subparsers.add_parser("delete", help="Delete a task.")
  delete_group = delete_parser.add_mutually_exclusive_group(required=True)
  delete_group.add_argument("--id",  type=manager.validate_used_id, help="ID of the task to delete.")
  delete_group.add_argument("--all", action="store_true",           help="Delete all tasks.")
  
  # gui
  gui_parser = subparsers.add_parser("gui", help="Interact with your To-Do list using a GUI.")
  # autopep8: on
  args = parser.parse_args()

  match args.command:
    case "add":
      task, id = manager.add_task(title=args.title, due_date=args.due_date,
                                  description=args.description, completed=args.completed, id=args.id)
      print(f"""Task successfully added:
  {stringify_task(task, id)}""")
    case "list":
      tasks = manager.list_tasks(sort_by=args.sort_by, completed=args.completed, reverse=args.reverse)
      for id, task in tasks.items():
        print(stringify_task(task, id))
    case "update":
      task = manager.update_task(
          id=args.id,
          title=args.title,
          due_date=args.due_date,
          description=args.description,
          completed=args.completed)
      print(f"""Task successfully updated:
  {stringify_task(task, args.id)}""")
    case "delete":
      if args.all and input("are you sure? (y/n)") == "y":
        manager.delete_all_tasks()
        print("Successfully deleted all tasks.")
      elif args.id:
        manager.delete_task(args.id)
        print(f"Successfully deleted task {args.id}")
    case "gui":
      gui(manager=manager)

if __name__ == "__main__":
  cli()
