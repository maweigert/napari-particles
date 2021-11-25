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
    parser.add_argument('-d','--dim',  type=int, choices=[2,3], default=3)
    parser.add_argument('-v', '--values', type=float, default=None)
    parser.add_argument('-a', '--antialias', type=int, default=1)
    args = parser.parse_args() 

    np.random.seed(32)

    coords = np.random.uniform(-10,10,(args.n,args.dim))
    if args.dim==3:
        coords[:,0] *= .1
    
    size = np.random.uniform(0.2,1,len(coords))
    size *= args.size*np.prod(coords.max(axis=0)-coords.min(axis=0))**(1/3)/np.mean(size)/len(size)**(1/3)
    size = args.size
    if args.values is None:
        args.values = np.random.uniform(0.2,1,len(coords))
    

    layer = Particles(coords, size=size, 
        values=args.values,
        colormap='bop orange',
        antialias=args.antialias, 
        filter = ShaderFilter(args.shader) if args.shader !="" else None, 
    )

    v = napari.Viewer()

    layer.contrast_limits=(0,1)

    layer.add_to_viewer(v)

    if args.dim==3:
        v.dims.ndisplay=3


    visual = layer.get_visual(v)


    v.camera.center=(3.4714992221962504e-06, 0.004604752451216498, 0.01231765490030412)
    v.camera.zoom=34.11731650145296
    v.camera.angles=(-14.376917598220158, 33.506835538300216, 141.30481201506916)
    v.camera.perspective=40.0
    layer.blending='additive'
    cam = visual.transforms.get_transform('scene', 'document')
    cam_inv = visual.transforms.get_transform('document', 'scene')

    napari.run()
