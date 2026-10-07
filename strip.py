import os
import subprocess
import sys

# This script is a simple wrapper that executes strip_xpy3.py in a custom environment


ENV_NAME = 'env'
TARGET = 'strip_xpy3.py'

# Determine the python executable inside the custom environment
if os.name == "nt":
  python_exe = os.path.join(
      os.path.dirname(__file__), ENV_NAME, "Scripts", "python.exe"
  )
else:
  python_exe = os.path.join(os.path.dirname(__file__), ENV_NAME, "bin", "python")

target_script = os.path.join(os.path.dirname(__file__), TARGET)

# Execute the target script, passing through all I/O and arguments
try:
  result = subprocess.run(
      [python_exe, target_script] + sys.argv[1:],
      stdin=sys.stdin,
      stdout=sys.stdout,
      stderr=sys.stderr,
  )
  sys.exit(result.returncode)
except Exception as e:
  sys.stderr.write(f"Wrapper execution error: {e}\n")
  sys.exit(1)