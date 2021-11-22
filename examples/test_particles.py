import numpy as np
np.random.seed(42)
import argparse
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter, TextureFilter


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, default=10**4)
    parser.add_argument('-s','--shader',  type=str, default='gaussian')
    parser.add_argument('-d','--dim',  type=int, choices=[2,3], default=3)
    args = parser.parse_args() 

    np.random.seed(32)

    coords = np.random.uniform(-10,10,(args.n,args.dim))
    if args.dim==3:
        coords[:,0] *= .1
    
    size = np.random.uniform(0.2,1,len(coords))
    size *= .5*np.prod(coords.max(axis=0)-coords.min(axis=0))**(1/3)/np.mean(size)/len(size)**(1/3)
    values = np.random.uniform(0.2,1,len(coords))

    layer = Particles(coords, size=size, 
        values=values,
        colormap='bop blue',
        filter = ShaderFilter(args.shader) if args.shader !="" else None, 
    )

    v = napari.Viewer()

    layer.contrast_limits=(0,1)

    layer.add_to_viewer(v)

    if args.dim==3:
        v.dims.ndisplay=3

    napari.run()
