# napari-particles (WIP)

A particle layer for napari (super rough draft)

----------------------------------


## Installation

Clone the repo and install 

```
git clone git@github.com:maweigert/napari-particles.git
pip install napari-particles/
```

## Usage


```python
import numpy as np
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter

coords = np.random.randint(0,100,(1000,3))
size   = np.random.uniform(3, 9, len(coords))
values = np.random.uniform(0.2,1, len(coords))

layer = Particles(coords, 
                size=size, 
                values=values,
                colormap='Spectral',
                filter = ShaderFilter('gaussian'))

layer.contrast_limits=(0,1)
v = napari.Viewer()
layer.add_to_viewer(v)
v.dims.ndisplay=3

napari.run()
```

<img width="683" alt="im2" src="https://user-images.githubusercontent.com/11042162/144323947-1636abc1-27b2-431d-a5f5-1e67b72b2071.png">


## Examples Scripts

in `./examples`

### Basic 

```
python test_particles.py
```


### SMLM

If you have a localization csv file in the following format (with "\t" as separator)

```
"frame" "x [nm]"        "y [nm]"        "z [nm]"        "uncertainty_xy [nm]"   "uncertainty_z [nm]"
2       23556.7 2045    -97     2.5     5
2       5871.4  2853.1  -306    2.2     4.5
2       24767.5 3298    -267    1.7     3.5
2       22070.8 3502.8  -334    1       2
....
```


you can render it like so:

```
python test_smlm.py -i data.csv
```
