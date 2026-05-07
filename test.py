from powershell import PowerShell, PipedCommand, Modules
from pprint import pprint as pprint_

ps = PowerShell()
# mod = Modules(runner_kwargs={'capture_output': True, 'text': True})
# result = ps.modules['Appx'].keys()
result = ps.modules['Appx']['Get-AppxPackage']()
# result = ps.modules['Appx']._load()
# cmd = PipedCommand('Get-Module -ListAvailable', output_is_object=True)
# result = cmd(PowerShell.with_subprocess, capture_output=True, text=True)
# print('Result is', result, sep=': ')
pprint_(result)