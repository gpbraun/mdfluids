"""
MDMLPROP

Esse módulo implementa uma classe para o cálculo de propriedades de fluidos.

Gabriel Braun, 2025
"""

__all__ = [
    "Fluid",
]


import re
from itertools import product
from typing import Any, Callable, ClassVar, Optional

import CoolProp.CoolProp as cp
import numpy as np
from scipy.optimize import brentq

from .phases import PhaseRegistry
from .properties import Property, PropertyRegistry, parse_property_string
from .refprop_config import get_refprop_interface


class Fluid:
    """
    Classe para cálculo de propriedades de uma mistura fluida.
    """

    _NORM_FLUID: ClassVar[Optional["Fluid"]] = None
    _PROPERTY_HANDLERS: ClassVar[dict[str, Callable]] = {}

    def __init__(
        self,
        fluid_str: str,
        # Parâmetros auxiliares
        round_decimals: int | None = 6,
    ):
        """
        Inicializa: classe 'Fluid'.
        """
        self.phase = None
        self.phase_imposed = False

        # Parâmetros de estado
        self._T = None
        self._D = None
        self._P = None

        # Parâmetros auxiliares
        self.round_decimals = round_decimals

        # Criação do estado abstrado do coolprop
        self._state = cp.AbstractState("REFPROP", fluid_str)

    def __getattr__(self, name):
        """
        Fallback: método do CoolProp AbstractState
        """
        return getattr(self._state, name)

    def is_mixture(self) -> bool:
        """
        Retorna: verdadeiro se o fluido é uma mistura.
        """
        return len(self._state.fluid_names()) > 1

    def fluid_names_rp(self) -> list[str]:
        """
        Retorna: lista de nomes compatível com o REFPROP.
        """
        return [cp.get_REFPROPname(name) for name in self.fluid_names()]

    @classmethod
    def set_normalizing_fluid(cls, fluid: "Fluid") -> None:
        """
        Define the global reference fluid used for normalization.
        """
        cls._NORM_FLUID = fluid

    @classmethod
    def get_normalizing_fluid(cls) -> "Fluid":
        """
        Returns the global reference fluid.
        Raises a ValueError if the reference fluid has not been set.
        """
        if cls._NORM_FLUID is None:
            raise ValueError(
                "Fluido de referência não definido. use 'set_reference_fluid()' primeiro."
            )
        return cls._NORM_FLUID

    def specify_phase(
        self,
        phase_key: str,
        impose: bool = False,
    ) -> None:
        """
        Atualiza: fase de referência imposta para cálculo de dados.
        """
        self.phase = PhaseRegistry.get(phase_key)
        self._state.specify_phase(self.phase.cp_index)
        if impose:
            self.phase_imposed = True

    def _calc_phase(self) -> None:
        """
        Retorna: fase da mistura fluida.
        """
        if self.phase_imposed == True:
            return
        try:
            phase = PhaseRegistry.get_cp_index(self._state.phase())
        except ValueError:
            # O REFPROP não implementa uma rotina de determinação da fase em misturas.
            # Devemos determinar a fase manualmente.
            Q = self._state.Q()
            P_r = self._state.p() / self._state.p_critical()
            T_r = self._state.T() / self._state.T_critical()

            if np.isclose(T_r, 1) and np.isclose(P_r, 1):
                phase = PhaseRegistry.get("critical_point")
            elif T_r >= 1 and P_r >= 1:
                phase = PhaseRegistry.get("supercritical")
            elif T_r > 1 and P_r < 1:
                phase = PhaseRegistry.get("supercritical_gas")
            elif T_r < 1 and P_r > 1:
                phase = PhaseRegistry.get("supercritical_liquid")
            elif Q > 1:
                phase = PhaseRegistry.get("gas")
            elif Q < 0:
                phase = PhaseRegistry.get("liquid")
            elif Q >= 0 and Q <= 1:
                phase = PhaseRegistry.get("twophase")
            else:
                raise ValueError("Erro na determinação da fase!")

        # Fase determinada. Refazer o Flash.
        self.phase = phase
        self._state.specify_phase(phase.cp_index)
        self._state.update(cp.DmolarT_INPUTS, self._state.rhomolar(), self._state.T())
        self._state.specify_phase(cp.iphase_not_imposed)

    def set_state(
        self,
        prop_str_1: str,
        prop_str_2: str,
        prop_values: list[float],
        use_guesses: bool = False,
    ) -> None:
        """
        Atualiza: EOS a partir dos valores dos parâmetros.
        """
        prop_1, _, normalized_1 = parse_property_string(prop_str_1)
        prop_2, _, normalized_2 = parse_property_string(prop_str_2)

        value_1 = prop_values[0]
        value_2 = prop_values[1]

        # Calcula o valor real das propriedades normalizadas.
        if normalized_1 or normalized_2:
            norm_fluid = self.get_normalizing_fluid()
            if normalized_1:
                value_1 *= norm_fluid._state.keyed_output(prop_1.cp_index)
            if normalized_2:
                value_2 *= norm_fluid._state.keyed_output(prop_2.cp_index)

        # Atualiza o estado das fases
        try:
            update_args = cp.generate_update_pair(
                prop_1.cp_index, value_1, prop_2.cp_index, value_2
            )
            # Flash para determinação da fase.
            if use_guesses and self._D is not None:
                guesses = cp.PyGuessesStructure()
                guesses.T = self._T
                guesses.p = self._P
                guesses.rhomolar = self._D

                self._state.update_with_guesses(*update_args, guesses)
            else:
                self._state.update(*update_args)
            self._calc_phase()

        except ValueError as e:
            if re.search(r"(2-phase|two-phase)", str(e), re.IGNORECASE):
                # Problema: Falha de convergência do flash para duas fases!
                # OBS1: normalmente ocorre com flash PT.
                # OBS2: dificuldade de alterar o MAXITER do REFPROP.
                self.specify_phase("twophase", impose=False)

                # Alternativa: usar o método de Brendt para encontrar a qualidade da mistura LV.
                # OBS3: isso nem sempre resolve o problema de convergência.
                def residual(Q):
                    _update_args = cp.generate_update_pair(
                        cp.iQ, Q, prop_1.cp_index, value_1
                    )
                    self._state.update(*_update_args)
                    return self._state.keyed_output(prop_2.cp_index) - value_2

                brentq(residual, 0.0, 1.0, xtol=1e-3)
            else:
                raise e

        # Atualiza os parâmetros de estado.
        self._T = self.T()
        self._P = self.p()
        self._D = self.rhomolar()

    @classmethod
    def register_prop(cls, key: str, *args, **kwargs):
        """
        Registra: propriedade atravéz de um Handler customizado.
        """
        prop = Property(key=key.upper(), *args, **kwargs)
        PropertyRegistry.register(prop)

        def decorator(fn):
            cls._PROPERTY_HANDLERS[key.upper()] = fn
            return fn

        return decorator

    def _calc_prop_hd(
        self,
        prop: Property,
        out_index: int | None = None,
    ) -> Any:
        """
        Retorna: propriedade calculada pelo handler definido pelo usuário.
        """
        if prop.key not in self._PROPERTY_HANDLERS:
            raise ValueError(f"Erro no cálculo da propriedade '{prop.key}'.")

        if out_index is None:
            return self._PROPERTY_HANDLERS[prop.key](self)

        return self._PROPERTY_HANDLERS[prop.key](self)[out_index]

    def _calc_prop_cp(
        self,
        prop: Property,
        out_index: int | None = None,
    ) -> float:
        """
        Retorna: propriedade calculada pelo CoolProp.
        """
        if prop.cp_index is None:
            raise ValueError(f"Erro no cálculo da propriedade '{prop.key}'.")

        if out_index is None:
            return self._state.keyed_output(prop.cp_index)

        return self._state.keyed_output(prop.cp_index)[out_index]

    def _calc_prop_rp(
        self,
        prop: Property,
        out_index: int | None = None,
    ) -> float:
        """
        Retorna: propriedade calculada pelo REFPROPdll.
        """
        if prop.rp_label is None:
            raise ValueError(f"Erro no cálculo da propriedade '{prop.key}'.")

        rp = get_refprop_interface()

        results = rp.REFPROPdll(
            ";".join(self.fluid_names_rp()),
            "TD",
            prop.rp_label + str(out_index + 1) if out_index else "",
            rp.MOLAR_BASE_SI,
            0,  # molar base
            0,  # no flags
            self.T(),
            self.rhomolar(),
            self.get_mole_fractions(),
        )
        if results.ierr > 100:
            raise ValueError(results.herr)

        return results.Output[0]

    def _calc_prop(
        self,
        prop_str: str,
    ) -> Any:
        """
        Retorna: propriedade calculada utilizando o backend adequado.
        """
        prop, out_index, normalized = parse_property_string(prop_str)

        # Se existir um handler customizado para essa propriedade, use-o.
        if prop.key in self._PROPERTY_HANDLERS:
            calc_method_name = "_calc_prop_hd"
        # Caso contrário, se houver cp_index, use CoolProp.
        elif prop.cp_index is not None:
            calc_method_name = "_calc_prop_cp"
        # Caso contrário, se houver rp_label, use REFPROPdll.
        elif prop.rp_label is not None:
            calc_method_name = "_calc_prop_rp"
        else:
            raise ValueError(f"Não foi possível calcular a propriedade '{prop.key}'.")

        # Cálculo e normalização
        value = getattr(self, calc_method_name)(prop, out_index)
        if normalized:
            norm_fluid = self.get_normalizing_fluid()
            value /= getattr(norm_fluid, calc_method_name)(prop, out_index)

        # Arredondamento opcional
        if self.round_decimals is not None and isinstance(value, float):
            value = np.round(value, decimals=self.round_decimals)

        return value

    def calc_props(
        self,
        prop_strs: list[str],
    ) -> np.ndarray:
        """
        Retorna: (np.ndarray) propriedades calculadas.
        """
        return np.array(
            [self._calc_prop(prop_str) for prop_str in prop_strs], dtype=object
        )

    def set_states_calc_props(
        self,
        prop_str_1: str,
        prop_str_2: str,
        prop_values: np.ndarray,
        target_props: list[str],
    ) -> np.ndarray:
        """
        Retorna: (np.ndarray) propriedades calculadas nos diferentes estados.
        """
        results = np.empty((len(prop_values), len(target_props)), dtype=object)

        for i, values in enumerate(prop_values):
            self.set_state(prop_str_1, prop_str_2, values, use_guesses=True)
            results[i] = self.calc_props(target_props)

        return results


@Fluid.register_prop("PHASE")
def _calc_phase(self):
    return self.phase.name
