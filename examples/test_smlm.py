import numpy as np
np.random.seed(42)
import napari
from smlm_utils import human_format, coords_from_smlm, coords_random, coords_from_csv
import argparse 
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter, TextureFilter


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser() 
    parser.add_argument('-i', '--input', type=str, default=None) 
    parser.add_argument('-d', '--data', type=str, default='simple', 
        choices=['simple','simple2', 'actin2d', 'actin3d', 'spectrin','dual','mt'])
    parser.add_argument('--plain', action='store_true')
    parser.add_argument('--persp', action='store_true')
    parser.add_argument('-a', '--antialias', type=float, default=0.005)

    args = parser.parse_args() 

    if args.input is None:
        if args.data=='simple':
            data = [coords_random(100, size=10, mode='only_2d')]
        elif args.data=='simple2':
            data = [coords_random(10**5, size=None, mode='small_z')]
        elif args.data=='spectrin':
            data = [coords_from_csv('data/smlm/spectrin.csv')[0]]
        elif args.data=='mt':
            data = [coords_from_smlm('data/smlm/leterrier_mt_simple.smlm')[0]]
        elif args.data=='actin2d':
            data = [coords_from_smlm('data/smlm/leterrier_actin2d.smlm')[0]]
        elif args.data=='actin3d':
            data = [coords_from_smlm('data/smlm/leterrier_actin3d.smlm')[0]]
        elif args.data=='dual':
            data = [coords_from_csv('data/smlm/cos_clathrin.csv', delimiter='\t')[0],
                    coords_from_csv('data/smlm/cos_mt.csv', delimiter='\t')[0]]
    else:
        data = [coords_from_csv(args.input,delimiter='\t')[0]]
        
    cmaps = ('bop blue', 'bop orange', 'magenta')
    v = napari.Viewer()


    for (coords, size, values), cmap in zip(data, cmaps):
        print(f'rendering {human_format(len(coords))} particles... ')
        
        layer = Particles(coords, values=values, size=2*size, colormap=cmap,
            antialias=args.antialias, 
            filter = ShaderFilter('gaussian'), 
            )

        layer.contrast_limits=(0,1)
        layer.add_to_viewer(v)
        
    if args.persp:
        v.camera.perspective=50

    if coords.shape[1]==3:
        v.dims.ndisplay=3


    napari.run()
