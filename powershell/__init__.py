"""A convenient way to use PowerShell from Python
Handle command construction, piping, and execution using subprocess. Uses JSON for input and output data.
"""

from json import dumps as json_dumps, loads as json_loads
from logging import getLogger

from .generic import LazyDict, LazyKeyedDict
from .runners import SubprocessRunner


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
__version__ = '0.3.0.dev6'


class PipedCommand(list):
	"""
	Describes a piped command chain for PowerShell.

	Attributes:
		- input_data: can be a string or an object (serializable into JSON). It will be added to the front of the chain.
		- output_is_object: boolean flag that triggers JSON parsing of the output
		- full_chain: dynamically builds the current command chain as a string
	"""

	def __call__(self, runner):
		"""Callable magic
		Execute the command described

		:param runner: a callable similar to the .runners.AbstractRunner interface, or a child of it.
		:type runner: callable
		:return: The result of the command as an object (dict) or string depending on the output_is_object init parameter
		:rtype: dict | str
		"""

		cmd = str(self)
		LOGGER.warning(f'Executing: {cmd}')
		stdout, stderr, returncode = runner(cmd)
		if self.output_is_object:
			return json_loads(stdout)
		else:
			return stdout

	def __init__(self, initial_command_line=None, input_data=None, output_is_object=True):
		"""Initialization
		Add the initial/unique command line to the list of commands in the pipe list

		:param initial_command_line: The initial command line, useful for simple commands
		:type initial_command_line: str
		:param input_data: Start by creating/feeding the provided data to the first command
		:type input_data: str|object|None
		:param output_is_object: Triggers a conversion to JSON of the last result
		:type output_is_object: bool
		"""

		super().__init__()
		self.input_data = input_data
		if initial_command_line is not None:
			self.append(initial_command_line)
		self.output_is_object = output_is_object

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
		"""Magic string representation
		The string representation of the current command chain.

		:return: the string representation of the current command chain
		:rtype: str
		"""

		return ' | '.join(self.full_chain)

	@staticmethod
	def build_command_line(command, parameters_definition=None, /, **parameters_values):
		"""Build command line
		Create a command line with the parameters provided. Starts with the command value and add switches to it based on the parameters_values.

		:param command: the actual "command"
		:type command: str
		:param parameters_definition: the valid switches supported by the command
		:type parameters_definition: dict
		:param parameters_values: the values for the switches
		:type parameters_values: dict
		:return: the command with all the switches added
		:rtype: str
		"""

		result = [command]
		if parameters_definition is None:
			for key, value in parameters_values.items():
				if value is None:
					result.append(f'-{key}')
				else:
					result.append(f'-{key} {value}')
		else:
			for key, type_ in parameters_definition.items():
				if key in parameters_values:
					if type_ is None:
						result.append(f'-{key}')
					else:
						result.append(f'-{key} {parameters_values.pop(key)}')

		return ' '.join(result)

	@property
	def full_chain(self):
		"""Return the full command chain
		Return the list with the input formatting command and output formatting one, if applicable.

		return: The input data, the commands on this chain, and the JSON converting command, if applicable.
		rtype: list
		"""

		if self.input_data is not None:
			if isinstance(self.input_data, str):
				initial_command = [f"'{self.input_data}'"]
			else:
				initial_command = [f"'{json_dumps(self.input_data)}'", 'ConvertFrom-Json']
		else:
			initial_command = []

		final_command = ['ConvertTo-Json'] if self.output_is_object else []
		return initial_command + self + final_command

	@classmethod
	def from_components(cls, command, /, **kwargs):
		"""Helper constructor from components
		Builds a chain with a single command from the components.

		:param command: the actual command
		:type command: str
		:param kwargs: command switches and their values
		:type kwargs: Any
		:return: a PipedCommand populated with the built command
		:rtype: PipedCommand
		"""

		return cls(cls.build_command_line(command, **kwargs))


class Command(LazyDict):
	"""
	Describes a single command in PowerShell
	"""

	def __call__(self, input_data=None, output_is_object=True, /, **kwargs):
		"""Callable magic
		Build the command with the currently registered switches, run it, and return the result.

		:param input_data: data to feed the command via pipes
		:type input_data: str|object|None
		:param output_is_object: selects the format of the output, True for dict, False for str
		:type output_is_object: bool
		:param kwargs: switches and values for the command
		:type kwargs: Any
		:return: the result of the command run
		:rtype: dict|str
		"""

		cmd = self._name if self._module is None else f'{self._module}\\{self._name}'
		cmd = PipedCommand.build_command_line(cmd, self, **kwargs)
		cmd = PipedCommand(cmd, input_data=input_data, output_is_object=output_is_object)
		return cmd(self._runner)

	def __init__(self, runner, name, module=None):
		"""Initialization
		Store the module, command name, and runner callable.

		:param runner: a callable similar to the .runners.AbstractRunner interface, or a child of it.
		:type runner: callable
		:param name: the actual command
		:type name: str
		:param module: the module containing the command
		:type module: str|None
		"""

		super().__init__()
		self._runner = runner
		self._name = name
		self._module = module

	def _load_dict(self):
		"""Load parameters
		Parses the definition of the command and compiles a list of all possible switches and the expected types.

		:return: the parameters for the command
		:rtype: dict
		"""

		params = {'Name': self._name}
		if self._module is not None:
			params['Module'] = self._module
		cmd = PipedCommand.from_components('Get-Command', **params)
		cmd |= 'Select-Object -ExpandProperty Parameters'

		result = {}
		for name, details in cmd(self._runner).items():
			result[name] = TYPE_MAP.get(details['ParameterType']['FullName'], dict)

		return result


class Module(LazyKeyedDict):
	"""
	Describes a single module in PowerShell
	"""

	def __init__(self, runner, name):
		"""Initialization
		Store the module and runner callable.

		:param name: the module name
		:type name: str
		:param runner: a callable similar to PowerShell.with_subprocess in signature and return format
		:type runner: callable
		"""

		super().__init__()
		self._name = name
		self._runner = runner

	def _load_keys(self):
		"""Load commands
		Retrieves the list of commands available in the module

		:return: the list of commands available in the module
		:rtype: set
		"""

		return {result['Name'] for result in PipedCommand.from_components('Get-Command', Module=self._name)(runner=self._runner)}

	def _load_value(self, name):
		"""Load value
		Return an instance of Command representing the named command

		:param name: the name of the command to load
		:type name: str
		:return: an instance of Command representing the named command
		:rtype: Command
		"""

		return Command(self._runner, name, self._name)


class Modules(LazyKeyedDict):
	"""
	Describes the list of modules available in PowerShell
	"""

	def __init__(self, runner):
		"""Initialization
		Store the runner callable.

		:param runner: a callable similar to PowerShell.with_subprocess in signature and return format
		:type runner: callable
		"""

		super().__init__()
		self._runner = runner

	def _load_keys(self):
		"""Load modules
		Imports the list of modules available to the shell

		:return: the list of modules available to the shell
		:rtype: set
		"""

		return {result['Name'] for result in PipedCommand.from_components('Get-Module', ListAvailable=None)(runner=self._runner)}

	def _load_value(self, name):
		"""Load value
		Return an instance of Module representing the named module

		:param name: the name of the module to load
		:type name: str
		:return: an instance of Module representing the named module
		:rtype: Module
		"""

		return Module(self._runner, name)


class PowerShell:
	"""
	High level interface to PowerShell
	"""

	def __call__(self, command, module=None, input_data=None, output_is_object=True, /, **kwargs):
		"""Callable magic
		Execute the command described

		:param command: the name of the command to execute
		:type command: str
		:param module: the name of the module containing the command
		:type module: str
		:param input_data: data to feed the command via pipes
		:type input_data: str|object|None
		:param output_is_object: selects the format of the output, True for dict, False for str
		:type output_is_object: bool
		:param kwargs: switches and values for the command
		:type kwargs: Any
		:return: the result of the command run
		:rtype: dict|str
		"""

		cmd = Command(runner=self._runner, name=command, module=module)
		return cmd(input_data, output_is_object, **kwargs)

	def __getattr__(self, name):
		"""Magic attribute resolution
		Lazy calculation of certain attributes

		:param name: the attribute that is not defined (yet)
		:type name: str
		:returns: the value for the attribute
		:rtype: Any
		"""

		if name == 'modules':
			value = Modules(runner=self._runner)
		else:
			raise AttributeError(name)

		self.__setattr__(name, value)
		return value

	def __init__(self, runner=None):
		"""Initialization
		Store the runner callable.

		:param runner: a callable similar to the .runners.AbstractRunner interface, or a child of it. Defaults to .runners.SubprocessRunner().
		:type runner: callable|None
		"""

		self._runner = SubprocessRunner() if runner is None else runner

	def run_string(self, command_string, input_data=None, output_is_object=True):
		"""Execute string
		Execute the command described in the string. Similar to the call magic method but with plain string instead of structured data.

		:param command_string: the full string of the command to execute
		:type command_string: str
		:param input_data: data to feed the command via pipes
		:type input_data: str|object|None
		:param output_is_object: selects the format of the output, True for dict, False for str
		:type output_is_object: bool
		:return: the result of the command run
		:rtype: dict|str
		"""

		return PipedCommand(initial_command_line=command_string, input_data=input_data, output_is_object=output_is_object)(runner=self._runner)
