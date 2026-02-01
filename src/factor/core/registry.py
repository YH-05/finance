"""Factor registry for centralized factor management.

This module provides a registry system for managing factor classes,
enabling registration, retrieval, and categorization of factors.

Classes
-------
FactorNotFoundError
    Exception raised when a factor is not found in the registry.
FactorRegistry
    Singleton registry for managing factor classes.

Functions
---------
get_registry
    Get the singleton FactorRegistry instance.
register_factor
    Class decorator for registering factors.

Examples
--------
>>> from factor.core.registry import get_registry, register_factor
>>> from factor.core.base import Factor
>>> from factor.enums import FactorCategory
>>>
>>> @register_factor
... class MyFactor(Factor):
...     name = "my_factor"
...     description = "My custom factor"
...     category = FactorCategory.VALUE
...     def compute(self, provider, universe, start_date, end_date):
...         return provider.get_prices(universe, start_date, end_date)
>>>
>>> registry = get_registry()
>>> registry.get("my_factor") is MyFactor
True
"""

# AIDEV-NOTE: Factor の循環インポートを避けるため TYPE_CHECKING を使用
from typing import TYPE_CHECKING, TypeVar

from utils_core.logging import get_logger

from factor.enums import FactorCategory
from factor.errors import FactorError

if TYPE_CHECKING:
    from factor.core.base import Factor

logger = get_logger(__name__)


# Type variable for factor classes
F = TypeVar("F", bound="Factor")


class FactorNotFoundError(FactorError):
    """Exception raised when a requested factor is not found in the registry.

    Parameters
    ----------
    factor_name : str
        The name of the factor that was not found.

    Examples
    --------
    >>> raise FactorNotFoundError("unknown_factor")
    FactorNotFoundError: Factor 'unknown_factor' not found in registry
    """

    def __init__(self, factor_name: str) -> None:
        """Initialize FactorNotFoundError.

        Parameters
        ----------
        factor_name : str
            The name of the factor that was not found.
        """
        message = f"Factor '{factor_name}' not found in registry"
        super().__init__(message, details={"factor_name": factor_name})
        self.factor_name = factor_name


class FactorRegistry:
    """Singleton registry for managing factor classes.

    This class provides centralized registration and retrieval of factor
    classes. It supports categorization and listing of registered factors.

    Attributes
    ----------
    _factors : dict[str, type[Factor]]
        Internal dictionary mapping factor names to their classes.

    Examples
    --------
    >>> from factor.core.registry import get_registry
    >>> registry = get_registry()
    >>> registry.register(MyFactor)
    >>> factor_class = registry.get("my_factor")
    >>> isinstance(factor_class(), MyFactor)
    True
    """

    def __init__(self) -> None:
        """Initialize an empty factor registry."""
        self._factors: dict[str, type["Factor"]] = {}
        logger.debug("FactorRegistry initialized")

    def register(self, factor_class: type["Factor"], *, force: bool = False) -> None:
        """Register a factor class in the registry.

        Parameters
        ----------
        factor_class : type[Factor]
            The factor class to register. Must have a `name` class attribute.
        force : bool, default=False
            If True, allows overwriting an existing registration.

        Raises
        ------
        FactorError
            If a factor with the same name is already registered and
            force is False.

        Examples
        --------
        >>> registry = get_registry()
        >>> registry.register(MyFactor)
        >>> registry.register(MyFactor)  # Raises FactorError
        >>> registry.register(MyFactor, force=True)  # Overwrites
        """
        name = factor_class.name
        logger.debug(
            "Registering factor",
            factor_name=name,
            factor_class=factor_class.__name__,
            force=force,
        )

        if name in self._factors and not force:
            logger.error(
                "Factor already registered",
                factor_name=name,
                existing_class=self._factors[name].__name__,
                new_class=factor_class.__name__,
            )
            raise FactorError(
                f"Factor '{name}' is already registered. Use force=True to overwrite.",
                details={
                    "factor_name": name,
                    "existing_class": self._factors[name].__name__,
                },
            )

        self._factors[name] = factor_class
        logger.info(
            "Factor registered",
            factor_name=name,
            category=factor_class.category.value
            if hasattr(factor_class.category, "value")
            else str(factor_class.category),
        )

    def get(self, name: str) -> type["Factor"]:
        """Retrieve a factor class by name.

        Parameters
        ----------
        name : str
            The name of the factor to retrieve.

        Returns
        -------
        type[Factor]
            The registered factor class.

        Raises
        ------
        FactorNotFoundError
            If no factor with the given name is registered.

        Examples
        --------
        >>> registry = get_registry()
        >>> factor_class = registry.get("momentum")
        >>> factor = factor_class()
        """
        logger.debug("Getting factor", factor_name=name)

        if name not in self._factors:
            logger.warning("Factor not found", factor_name=name)
            raise FactorNotFoundError(name)

        factor_class = self._factors[name]
        logger.debug(
            "Factor retrieved",
            factor_name=name,
            factor_class=factor_class.__name__,
        )
        return factor_class

    def list_by_category(self, category: FactorCategory) -> list[str]:
        """List all factor names in a specific category.

        Parameters
        ----------
        category : FactorCategory
            The category to filter by.

        Returns
        -------
        list[str]
            List of factor names in the specified category.

        Examples
        --------
        >>> registry = get_registry()
        >>> momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
        >>> print(momentum_factors)
        ['momentum_12m', 'momentum_6m']
        """
        logger.debug(
            "Listing factors by category",
            category=category.value if hasattr(category, "value") else str(category),
        )

        result = [
            name
            for name, factor_class in self._factors.items()
            if factor_class.category == category
        ]

        logger.debug(
            "Factors listed by category",
            category=category.value if hasattr(category, "value") else str(category),
            count=len(result),
        )
        return result

    def list_all(self) -> list[str]:
        """List all registered factor names.

        Returns
        -------
        list[str]
            List of all registered factor names.

        Examples
        --------
        >>> registry = get_registry()
        >>> all_factors = registry.list_all()
        >>> print(len(all_factors))
        10
        """
        result = list(self._factors.keys())
        logger.debug("Listed all factors", count=len(result))
        return result

    def clear(self) -> None:
        """Clear all registered factors from the registry.

        This method is primarily useful for testing purposes.

        Examples
        --------
        >>> registry = get_registry()
        >>> registry.clear()
        >>> len(registry.list_all())
        0
        """
        count = len(self._factors)
        self._factors.clear()
        logger.debug("Registry cleared", removed_count=count)


# Singleton instance
_registry_instance: FactorRegistry | None = None


def get_registry() -> FactorRegistry:
    """Get the singleton FactorRegistry instance.

    Returns
    -------
    FactorRegistry
        The global factor registry instance.

    Examples
    --------
    >>> registry1 = get_registry()
    >>> registry2 = get_registry()
    >>> registry1 is registry2
    True
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = FactorRegistry()
        logger.info("Singleton FactorRegistry created")
    return _registry_instance


def register_factor(cls: type[F]) -> type[F]:
    """Class decorator for registering a factor class.

    This decorator automatically registers the decorated factor class
    with the global registry.

    Parameters
    ----------
    cls : type[F]
        The factor class to register.

    Returns
    -------
    type[F]
        The same class, unchanged.

    Examples
    --------
    >>> from factor.core.registry import register_factor
    >>> from factor.core.base import Factor
    >>> from factor.enums import FactorCategory
    >>>
    >>> @register_factor
    ... class MyFactor(Factor):
    ...     name = "my_factor"
    ...     description = "My custom factor"
    ...     category = FactorCategory.VALUE
    ...     def compute(self, provider, universe, start_date, end_date):
    ...         return provider.get_prices(universe, start_date, end_date)
    """
    logger.debug(
        "Registering factor via decorator",
        class_name=cls.__name__,
        factor_name=getattr(cls, "name", "unknown"),
    )
    registry = get_registry()
    registry.register(cls)
    return cls


__all__ = [
    "FactorNotFoundError",
    "FactorRegistry",
    "get_registry",
    "register_factor",
]
