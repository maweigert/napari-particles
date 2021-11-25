import numpy as np
from pandas.core.tools.numeric import to_numeric
np.random.seed(42)
import argparse
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter
import pandas as pd
from csbdeep.utils import normalize

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', type=str, default='data/galaxy_200kparticles.dat')
    parser.add_argument('--size', type=float, default=.015)
    parser.add_argument('--sub',  type=int, default=1)
    parser.add_argument('-s','--shader',  type=str, default='particle')
    parser.add_argument('-a','--antialias',  type=float, default=0.05)
    args = parser.parse_args() 

    np.random.seed(32)

    
    for sep in (',', " ", "\t"):
        try:
            print(sep)
            df = pd.read_csv(args.input, delimiter=sep)
            df = df[df.columns[:4]]
            df.columns=["x","y","z","r"]
            break
        except Exception as e:
            print(e)
            continue
    
    coords = df[["x","y","z"]].to_numpy()
    
    diam = df['r'].to_numpy() 
    if diam.max()>diam.min():
        diam = normalize(diam, clip=True)

    size   = args.size*diam
    values = diam 

    layer = Particles(coords, 
        size=size, 
        values=values,
        colormap='Spectral',
        filter = ShaderFilter(args.shader, distance_intensity_increase=args.antialias) if args.shader !="" else None, 
        antialias=args.antialias,
    )

    v = napari.Viewer()

    layer.contrast_limits=(0,1)

    layer.add_to_viewer(v)


    v.dims.ndisplay=3
    v.camera.perspective=40.0
    v.camera.angles=(90,0, 0)

    napari.run()


