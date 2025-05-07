"""
MDMLPROP

Esse módulo implementa definições de fases para cálculo de propriedades termodinâmicas.

Gabriel Braun, 2025
"""

__all__ = [
    "PhaseRegistry",
]


from dataclasses import dataclass

import CoolProp.CoolProp as cp

from mlfluids.utils.registry import Item, Registry


@dataclass(frozen=True)
class Phase(Item):
    """
    Estrutura para armazenar metadados de uma propriedade termodinâmica.
    """

    name: str
    cp_index: int | None = None
    rp_label: str | None = None


class PhaseRegistry(Registry[Phase]):
    """
    Registro especializado para fases termodinâmicas.
    """

    @classmethod
    def get_cp_index(cls, cp_index: str) -> Phase:
        """
        Retorna: fase recuperada pelo seu índice no CoolProp.
        """
        for item in cls._registry.values():
            if item.cp_index == cp_index:
                return item
        raise KeyError(f"Índice '{cp_index}' não encontrado no registro.")


def _register_default_phases():
    """
    Registra as propriedades padrão usadas em termodinâmica e transporte.
    """
    PhaseRegistry.register_many(
        [
            Phase(
                key="liquid",
                name="liquid",
                cp_index=cp.iphase_liquid,
                rp_label="L",
            ),
            Phase(
                key="gas",
                name="gas",
                cp_index=cp.iphase_gas,
                rp_label="G",
            ),
            Phase(
                key="supercritical_gas",
                name="supercritical gas",
                cp_index=cp.iphase_supercritical_gas,
                rp_label="G",
            ),
            Phase(
                key="supercritical_liquid",
                name="supercritical liquid",
                cp_index=cp.iphase_supercritical_liquid,
                rp_label="L",
            ),
            Phase(
                key="supercritical",
                name="supercritical",
                cp_index=cp.iphase_supercritical,
            ),
            Phase(
                key="critical_point",
                name="critical point",
                cp_index=cp.iphase_critical_point,
            ),
            Phase(
                key="twophase",
                name="twophase",
                cp_index=cp.iphase_twophase,
            ),
        ]
    )


_register_default_phases()
