"""

"""

from json import dumps as json_dumps, loads as json_loads
from logging import getLogger
from subprocess import run as subprocess_run


LOGGER = getLogger('__name__')
TYPE_MAP = {
	'System.Boolean': bool,
	'System.Collections.Hashtable': dict,
	'System.Double': float,
	'System.Int32': int,
	'System.Management.Automation.SwitchParameter': None,
	'System.String': str,
	'System.String[]': list,
}
__version__ = '0.2.0'


class PipedCommand(list):
	"""
	Describes a piped command chain for PowerShell.
	"""

	def __call__(self, runner, /, **kwargs):
		"""

		"""

		result = runner(str(self), **kwargs)
		if self._output_is_object:
			return json_loads(result.stdout)
		else:
			return result.stdout

	def __init__(self, initial_command_line=None, input_data=None, output_is_object=True):
		"""Initialization
		Add the initial/unique command line to the list of commands in the pipe list

		:param initial_command_line: The initial command line, useful for simple commands
		:type initial_command_line: str
		:param input_data: Start by creating/feeding the provided data to the first command
		:type input_data: str|object
		:param output_is_object: Triggers a conversion to JSON of the last result
		:type output_is_object: bool
		"""

		super().__init__()
		if input_data is not None:
			if isinstance(input_data, str):
				self.append(f"'{input_data}'")
			else:
				self.extend([f"'{json_dumps(input_data)}'", 'ConvertFrom-Json'])
		if initial_command_line is not None:
			self.append(initial_command_line)
		self._output_is_object = output_is_object

	def __or__(self, next_command):
		"""Add a command to the pipe list
		Just adds the provided command line to the list

		:param next_command: the next command to add to the pipe list
		:type next_command: str
		:return: self
		:rtype: PowerShellCommand
		"""

		self.append(next_command)
		return self

	def __str__(self):
		"""

		:return:
		"""

		extra_command = ['ConvertTo-Json'] if self._output_is_object else []
		return ' | '.join(self + extra_command)

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

	@staticmethod
	def build_command_line_v2(command, param_def={}, /, **param_values):
		"""

		:param command:
		:param param_def:
		:param param_values:
		:return:
		"""

		result = [command]
		for key, type_ in param_def.items():
			if key in param_values:
				if type_ is None:
					result.append(f'-{key}')
				else:
					result.append(f'-{key} {param_values.pop(key)}')

		return ' '.join(result)

	@classmethod
	def from_components(cls, command, /, **kwargs):
		"""

		:param command:
		:param kwargs:
		:return:
		"""

		return cls(cls.build_command_line(command, **kwargs))


class Command(dict):
	"""

	"""

	_already_loaded = False

	def __call__(self, input_data=None, /, *args, **kwargs):
		"""

		"""

		cmd = f'{self._module}\\{self._name}'
		cmd = PipedCommand.build_command_line_v2(cmd, self, **kwargs)
		cmd = PipedCommand(cmd, input_data=input_data)
		return cmd(self._runner)

	def __init__(self, module, name, runner):
		"""

		:param module:
		:type module:
		:param name:
		:type name:
		:param runner:
		:type runner:
		"""

		super().__init__()
		self._module = module
		self._name = name
		self._runner = runner

	def __iter__(self):
		"""

		"""

		self._load()
		return super().__iter__()

	def __getitem__(self, item):
		"""
		
		"""
		
		self._load()
		return super().__getitem__(item)

	def __len__(self):
		"""

		"""

		self._load()
		return super().__len__()

	def __missing__(self, name):
		"""

		:param name:
		:return:
		"""

		if self._already_loaded:
			raise KeyError(name)

		self._load()
		return self[name]

	def _load(self):
		"""

		"""

		if self._already_loaded:
			return False

		cmd = PipedCommand(f'Get-Command -Module {self._module} -Name {self._name}', output_is_object=True)
		cmd |= 'Select-Object -ExpandProperty Parameters'
		for name, result in cmd(self._runner).items():
			# self[name] = result['ParameterType']['FullName']
			self[name] = TYPE_MAP.get(result['ParameterType']['FullName'], dict)

		self._already_loaded = True
		return True

	def items(self, *args, **kwargs):
		"""

		"""

		self._load()
		return super().items(*args, **kwargs)

	def keys(self):
		"""

		:return:
		"""

		self._load()
		return super().keys()

	def values(self):
		"""

		"""

		self._load()
		return super().values()


class Module(dict):
	"""

	"""

	_already_loaded = False

	def __init__(self, name, runner):
		"""

		:param name:
		:type name:
		:param runner:
		:type runner:
		"""

		super().__init__()
		self._name = name
		self._runner = runner

	def __missing__(self, name):
		"""

		:param name:
		:return:
		"""

		if self._already_loaded:
			raise KeyError(name)

		self._load()
		return self[name]

	def _load(self):
		"""

		"""

		if self._already_loaded:
			return False

		cmd = PipedCommand(f'Get-Command -Module {self._name}', output_is_object=True)
		for result in cmd(self._runner):
			self[result['Name']] = Command(self._name, result['Name'], self._runner)

		self._already_loaded = True
		return True

	def items(self, *args, **kwargs):
		"""

		"""

		self._load()
		return super().items(*args, **kwargs)

	def keys(self):
		"""

		:return:
		"""

		self._load()
		return super().keys()

	def values(self):
		"""

		"""

		self._load()
		return super().values()


class Modules(dict):
	"""

	"""

	_already_loaded = False

	def __init__(self, runner):
		"""

		:param shell:
		"""

		super().__init__()
		self._runner = runner

	def __missing__(self, name):
		"""

		:param name:
		:return:
		"""

		if self._already_loaded:
			raise KeyError(name)

		self._load()
		return self[name]

	def _load(self):
		"""

		"""

		if self._already_loaded:
			return False

		cmd = PipedCommand('Get-Module -ListAvailable', output_is_object=True)
		for result in cmd(self._runner):
			self[result['Name']] = Module(result['Name'], self._runner)

		self._already_loaded = True
		return True

	def items(self, *args, **kwargs):
		"""

		"""

		self._load()
		return super().items(*args, **kwargs)

	def keys(self):
		"""

		:return:
		"""

		self._load()
		return super().keys()

	def values(self):
		"""

		"""

		self._load()
		return super().values()


class PowerShell:
	"""

	"""

	def __getattr__(self, name):
		"""

		"""

		if name == 'modules':
			value = Modules(runner=self._runner)
		else:
			raise AttributeError(name)

		self.__setattr__(name, value)
		return value

	def __init__(self, runner=None):
		"""

		:param runner:
		"""

		self._runner = self.with_subprocess if runner is None else runner

	@staticmethod
	def with_subprocess(command_string, /, **kwargs):
		"""

		:param command_string:
		:return:
		"""

		if 'capture_output' not in kwargs:
			kwargs['capture_output'] = True
		if 'text' not in kwargs:
			kwargs['text'] = True

		return subprocess_run(('powershell', '-Command', command_string), **kwargs)