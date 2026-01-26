import os, inspect
import importlib.util, importlib
from pathlib import Path
from typing  import Type


class Module:
	@staticmethod
	def import_module(module_name: str, file_path: str):
		if not os.path.exists(file_path):
			raise FileNotFoundError(f'Module file does not exist: "{file_path}"')

		spec = importlib.util.spec_from_file_location(module_name, file_path)
		if not spec or not spec.loader:
			raise ImportError(f'Cannot import module from: "{file_path}"')

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)

		return module

	@staticmethod
	def import_class(class_name: str, file_path: str):
		module_name = Path(file_path).stem
		module      = Module.import_module(module_name, file_path)

		if not hasattr(module, class_name):
			raise AttributeError(f'Module "{file_path}" does not contain class "{class_name}"')

		return getattr(module, class_name)

	@staticmethod
	def find_all_classes_by_base(base_class: Type, file_path: str):
		module_name = Path(file_path).stem
		module      = Module.import_module(module_name, file_path)
		found = []
		for _, obj in inspect.getmembers(module, inspect.isclass):
			if issubclass(obj, base_class) and obj is not base_class:
				found.append(obj)
		return found
	
	@staticmethod
	def find_class_by_base(base_class: Type, file_path: str):
		results = Module.find_all_classes_by_base(base_class=base_class, file_path=file_path)
		if results:
			return results[0]
		return None

	@staticmethod
	def get_exports(file_path: str) -> list[str]:
		module_name = Path(file_path).stem
		module = Module.import_module(module_name, file_path)
		return getattr(module, '__all__', [])

	@staticmethod
	def load_package_classes(base_class: Type, package_path: str) -> dict[str, Type]:
		path       = Path(package_path).resolve()
		init_path  = path / '__init__.py'
		registry   = {}

		exports = []
		if init_path.exists():
			exports = Module.get_exports(str(init_path))
		if not exports:
			exports = [p.stem for p in path.glob('*.py') if p.name != '__init__.py']

		for name in exports:
			file_path = path / f'{name}.py'
			try:
				classes = Module.find_all_classes_by_base(base_class, str(file_path))
				for cls in classes:
					registry[cls.__name__] = cls
			except Exception as e:
				raise ImportError(f'Could not import {file_path}: {e}')
		return registry


	def get_module_text(module_name):
		module = importlib.import_module(module_name)
		path   = inspect.getfile(module)

		with open(path, 'r', encoding='utf-8') as f:
			return f.read()
