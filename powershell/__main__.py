#!python
"""A convenient way to use PowerShell from Python
Handle command construction, piping, and execution using subprocess. Uses JSON for input and output data.

This is the executable script
"""

from simplifiedapp import main

try:
	import powershell
except ModuleNotFoundError:
	import __init__ as powershell

main(powershell)