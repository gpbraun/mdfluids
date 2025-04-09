import numpy as np

from mlfluids import Fluid, set_refprop_path

set_refprop_path("/home/braun/Documents/Developer/REFPROP10")


# mixture = "Air"
mixture = "CO2&H2S"

X = 0.5

# FLUIDO DE NORMALIZAÇÃO
norm_fluid = Fluid(mixture)
norm_fluid.set_mole_fractions([X, 1 - X])
norm_fluid.set_state(
    "T", "D", [norm_fluid.T_critical(), norm_fluid.rhomolar_critical()]
)

Fluid.set_normalizing_fluid(norm_fluid)

# FLUIDO DE ANÁLISE
fluid = Fluid(mixture)
fluid.set_mole_fractions([X, 1 - X])
fluid.set_state("T*", "P*", [2.0, 2.0])

# CÁLCULO DE PARÂMETROS
P_vals = np.geomspace(1.05, 20, 100)
T_vals = np.geomspace(0.3, 0.95, 100)

Pv, Tv = np.meshgrid(P_vals, T_vals, indexing="ij")

results = fluid.set_states_calc_props(
    "P*",
    "T*",
    np.column_stack((Pv.ravel(), Tv.ravel())),
    ["PHASE", "P*", "T*", "VIS*", "TCX*"],
)

print(results)
print(len(results))
