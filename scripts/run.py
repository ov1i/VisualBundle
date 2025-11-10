""" This file is a wrapper that helps users run the app """

import subprocess as sp
import os
import sys

python3_exe = "python3"
python_exe = "python"
main_path = "main.py"

if os.name == 'nt':
    print("\n\n\tWindows detected\n\n")
    python3_exe = "python3.exe"
    python_exe = "python.exe"
else:
    print("\n\n\tLinux/MacOS detected\n\n")

python_path = os.path.join(".venv", "bin", python3_exe)

if not os.path.exists(python_path):
    python_path = os.path.join(".venv", "Scripts", python_exe)
    if not os.path.exists(python_path):
        print("\n\nError please check you have a virtual enviroment set up\n\n")
        sys.exit(-1)

if not os.path.exists(main_path):
    print("\n\nError please check run.py script path\n\n")
    sys.exit(-1)

if os.path.exists(python_path) and os.path.exists(main_path):
    command = python_path + " " + main_path

    sp.run(command, check=True, shell=True)
else :
    print("\n\nUnknown error\n\n")
    sys.exit(-1)
