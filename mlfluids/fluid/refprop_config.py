"""
MDMLPROP

Esse módulo implementa funções para configuração da interface com o REFPROP.

Gabriel Braun, 2025
"""

import os

import CoolProp.CoolProp as cp
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary, REFPROPInstance

_REFPROP_PATH: str | None = None
_REFPROP_INSTANCE: REFPROPInstance | None = None


def set_refprop_path(path: str):
    """
    Atualiza: endereço do REFPROP para o cálculo de propriedades.
    """
    global _REFPROP_PATH, _REFPROP_INSTANCE

    _REFPROP_PATH = path

    # Define a variável de ambiente.
    os.environ["RPPREFIX"] = path

    # Define o diretório para os cálculos com o CoolProp.
    cp.set_config_string(cp.ALTERNATIVE_REFPROP_PATH, path)

    # Define o diretório para os cálculos com o ctREFPROP.
    _REFPROP_INSTANCE = REFPROPFunctionLibrary(path)
    _REFPROP_INSTANCE.SETPATHdll(path)


def get_refprop_path() -> str:
    """
    Retorna: diretório do REFPROP.
    """
    if _REFPROP_PATH is None:
        raise RuntimeError("O endereço do REFPROP não foi definido.")
    return _REFPROP_PATH


def get_refprop_interface() -> REFPROPInstance:
    """
    Retorna: Instância do REFPROP para o cálculo de propriedades usando o REFPROPdll.
    """
    if _REFPROP_INSTANCE is None:
        raise RuntimeError("A interface do REFPROP não foi inicializada.")
    return _REFPROP_INSTANCE
