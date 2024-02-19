from subprocess import call
import os, sys

for folder in ("blomp_api.egg-info", "build", "dist"):
    for path, folders, files in reversed(tuple(os.walk(folder))):
        for file in files:
            filepath = f"{path}{os.sep}{file}"
            os.remove(filepath)
            print(f'file {filepath} deleted')
        
        os.rmdir(path)

if not "--only-delete" in sys.argv:
    call(["python", "setup.py", "sdist", "bdist_wheel"])