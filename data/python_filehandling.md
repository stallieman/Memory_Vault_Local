# Python Template for File Handling & Basic Operations

## 1. Imports
```python
import os  # Provides functions for interacting with the operating system (e.g., file and directory operations).
```

## 2. File Traversal Function
```python
def traverse_directory(directory):
    """
    Traverse the given directory and print each directory and file.
    """
    for root, dirs, files in os.walk(directory):
        print(f"Directory: {root}")
        for file in files:
            print(f"  File: {file}")
```

## 3. File Reading Function
```python
def read_file(filepath):
    """
    Read the content of the file at filepath.
    Returns a list of lines or an empty list if an error occurs.
    """
    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()
        return lines
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []
```

## 4. File Writing Function
```python
def write_file(filepath, content):
    """
    Write the given content to a file at filepath.
    """
    try:
        with open(filepath, 'w') as file:
            file.write(content)
        print(f"Successfully wrote to {filepath}")
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")
```

## 5. Processing Files in a Directory
```python
def process_files(directory):
    """
    Traverse the directory and process each file by reading and printing its content.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            lines = read_file(filepath)
            for line in lines:
                print(line.strip())
```

## 6. Working with Lists and Dictionaries

### 6.1 Process List
```python
def process_list(items):
    """
    Loop through a list and print each item.
    """
    for item in items:
        print(f"Processing list item: {item}")
```

### 6.2 Process Dictionary
```python
def process_dictionary(data):
    """
    Loop through a dictionary and print each key and its corresponding value.
    """
    for key, value in data.items():
        print(f"Key: {key} - Value: {value}")
```

## 7. Main Function
```python
def main():
    """
    Main function that ties together directory traversal, file processing, and other utilities.
    Modify `directory_to_traverse` as needed for your project.
    """
    # Set the directory you want to work with (change this path as needed)
    directory_to_traverse = './your_directory'

    print("=== Traversing Directory ===")
    traverse_directory(directory_to_traverse)

    print("\n=== Processing Files in Directory ===")
    process_files(directory_to_traverse)

    # Example usages for lists and dictionaries:
    sample_list = ['apple', 'banana', 'cherry']
    sample_dict = {'name': 'Alice', 'age': 30, 'city': 'Wonderland'}

    print("\n=== Processing a Sample List ===")
    process_list(sample_list)

    print("\n=== Processing a Sample Dictionary ===")
    process_dictionary(sample_dict)

if __name__ == "__main__":
    main()
```

---

## ℹ️ Wanneer gebruik je welke helper? (+ voorbeelden)
- `traverse_directory(path)` → snel overzicht van mappen/bestanden. Voorbeeld: `traverse_directory('/tmp/data')`.  
- `read_file(path)` → inhoud als lijst van regels; gebruik in pipelines of validatie.  
- `write_file(path, content)` → textbestand schrijven (config/log). Voorbeeld: `write_file('out.txt', 'hello\\n')`.  
- `process_files(dir)` → alles in boom lezen en printen; pas aan om bijvoorbeeld CSV’s te parsen.  
- `process_list` / `process_dictionary` → simpele demo’s voor iteratie; vervang met eigen logica.  
- `main()` → invullen met jouw pad of commentaar en direct draaien: `python filehandling.py`.  
