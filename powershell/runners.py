"""

"""
from abc import ABC, abstractmethod
from logging import getLogger
from subprocess import run as subprocess_run


LOGGER = getLogger(__name__)


class AbstractRunner(ABC):
	"""Abstract Runner
	Describes how a class based runner should be.
	"""

	@abstractmethod
	def __init__(self, *args, **kwargs):
		"""Initialization
		Usually store the provided parameters for execution time
		"""

	@abstractmethod
	def __call__(self, command_string):
		"""Run
		Execute the provided command string
		"""


class SubprocessRunner(AbstractRunner):
	"""Subprocess runner
	Execute commands using subprocess.run
	"""

	def __init__(self, *args, **kwargs):
		"""Initialization
		Store extra parameters to pass to subprocess.run. The class will add "capture_output" and "text" if not present.

		:param kwargs: extra parameters to pass to subprocess.run
		:type kwargs: dict
		"""

		self.kwargs = kwargs

	def __call__(self, command_string):
		"""Run with subprocess
		Use the subprocess stdlib module to execute the provided command in PowerShell. Return the stdout, stderr, and returncode.

		:param command_string: the command to be run
		:type command_string: str
		:return: the stdout, stderr, and returncode
		:rtype: tuple
		"""

		if 'capture_output' not in self.kwargs:
			self.kwargs['capture_output'] = True
		if 'text' not in self.kwargs:
			self.kwargs['text'] = True

		result = subprocess_run(('pwsh', '-Command', command_string), **self.kwargs)
		return result.stdout, result.stderr, result.returncode
