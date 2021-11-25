"""

SELECT source_id, random_index, ra, dec, parallax, phot_g_mean_mag, parallax_over_error 
FROM gaiaedr3.gaia_source
WHERE random_index<10000000 AND parallax_over_error > 5

"""

import numpy as np
from pandas.core.tools.numeric import to_numeric
np.random.seed(42)
import argparse
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', type=str, default='data/gaia_mag11.csv')
    parser.add_argument('--size', type=float, default=.005)
    parser.add_argument('--sub',  type=int, default=1)
    parser.add_argument('-s','--shader',  type=str, default='particle')
    parser.add_argument('-a','--antialias',  type=float, default=0.1)
    args = parser.parse_args() 

    np.random.seed(32)


    if not 'df' in locals():
        df = pd.read_csv(args.input)
        df = df[df['parallax']>0]
        df['mag_abs'] = df['phot_g_mean_mag'] - 5*(np.log10(1000/df['parallax'])-1)
        


    df = df.iloc[::args.sub]


    phi   = df['ra'].to_numpy()/180*np.pi
    theta = df['dec'].to_numpy()/180*np.pi
    r     = 1/df['parallax'].to_numpy()

    
    bright = df['mag_abs'].to_numpy()
    mi, ma = np.percentile(bright[::10],0), np.percentile(bright[::10],99)
    # mi, ma = 6, 13
    # mi, ma = -3, 8
    bright = 1-np.clip((bright-mi)/(ma-mi),0,1)
    size=args.size
    values = bright
    
    
    
    from astropy import units
    from astropy.coordinates import SkyCoord, Galactocentric, Distance
    c = SkyCoord(ra=units.Quantity(df['ra'])*units.degree, 
                        dec=units.Quantity(df['dec'])*units.degree, 
                        distance=Distance(parallax=df['parallax'].values*units.mas))
    c_centered = c.transform_to(Galactocentric())
    coords = np.stack([c_centered.z.value, c_centered.y.value, c_centered.x.value], axis=-1)


    coords = np.stack([r*np.cos(phi)*np.cos(theta), 
                       r*np.sin(phi)*np.cos(theta),
                       r*np.sin(theta),
                       ], axis=-1)
    # orthogonal trafo into galactic coordinates
    # https://gea.esac.esa.int/archive/documentation/GDR2/Data_processing/chap_cu3ast/sec_cu3ast_intro/ssec_cu3ast_intro_tansforms.html
    A_galactic  = np.array([[-0.0548755604162154, 0.4941094278755837, -0.8676661490190047],
                [-0.8734370902348850, -0.4448296299600112, -0.1980763734312015], 
                [-0.4838350155487132, 0.7469822444972189, 0.4559837761750669]]).T                       
    coords = np.einsum('ij,kj', A_galactic, coords).T
    coords = coords[:,::-1]

    coords = coords - np.median(coords,axis=0)

    
    coords /= np.max(np.abs(np.percentile(coords, (.1,99.9), axis=0)),0, keepdims=True)
    coords = np.clip(coords,-1,1)

    layer = Particles(coords, 
        size=size, 
        values=1,
        # colormap='Spectral',
        colormap='gray',
        filter = ShaderFilter(args.shader, distance_intensity_increase=0 if args.antialias==0 else 1) if args.shader !="" else None, 
        antialias=args.antialias,
    )

    v = napari.Viewer()

    layer.contrast_limits=(0,1)

    layer.add_to_viewer(v)

    

    v.dims.ndisplay=3
    v.camera.perspective=40.0
    v.camera.angles=(0,90,0)

    napari.run()


