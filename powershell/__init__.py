"""

"""

from json import dumps as json_dumps, loads as json_loads
from logging import getLogger
from subprocess import run as subprocess_run


LOGGER = getLogger('__name__')


class Modules(dict):
	"""

	"""

	def __init__(self, runner=None, runner_kwargs=None):
		"""

		:param shell:
		"""

		super().__init__()
		self._shell = PowerShell(runner=runner)

	def __missing__(self, name):
		"""

		:param name:
		:return:
		"""

	def keys(self):
		"""

		:return:
		"""

		return self._shell('Get-Module')


class PipedCommand:
	"""
	Describes a piped command chain for PowerShell.
	"""

	def __init__(self, initial_command_line=None):
		"""Initialization
		Add the initial/unique command line to the list of commands in the pipe list

		:param initial_command_line: The initial command line
		:type initial_command_line: str
		"""

		self._commands = []
		if initial_command_line is not None:
			self._commands.append(initial_command_line)

	def __or__(self, next_command):
		"""Add a command to the pipe list
		Just adds the provided command line to the list

		:param next_command: the next command to add to the pipe list
		:type next_command: str
		:return: self
		:rtype: PowerShellCommand
		"""

		self._commands.append(next_command)
		return self

	def __str__(self):
		"""

		:return:
		"""

		return ' | '.join(self._commands)

	@staticmethod
	def build_command_line(command, /, **kwargs):
		"""

		:param command:
		:param kwargs:
		:return:
		"""

		result = [command]
		for key, value in kwargs.items():
			if value is None:
				result.append(f'-{key}')
			else:
				result.append(f'-{key} {value}')

		return ' '.join(result)

	@classmethod
	def from_components(cls, command, /, **kwargs):
		"""

		:param command:
		:param kwargs:
		:return:
		"""

		return cls(cls.build_command_line(command, **kwargs))


class PowerShell:
	"""

	"""

	def __call__(self, command_string, input_data=None):
		"""

		:param command_string:
		:return:
		"""

		cmd = PipedCommand()
		if input_data is not None:
			cmd |= f"'{json_dumps(input_data)}'"
			cmd |= 'ConvertFrom-Json'
		cmd |= command_string
		cmd |= 'ConvertTo-Json'
		result = self._runner(str(cmd), **self._runner_kwargs)
		return vars(result)
		return json_loads(result)

	def __new__(cls, runner=None, runner_kwargs=None):
		"""

		:param runner:
		"""

		instance = super().__new__(cls)
		if runner is None:
			instance._runner = cls.with_subprocess
		else:
			instance._runner = runner
		instance._runner_kwargs = {} if runner_kwargs is None else runner_kwargs
		return instance

	@staticmethod
	def with_subprocess(command_string, /, **kwargs):
		"""

		:param command_string:
		:return:
		"""

		return subprocess_run(('powershell', '-Command', command_string), **kwargs)