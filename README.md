# Zolldo - To-Do List Application

This a simple and lightweight to-do list application that provides both a CLI and a GUI for task management. Users can add, view, update, and delete tasks.

## Features

- **CLI and GUI Support**: Manage tasks via the command line or an interactive Tkinter-based GUI.
- **Task Management**:
  - Add tasks with titles and optional descriptions.
  - List tasks with sorting and filtering.
  - Edit task details.
  - Mark tasks as completed.
  - Delete individual or all tasks.
- **Persistent Storage**: Tasks are saved in a JSON file (`tasks.json`).

## Installation

Ensure you have Python 3.10 or higher installed, and install with:

```sh
$ pip install zolldo
```

## Usage

### CLI Usage

See the help menu with:

```sh
$ zolldo -h
```

#### Commands:
- **Add a task:**
  ```sh
  $ zolldo add --title "Task Title" --due_date 2025-03-15T21:30 --description "Optional Description"
  ```
- **List tasks:**
  ```sh
  $ zolldo list
  ```
- **Mark a task as completed:**
  ```sh
  $ zolldo update --id <ID> --completed
  ```

- **Update task information:**
  ```sh
  $ zolldo update --id <ID> --tile "New Title"
  ```

- **Delete a task:**
  ```sh
  $ zolldo delete --id <ID>
  OR
  $ zolldo delete --all
  ```

See the help menu for more details.

### GUI Usage

Run the GUI with:

```sh
$ zolldo gui
```

## License

This project is licensed under the GNU v3 Public License.

## Author

[zollqir](https://github.com/zollqir)

