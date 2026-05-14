#!python
"""

This is the executable script
"""

from simplifiedapp import main

try:
	import powershell
except ModuleNotFoundError:
	import __init__ as powershell

main(powershell)