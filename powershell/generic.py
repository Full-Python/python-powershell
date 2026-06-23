"""

"""
from abc import abstractmethod, abstractstaticmethod
from logging import getLogger


LOGGER = getLogger('__name__')


class FullLoadDict(dict):
	"""Full load dict
	Custom dynamic dict that pulls all its content on a single operation. Useful for lazy objects that might not need to be loaded in certain conditions when the content can only be retrieved via a single operation (very expensive for big dicts).
	"""

	_already_loaded = False

	def __len__(self):
		"""Dict __len__
		Override of the builtin dict __len__ method
		"""

		return len(self.keys())

	@abstractmethod
	def _load_dict(self):
		"""Load the dict
		Execute the potentially expensive operation to load the dict content.

		:return: "the" dict with the items
		:rtype: dict
		"""

	def items(self, *args, **kwargs):
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

		if not self._already_loaded:
			self.update(self._load_dict())

		return super().keys()

	def values(self):
		"""Dict values
		Override of the builtin dict values method

		:return: a list with the values
		:rtype: list
		"""

		return [self[key] for key in self.keys()]


class FullKeysDict(dict):
	"""Full keys dict
	A dynamic dict that loads all the keys with a single operation and values with individual ones.
	"""

	_already_loaded = False

	def __len__(self):
		"""Dict __len__
		Override of the builtin dict __len__ method
		"""

		return len(self.keys())

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

	def items(self, *args, **kwargs):
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

		if not self._already_loaded:
			self.update(self._load_keys())

		return super().keys()

	def values(self):
		"""Dict values
		Override of the builtin dict values method

		:return: a list with the values
		:rtype: list
		"""

		return [self[key] for key in self.keys()]