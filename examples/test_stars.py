import numpy as np
from pandas.core.tools.numeric import to_numeric
np.random.seed(42)
import argparse
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter
import pandas as pd


def norm_clip(x, pmin=0.1, pmax=99.9):
    bounds = np.max(np.abs(np.percentile(x, (pmin, pmax), axis=0)),0) 
    bounds = np.stack([-bounds, bounds])
    x = np.clip(x, *bounds)
    x = x/np.max(bounds)
    return x 


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument('-i','--input', type=str, default='data/stars/galaxy_200kparticles.dat')
    parser.add_argument('-i','--input', type=str, default='data/stars/gaiasky_basedata.csv')
    parser.add_argument('--size', type=float, default=.005)
    parser.add_argument('--sub',  type=int, default=1)
    parser.add_argument('-s','--shader',  type=str, default='particle')
    parser.add_argument('-a','--antialias',  type=float, default=0.05)
    parser.add_argument('--points', action='store_true')
    args = parser.parse_args() 

    np.random.seed(32)

    
    for sep in (',', " ", "\t"):
        try:
            df = pd.read_csv(args.input, delimiter=sep, comment='#')
            df = df[df.columns[:4]]
            df.columns=["x","y","z","r"]
            break
        except Exception as e:
            print(e)
            continue
    
    df = df.dropna()
    # df = df[df.x.abs()<1e10]
    # df = df[df.y.abs()<1e10]
    # df = df[df.z.abs()<1e10]

    df = df.iloc[::args.sub]


    coords = df[["x","y","z"]].to_numpy()

    print(f'rendering {len(coords)} objects')

    coords = coords - np.median(coords,axis=0)

    
    coords = norm_clip(coords)
    

    rad = np.maximum(0,df['r'].to_numpy())
    rad /= np.max(np.abs(np.percentile(rad, (.01,99.99), axis=0)),0, keepdims=True)

    size   = args.size
    values = rad

    v = napari.Viewer()

    if args.points:
        v.add_points(coords, size=size)
        v.layers[-1].blending='additive'
    else:
        layer = Particles(coords, 
            size=size, 
            values=values,
            colormap='Spectral',
            filter = ShaderFilter(args.shader, distance_intensity_increase=args.antialias) if args.shader !="" else None, 
            antialias=args.antialias,
        )


        layer.contrast_limits=(0,1)

        layer.add_to_viewer(v)


    v.dims.ndisplay=3
    v.camera.perspective=80.0
    v.camera.angles=(90,0, 0)

    napari.run()


