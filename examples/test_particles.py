import numpy as np
np.random.seed(42)
import argparse
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter, TextureFilter


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, default=10**4)
    parser.add_argument('--size', type=float, default=.5)
    parser.add_argument('-s','--shader',  type=str, default='gaussian')
    parser.add_argument('--cmap',  type=str, default='Spectral')
    parser.add_argument('-d','--dim',  type=int, choices=[2,3], default=3)
    parser.add_argument('-v', '--values', type=float, default=None)
    parser.add_argument('-a', '--antialias', type=float, default=0)
    parser.add_argument('--persp', action='store_true')
    parser.add_argument('--vol', action='store_true')
    parser.add_argument('--points', action='store_true')

    args = parser.parse_args() 

    np.random.seed(32)

    coords = np.random.uniform(0,50,(args.n,args.dim))

    coords[:100] = np.random.uniform(24,26,(100,args.dim))

    if args.dim==3:
        coords[:,0] *= .1
    
    size = .4*np.random.uniform(0.2,1,len(coords))
    size *= size*np.prod(coords.max(axis=0)-coords.min(axis=0))**(1/3)/np.mean(size)/len(size)**(1/3)

    if args.values is None:
        args.values = np.random.uniform(0.1,1,len(coords))
    

    v = napari.Viewer()

    if args.points:
        layer = v.add_points(coords, size=size)
        v.layers[-1].blending='additive'
    else:
        layer = Particles(coords, size=size, 
        values=args.values,
        colormap=args.cmap,
        antialias=args.antialias, 
        filter = ShaderFilter(args.shader) if args.shader !="" else None, 
        )
        layer.add_to_viewer(v)

    
    if args.vol:
        vol = np.einsum('i,jk', np.ones(20), np.random.randint(0,50,(50,50))==0)
        _im = v.add_image(vol)
        _im.opacity=.3

    layer.contrast_limits=(0,1)

    

    if args.dim==3:
        v.dims.ndisplay=3



    if args.persp:
        v.camera.perspective=50

    napari.run()
