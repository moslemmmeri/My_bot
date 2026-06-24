# src/admin_panel/bootstrap/module_register.py
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, field

from my_bot.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AdminModule:
    """Data class representing an admin module."""
    name: str
    handlers: Optional[Dict[str, Any]] = None
    keyboards: Optional[Dict[str, Any]] = None
    services: Optional[Dict[str, Any]] = None
    validators: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    is_loaded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModuleRegister:
    """
    Registry for admin modules.

    Manages the registration and retrieval of admin modules,
    their handlers, services, and other components.
    """

    def __init__(self) -> None:
        self._modules: Dict[str, AdminModule] = {}
        self._loaded_modules: List[str] = []

    def register_module(
        self,
        name: str,
        handlers: Optional[Dict[str, Any]] = None,
        keyboards: Optional[Dict[str, Any]] = None,
        services: Optional[Dict[str, Any]] = None,
        validators: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a new admin module.

        Args:
            name: Unique module name (e.g., 'user_management')
            handlers: Dictionary of handler functions
            keyboards: Dictionary of keyboard builders
            services: Dictionary of service classes
            validators: Dictionary of validator classes
            dependencies: List of module names this module depends on
            metadata: Additional metadata for the module
        """
        if name in self._modules:
            logger.warning(f"Module '{name}' is already registered. Overwriting.")
            return

        module = AdminModule(
            name=name,
            handlers=handlers or {},
            keyboards=keyboards or {},
            services=services or {},
            validators=validators or {},
            dependencies=dependencies or [],
            metadata=metadata or {},
            is_loaded=False,
        )
        self._modules[name] = module
        logger.info(f"Module '{name}' registered successfully.")

    def get_module(self, name: str) -> Optional[AdminModule]:
        """Get a registered module by name."""
        return self._modules.get(name)

    def get_all_modules(self) -> List[str]:
        """Get list of all registered module names."""
        return list(self._modules.keys())

    def get_loaded_modules(self) -> List[str]:
        """Get list of loaded module names."""
        return self._loaded_modules.copy()

    def get_module_handlers(self, name: str) -> Optional[Dict[str, Any]]:
        """Get handlers of a specific module."""
        module = self.get_module(name)
        return module.handlers if module else None

    def get_module_keyboards(self, name: str) -> Optional[Dict[str, Any]]:
        """Get keyboards of a specific module."""
        module = self.get_module(name)
        return module.keyboards if module else None

    def get_module_services(self, name: str) -> Optional[Dict[str, Any]]:
        """Get services of a specific module."""
        module = self.get_module(name)
        return module.services if module else None

    def get_module_validators(self, name: str) -> Optional[Dict[str, Any]]:
        """Get validators of a specific module."""
        module = self.get_module(name)
        return module.validators if module else None

    def mark_loaded(self, name: str) -> None:
        """Mark a module as loaded."""
        module = self.get_module(name)
        if module:
            module.is_loaded = True
            if name not in self._loaded_modules:
                self._loaded_modules.append(name)
            logger.info(f"Module '{name}' marked as loaded.")
        else:
            logger.warning(f"Cannot mark module '{name}' as loaded: module not found.")

    def is_loaded(self, name: str) -> bool:
        """Check if a module is loaded."""
        module = self.get_module(name)
        return module.is_loaded if module else False

    def has_module(self, name: str) -> bool:
        """Check if a module is registered."""
        return name in self._modules

    def clear(self) -> None:
        """Clear all registered modules."""
        self._modules.clear()
        self._loaded_modules.clear()
        logger.info("Module registry cleared.")

    def get_module_count(self) -> int:
        """Get the total number of registered modules."""
        return len(self._modules)


# Convenience decorator for defining modules
def module_registry(module_register: ModuleRegister):
    """
    Decorator factory to register a module class/function.
    Usage:
        @module_registry(register)
        class MyModule:
            name = "my_module"
            handlers = {...}
    """
    def decorator(cls_or_func):
        if hasattr(cls_or_func, "name"):
            name = cls_or_func.name
            handlers = getattr(cls_or_func, "handlers", {})
            keyboards = getattr(cls_or_func, "keyboards", {})
            services = getattr(cls_or_func, "services", {})
            validators = getattr(cls_or_func, "validators", {})
            dependencies = getattr(cls_or_func, "dependencies", [])
            metadata = getattr(cls_or_func, "metadata", {})
            module_register.register_module(
                name=name,
                handlers=handlers,
                keyboards=keyboards,
                services=services,
                validators=validators,
                dependencies=dependencies,
                metadata=metadata,
            )
        return cls_or_func
    return decorator