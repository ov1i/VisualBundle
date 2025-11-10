import subprocess as sp
import os

python3_exe = "python3"
python_exe = "python"

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
        exit(-1)

main_script_path = "main.py"
if not os.path.exists(main_script_path):
    print("\n\nError please check run.py script path\n\n")
    exit(-1)

if os.path.exists(python_path) and os.path.exists(main_script_path):
    command = python_path + " " + main_script_path

    sp.run(command, check=True, shell=True)
else :
    print("\n\nUnknown error\n\n")
    exit(-1)
