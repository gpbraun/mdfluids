# MLPROP

`MLPROP` provides an interface to **CoolProp** and **REFPROPdll**, allowing the user to produce large, thermodynamically self‑consistent data sets for machine‑learning applications and process analysis.

## REFPROP requirement

`MLPROP` presumes that the National Institute of Standards and Technology (NIST) **REFPROP** package is installed on the host system. The user must explicitly declare its location **before** instantiating any `Fluid` objects:

```python
from mlfluids import set_refprop_path

set_refprop_path("/home/REFPROP10")
```

## The `Fluid` class

`Fluid` encapsulates a CoolProp/REFPROP state object and exposes a high‑level API for setting thermodynamic states and evaluating native or user‑defined properties.

```python
from mlfluids import Fluid

mixture = Fluid("Nitrogen&CO2")
```

### Batch calculations over a thermodynamic state grid

The following example demonstrates how to generate a two‑property data set (density and viscosity) on a  $PT$ grid.

```python
import numpy as np
from mlfluids import Fluid

mixture = Fluid("Methane&Ethane")
mixture.set_mole_fractions([0.3, 0.7])

# Construct a Cartesian grid
T = np.linspace(200.0, 600.0, 80)
P = np.geomspace(5.0e4, 2.0e7, 100)
grid = np.stack(np.meshgrid(T, P, indexing="ij"), axis=-1).reshape(-1, 2)

# Evaluate properties on the grid
targets = ["D", "VIS"]
data = mixture.calc_states_props("T", "P", grid, targets)
```

### Normalization

Dimensionless target variables facilitate the training of many machine‑learning models.
`MLPROP` implements normalization via a **reference fluid** and a trailing asterisk in the property token:

```python
from mlfluids import Fluid

reference = Fluid("Nitrogen")
reference.set_state("T", "P", [350.0, 4.0e5])

Fluid.set_normalizing_fluid(reference)

sample = Fluid("Methane&Ethane")
sample.set_mole_fractions([0.6, 0.4])
sample.set_state("T", "P", [350.0, 4.0e5])

dimensionless_mu = sample.calc_props(["VIS*"])[0] # μ_sample / μ_reference
```

The same mechanism applies to batch queries; simply append `*` to each target key:

```python
targets = ["D*", "VIS*", "TCX*"]
rel_data = sample.calc_states_props("T", "P", grid, targets)
```

### Creating custom property handlers

The library permits the registration of additional property correlations without modifying the source code. For example, a Peng-Robinson $\kappa$ function may be introduced as follows:

```python
from mlfluids import Fluid

@Fluid.register_prop("PR_KAPPA")
def _calc_pr_kappa(self):
    omega = self.acentric_factor() # CoolProp method
    return 0.37464 + 1.54226*omega - 0.26992*omega**2
```

Thereafter, the key `"PR"` behaves identically to the built‑in properties and can be included in both scalar and batch evaluations.

