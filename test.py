from powershell import Modules

mod = Modules(runner_kwargs={'capture_output': True, 'text': True})
result = mod.keys()
print('Result is', result, sep=': ')