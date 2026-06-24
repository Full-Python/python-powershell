"""Some generic code
This is some utilitary code that should probably live elsewhere.
"""

from abc import abstractmethod
from logging import getLogger


LOGGER = getLogger('__name__')


class PurePythonDict(dict):
	"""Pure python dict
	An effort to overlay the builtin dict type which is usually implemented on the interpreter language into a native python one. The main goal is to improve the inheritance. The main reason to pursue this is the internal implementation of builtin dicts: they don't rely on the public interface, which means that overriding certain methods won't trigger the implicit/expected behavior. By exposing such implementations here, it improves the result of overriding builtin methods.

	ToDo: This follows the very old dicts. Extra work will have to be done to get dict views working on these.
	"""

	def __len__(self):
		"""Dict __len__
		Override of the builtin dict __len__ method
		"""

		return len(self.keys())

	def items(self):
		"""Dict items
		Override of the builtin dict items method

		:return: a list with the items
		:rtype: list
		"""

		return [(key, self[key]) for key in self.keys()]

	def keys(self):
		"""Dict keys
		Override of the builtin dict keys method

		:return: a set with the keys
		:rtype: set
		"""

		return super().keys()

	def values(self):
		"""Dict values
		Override of the builtin dict values method

		:return: a list with the values
		:rtype: list
		"""

		return [self[key] for key in self.keys()]


class LazyDict(PurePythonDict):
	"""A lazy dict that loads all its content on a single operation.
	Intended for static lazy objects that might not need to be loaded in certain conditions and which contents can only be retrieved via a single operation (very expensive for big dicts).
	"""

	_already_loaded = False

	@abstractmethod
	def _load_dict(self):
		"""Load the dict
		Execute the potentially expensive operation to load the dict content.

		:return: "the" dict with the items
		:rtype: dict
		"""

	def keys(self):
		"""Dict keys
		Override of the builtin dict keys method

		:return: a set with the keys
		:rtype: set
		"""

		if not self._already_loaded:
			self.update(self._load_dict())
			self._already_loaded = True

		return super().keys()


class LazyKeyedDict(PurePythonDict):
	"""A lazy dict that loads all its keys with a single operation and its values with individual ones.
	Intended for static lazy objects that might not need to be loaded in certain conditions and supports retrieving the list of keys and individual values (identified by key).
	"""

	def __getattr__(self, name):
		"""Magic attribute resolution
		Lazy calculation of certain attributes

		:param name: the attribute that is not defined (yet)
		:type name: str
		:returns: the value for the attribute
		:rtype: Any
		"""

		if name == '_keys':
			value = frozenset(self._load_keys())
		else:
			raise AttributeError(name)

		self.__setattr__(name, value)
		return value

	def __missing__(self, name):
		"""Lazy value load
		Load the value

		:param name: the key of the value to load
		:type name: str
		:return: the value
		:rtype: Any
		"""

		if name not in self.keys():
			raise KeyError(name)

		value = self._load_value(name)
		self.__setitem__(name, value)
		return value

	@abstractmethod
	def _load_keys(self):
		"""Load the dict keys
		Load all the keys in the dict.

		:return: the keys
		:rtype: list
		"""

	@abstractmethod
	def _load_value(self, name):
		"""Load the dict
		Execute the potentially expensive operation to load the dict content.

		:param name: the key for the requested value
		:type name: Hashable
		:return: the value matching the key
		:rtype: Any
		"""

	def keys(self):
		"""Dict keys
		Override of the builtin dict keys method

		:return: a set with the keys
		:rtype: set
		"""

		return self._keys
