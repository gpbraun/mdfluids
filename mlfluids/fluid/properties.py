"""
MDMLPROP

Esse módulo implementa definições de propriedades termodinâmicas.

Gabriel Braun, 2025
"""

import re
from dataclasses import dataclass

import CoolProp.CoolProp as cp

from mlfluids.utils.registry import Item, Registry


@dataclass(frozen=True)
class Property(Item):
    """
    Estrutura para armazenar metadados de uma propriedade termodinâmica.
    """

    name: str | None = None
    symbol: str | None = None
    cp_index: int | None = None
    rp_label: str | None = None


class PropertyRegistry(Registry[Property]):
    """
    Registro especializado para propriedades termodinâmicas.
    """


PROPERTY_REGEX = re.compile(
    r"^(?P<prop>[A-Z0-9_]+)"  # nome base
    r"(?:\((?P<index>\d+)\))?"  # índice opcional
    r"(?P<normalized>\*)?$"  # "*" indica normalização
)
"""
Regex para o parsing das propriedades
"""


def parse_property_string(prop_str: str) -> tuple[Property, int | None, bool]:
    """
    Parse a property string that may include an index and an optional modifier.
    """
    match = PROPERTY_REGEX.match(prop_str.upper())
    if not match:
        raise ValueError(f"Invalid property string format: {prop_str}")

    groupdict = match.groupdict()
    prop_key = groupdict["prop"].upper()

    try:
        prop = PropertyRegistry.get(prop_key)
    except KeyError:
        raise ValueError(f"Propriedade não encontrada: {prop_str}")

    index = int(groupdict["index"]) if groupdict["index"] else None
    normalized = True if groupdict["normalized"] else False

    return prop, index, normalized


def _register_default_properties():
    """
    Registra as propriedades padrão usadas em termodinâmica e transporte.
    """
    PropertyRegistry.register_many(
        [
            # PROPRIEDADES REGULARES
            Property(
                key="T",
                name="temperature",
                symbol="T",
                cp_index=cp.iT,
                rp_label="T",
            ),
            Property(
                key="P",
                name="pressure",
                symbol="P",
                cp_index=cp.iP,
                rp_label="P",
            ),
            Property(
                key="D",
                name="molar density",
                symbol="\\rho",
                cp_index=cp.iDmolar,
                rp_label="D",
            ),
            # PROPRIEDADES PARA TESTE DA EOS
            Property(
                key="PIP",
                name="phase indication parameter",
                symbol="\\Pi",
                cp_index=cp.iPIP,
                rp_label="PIP",
            ),
            # PROPRIEDADES DE TRANSPORTE
            Property(
                key="VIS",
                name="shear viscosity",
                symbol="\\mu",
                cp_index=cp.iviscosity,
                rp_label="VIS",
            ),
            Property(
                key="TCX",
                name="thermal conductivity",
                symbol="\\kappa",
                cp_index=cp.iconductivity,
                rp_label="TCX",
            ),
        ]
    )


_register_default_properties()
