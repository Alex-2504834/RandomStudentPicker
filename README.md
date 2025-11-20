# RandomStudentPicker

A simple, user-friendly desktop app (built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)) that helps teachers randomly pick students from a list, using **weighted fairness** so the same student isn’t selected repeatedly. Each pick reduces the chosen student’s weight, giving others a higher chance next time.

---

## Features

- Randomly selects a student **instantly** or with a **smooth animated spinner**
- Fair selection based on **weight reduction**
- Tracks how often each student has been picked
- Allows **resetting** weights or full stats
- Automatically **loads and saves** class files
- Customizable settings:
  - Light/Dark mode  
  - Color theme  
  - Spinner speed  
  - Weight decrease amount  

---

## Class File Location

When the app runs, it automatically creates:

```
~/Documents/randomStudentPicker/classes/
```

Place your `.json` or `.csv` class files in this folder.

They will appear in the app under:

```
Settings -> Class List
```

This is the **only** directory the app scans for class lists.

---

# Supported File Formats

The app accepts:

- **JSON** (`.json`)
- **CSV** (`.csv`)

Missing `weight` or `count` fields are automatically assigned defaults.

---

## JSON Examples

### Recommended JSON
```json
[
  { "name": "Alice", "weight": 1.0, "count": 0 },
  { "name": "Bob", "weight": 0.7, "count": 0 },
  { "name": "Charlie", "weight": 0.7, "count": 0 }
]
```

### Minimal JSON
```json
[
  { "name": "Alice" },
  { "name": "Bob" },
  { "name": "Charlie" }
]
```

---

## CSV Examples

### Recommended CSV
```csv
name,weight,count
Alice,0.5,0
Bob,0.4,3
Charlie,0.5,0
```

### Minimal CSV
```csv
name
Alice
Bob
Charlie
```

---

# Installing

## Option 1 - Using the Installer (recommended)

Run:

```
python installer.py
```

The installer will:

- Download the latest version of the application  
- Create the `randomStudentPicker` directory in your **Documents** folder  
- Install required Python dependencies  
- Optionally create:
  - A desktop shortcut  
  - A Start Menu / Application Menu entry  

After installation, you may launch the application from the shortcut or by running:

```
python ~/Documents/randomStudentPicker/main.py
```

---

## Option 2 — Manual Installation

1. Install the dependency:

   ```
   pip install customtkinter
   ```

2. Download or place `main.py` in any folder.

3. Run the application:

   ```
   python main.py
   ```

---

# Python Requirements

This application requires:

**Python 3.9 or higher**

Check your Python version:

```
python --version
```

---
