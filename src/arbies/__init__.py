import importlib
from typing import Type, Dict

_import_class_cache: Dict[str, Type] = {}


def import_module_class_from_fullname(name) -> Type:
    if name not in _import_class_cache:
        name_index: int = name.rindex('.')
        module_name: str = name[:name_index]
        class_name: str = name[name_index + 1:]
        module = importlib.import_module(module_name)
        _import_class_cache[name] = getattr(module, class_name)
    return _import_class_cache[name]
