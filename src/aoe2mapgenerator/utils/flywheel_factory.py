from typing import Any


class FlywheelFactory:
    """
    This class is a flywheel factory that stores instances of objects in a dictionary.
    """

    _instances: Any = {}

    @classmethod
    def get_instance(cls, key, create_func):
        """
        Retrieves an existing instance from the flywheel or creates a new one if not found.

        Args:
            key (Any): Unique identifier for the object.
            create_func (Callable): Function to create the object if it doesn't exist.

        Returns:
            Any: The requested object instance.
        """
        if key not in cls._instances:
            cls._instances[key] = create_func()
        return cls._instances[key]

    @classmethod
    def clear(cls):
        """Clears the flywheel cache."""
        cls._instances.clear()
