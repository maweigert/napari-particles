import numpy as np 
from typing import Literal
from smlm_file import readSmlmFile
import pandas as pd

def coords_random(n=10**4, size = None, mode:Literal[None, 'no_z', 'small_z', 'only_2d']=None):
    coords = np.random.uniform(-100,100,(n,3))

    if mode=='no_z':
        coords[:,0] = 0
    elif mode=='small_z':
        coords[:,0] *= 0.03
    elif mode=='only_2d':
        coords = coords[:,1:]
    elif mode is None:        
        pass 
    else:
        raise NotImplementedError(mode)

    if size is None:
        size = np.random.uniform(.2,1.5, len(coords))*coords.max()/np.sqrt(len(coords))
    elif np.isscalar(size):
        size = size*np.ones(len(coords))
    intens = np.random.uniform(0.2,1, len(coords))
    return coords, size, intens 


def coords_from_smlm(fname):
    manifest, files = readSmlmFile(fname)
    prop = files[-1]['data']['tableDict']
    axis = ('y','x')
    if 'z' in prop:
        axis = ('z',) + axis
    
    coords = np.stack([prop[a] for a in axis], axis=-1)
    coords -= coords.mean(axis=0)
    size = 4*prop.get('uncertainty_xy',10)
    intens = prop.get('intensity_photon_',100)-prop.get('offset_photon_',0)
    intens = intens/np.percentile(intens[::8],90)
    return (coords, size, intens), prop


def coords_from_csv(fname, delimiter=None):
    df = pd.read_csv(fname, delimiter=delimiter)

    # standardize column names
    df = df.rename(columns={
        'x [nm]': 'xnm',
        'y [nm]': 'ynm',
        'z [nm]': 'znm',
        'uncertainty_xy [nm]': 'xnmerr',
        'uncertainty_z [nm]': 'znmerr',
        'intensity [photon]': 'phot',
    })
    
    if not 'ynmerr' in df:
        df['ynmerr'] = df['xnmerr']

    axis = ['ynm','xnm']
    if 'znm' in df.columns:
        axis = ['znm'] + axis
    
    coords = df[axis].to_numpy()
    coords -= coords.mean(axis=0)
    try:
        size = 4*df['znmerr'].to_numpy()
    except KeyError:
        print('could not get size')
        size = 10
    try:
        sigmas = df[['znmerr', 'ynmerr', 'xnmerr']].to_numpy()
    except KeyError:
        print('could not get sigmas')
        sigmas = .25*size
    
    try:
        intens = df['phot'].to_numpy()
    except KeyError:
        intens = 1/size
    
    intens = intens/np.percentile(intens[::8],95)


    return (coords, size, intens), sigmas, df




def human_format(val : int, fmt = '.1f') -> str :
    """ convert e.g. 1230 -> 1.23k """
    units = ['', 'K', 'M', 'G']
    base  = min(int(np.floor(np.log10(val)))//3, len(units))
    if base==0:
        return str(val)
    val   = val/10**(3*base)
    res = ('{{:{}}} {}'.format(fmt, units[base])).format(val)
    return res



if __name__ == "__main__":
    data = coords_from_csv('data/spectrin.csv')

