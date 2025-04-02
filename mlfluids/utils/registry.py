"""
MDMLPROP

Esse módulo implementa uma classe para registro de constantes.

Gabriel Braun, 2025
"""

from dataclasses import dataclass
from typing import Dict, Generic, TypeVar


@dataclass(frozen=True)
class Item:
    key: str


T = TypeVar("T", bound=Item)


class Registry(Generic[T]):
    """
    Classe base para registro de constantes com um 'label' único.
    """

    _registry: Dict[str, T] = {}

    @classmethod
    def register(cls, item: T) -> None:
        """
        Registra: propriedade no sistema.
        """
        key = item.key.upper()
        if key in cls._registry:
            raise ValueError(f"'{item.key}' já está registrado.")
        cls._registry[key] = item

    @classmethod
    def register_many(cls, items: list[T]) -> None:
        """
        Registra: múltiplas propriedades no sistema.
        """
        for item in items:
            cls.register(item)

    @classmethod
    def get(cls, key: str) -> T:
        """
        Retorna: propriedade recuperada pelo seu rótulo.
        """
        try:
            return cls._registry[key.upper()]
        except KeyError:
            raise KeyError(f"'{key}' não encontrado no registro.")

    @classmethod
    def get_many(cls, keys: list[str]) -> list[T]:
        """
        Retorna: propriedades recuperadas pelos seus rótulos.
        """
        return [cls.get(key) for key in keys]

    @classmethod
    def all(cls) -> dict[str, T]:
        """
        Retorna: dicionário com todas as propriedades registradas.
        """
        return cls._registry.copy()
