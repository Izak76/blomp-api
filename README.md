# blomp-api

[![Static Badge](https://img.shields.io/badge/GitHub-Source_code-blue?logo=github&logoColor=white)](https://github.com/Izak76/blomp-api)
[![PyPI - License](https://img.shields.io/pypi/l/blomp-api)](https://github.com/Izak76/blomp-api/blob/main/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/blomp-api)](https://pypi.org/project/blomp-api)
![PyPI - Status](https://img.shields.io/pypi/status/blomp-api)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/blomp-api?logo=python&logoColor=white)
<!-- ([![Pepy Total Downlods](https://img.shields.io/pepy/dt/blomp-api)](https://www.pepy.tech/projects/blomp-api)) -->

A unofficial Python API client to the [Blomp cloud](https://www.blomp.com).

## Table of contents
- [Instalation](#instalation)
- [Examples](#examples)
    - [Getting started with the API](#getting-started-with-the-api)
    - [Example directory structure for the next examples](#example-directory-structure-for-the-next-examples)
    - [Access files and folders](#access-files-and-folders)
    - [Downloading a file and getting download progress](#downloading-a-file-and-getting-download-progress)
    - [Uploading a file and getting upload progress](#uploading-a-file-and-getting-upload-progress)
    - [Other operations with folders](#other-operations-with-folders)
        - [Create a new folder](#create-a-new-folder)
        - [Renaming a folder](#renaming-a-folder)
        - [Cutting or copying files and folders](#cutting-or-copying-files-and-folders)
        - [Deleting files and folders](#deleting-files-and-folders)
    - [Other operations with files](#other-operations-with-files)
        - [Renaming a file](#renaming-a-file)
        - [Sharing a file](#sharing-a-file)
- [Other information](#other-information)
- [License](#license)
- [Source Code](#source-code)

## Instalation
Blomp API can be installed with pip:
```sh
pip install blomp-api
```

## Examples

### Getting started with the API
```python
from blomp_api import Blomp

# Log in to your Blomp account
blomp = Blomp("youremail@example.com", "yourpassword")

# Get your cloud root directory
root = blomp.get_root_directory()
```

### Example directory structure for the next examples
```
(root directory)
├── folder1/
│   ├── file1.ext
│   └── file2.ext
├── folder2/
│   ├── folder3/
│   │   └── file3.ext
│   └── file4.ext
├── file5.txt
└── file6.ext
```

### Access files and folders
```python
# Getting a folder using the get_folder_by_name method
folder1 = root.get_folder_by_name("folder1")

# Getting a file using the get_file_by_name method
file5 = root.get_file_by_name("file5.ext")

# Getting a file from a tuple with all files in the folder
# root.files -> (File(file5.ext), File(file6.ext))
file6 = root.files[-1]

# Getting a folder from a tuple with all subfolders in the folder
# root.subfolders -> (Folder(folder1), Folder(folder2))
folder2 = root.subfolders[1]

# All folders are iterable
# tuple(folder) is equivalent to folder.subfolders+folder.files
# tuple(folder2) -> (Folder(folder3), File(file4.ext))
folder3 = tuple(folder2)[0]

# All folders are subscriptable
# folder[i] is equivalent to tuple(folder)[i]
file1 = folder1[0]
file4 = folder2[1]
```

### Downloading a file and getting download progress
```python
# NOTE: All folder and file variables are the same as in previous examples

# Specifying a directory to save the file
# The following file will be saved as "/path/to/save/file1.ext"
thread1, monitor1 = file1.download("/path/to/save")

# Waiting for file1.ext to complete download
thread1.join()

# Specifying a directory and file name
# The following file will be saved as "/path/to/save/f4.ext"
# If a directory is not specified, then the file will be saved
# in the same directory where the program is running.
# This time we will let the following download occur in parallel
file4.download("/path/to/save/f4.ext")

# Specifying an open file object
with open("file5.ext", "wb") as f5:
    thread5 = file5.download(f5)[0]
    thread5.join()

# Nothing specified
# The following file will be saved as "file6.ext"
thread6, monitor6 = file6.download()

# Monitoring "file6.ext" download progress
while thread6.is_alive():
    loaded = monitor6.loaded
    total = monitor6.total
    progress = int(monitor6.progress)*100

    print(f"\r{loaded} of {total} bytes downloaded ({progress}%)")
```

### Uploading a file and getting upload progress
```python
# NOTE: All folder and file variables are the same as in previous examples

# Uploading a file to root directory
# The file will be saved in the root directory as "file7.ext"
thread7, monitor7 = root.upload("/path/to/file/file7.ext")

# Monitoring "file7.ext" upload progress
while thread7.is_alive():
    loaded = monitor7.loaded
    total = monitor7.total
    progress = int(monitor7.progress)*100

    print(f"\r{loaded} of {total} bytes uploaded ({progress}%)")

# Uploading a file from a file object to "folder1"
# The file will be saved in the folder1 as file8.ext
with open("/path/to/file/file8.ext", "rb") as f8:
    thread8, monitor8 = folder1.upload(f8)
    thread8.join()

# Upload specifying file name
folder3.upload("path/to/file/file9_1.ext", file_name="file9.ext")[0].join()

# Uploading a file when there is already another file
# with the same name in folder.
# If a file of the same name is found and the "replace_if_exists"
# attribute is False (default), FileExistsError is raised.
folder3.upload("path/to/file/file9.ext", replace_if_exists=True)
```

### Other operations with folders
All folder and file variables in the following examples are the same as in the previous examples.

#### Create a new folder
```python
# Creating a new folder in "folder3" com nome "folder4"
folder3.create_folder("folder4")
```

#### Renaming a folder
```python
# Renaming "folder4" to "folder5"
folder4 = folder3.get_folder_by_name("folder4")
folder4.safe_rename("folder5")
print(folder4.name) # Will be printed "folder5"
```

#### Cutting or copying files and folders
```python
folder5 = folder3.get_folder_by_name("folder5")
file7 = root.get_file_by_name("file7.ext")

# The following operations apply to both files and folders

# Copying a file to a folder
folder5.paste(file7)

# Cutting a folder to another folder
folder1.paste(folder5, cut=True)

folder1.reload()
folder5.reload()
```

#### Deleting files and folders
```python
# Deleting a file
file8 = folder1.get_file_by_name("file8.ext")
folder1.delete(file8)

# Deleting a folder
folder1.delete(folder5)

# Deleting a file by name (also works with folder names)
folder3.delete("file9.ext")

folder1.reload()
folder3.reload()
```

### Other operations with files
All folder and file variables in the following examples are the same as in the previous examples.

#### Renaming a file
```python
file6.rename("file66.ext")
print(file6.name) # Will be printed "file66.ext"
```

#### Sharing a file
```python
# Enabling sharing of "file1.ext" and getting the link
file1_link = file1.share()

# Enabling sharing of "file2.ext" and sending the link to an email list
file2 = folder1.get_file_by_name("file2.ext")
file2_link = file2.share(["email1@example.com", "email2@example.com"])

# Disabling sharing of "file1.ext"
file1.share_switch_off()

# Enabling sharing of "file1.ext"
file1.share_switch_on()
```

## Other information
For more information, type into your Python shell:
```python
help(<blomp_object>)
```
Where `<blomp_object>` can be:
- A `Blomp` instance
    - Example:
        ```python
        from blomp import Blomp

        blomp = Blomp("youremail@example.com", "yourpassword")
        help(blomp)
        ```
- A `Folder`object
    - Example:
        ```python
        root = blomp.get_root_directory()
        help(root)
        ```
- A `File` object
    - Example:
        ```python
        file = root.get_file_by_name("<file_name>")
        help(file)
        ```

## License
This package is released under the MIT License. See the [LICENSE](https://github.com/Izak76/blomp-api/blob/main/LICENSE) file for details.

## Source Code
Source code is available on [GitHub](https://github.com/Izak76/blomp-api).

## Changelog
Changelog is available on [GitHub](https://github.com/Izak76/blomp-api/blob/main/CHANGELOG).