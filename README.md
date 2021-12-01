# napari-particles (WIP)

A particle layer for napari (super rough draft)

----------------------------------


## Installation

Clone the repo and install 

```
git clone git@github.com:maweigert/napari-particles.git
pip install napari-particles/
```


## Examples

### Basic

```
cd examples

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
cd examples

python test_smlm.py -i data.csv
```
