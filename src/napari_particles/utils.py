from typing import Tuple, Union
import numpy as np

from scipy.spatial.transform import Rotation

def generate_billboards_2d(coords: np.ndarray, size: Union[float, np.ndarray] =20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns (vertices, faces, texture coordinates) of a <n> standard 2D billboards of given size(s) 
    """
    verts0 = np.array([[-0.5, -0.5],
                       [0.5,  -0.5],
                       [0.5,   0.5],
                       [-0.5,  0.5]]).astype(np.float32)

    n = len(coords) 

    if np.isscalar(size):
        size = np.ones(n)*size
    else:
        size = np.asarray(size)

    assert len(size)==n and size.ndim==1

    verts = size[:,np.newaxis, np.newaxis]*verts0[np.newaxis]
    verts = verts.reshape((-1,verts.shape[-1]))

    # add time/z dimensions if present
    
    if coords.shape[1]>2:
        coords = np.repeat(coords, 4, axis=0) 
        verts = np.concatenate([coords[:,:-2], verts], axis=-1)
        

    texcoords0 = np.array([[0, 0],
                           [1, 0],
                           [1, 1],
                           [0, 1]]).astype(np.float32)
    
    texcoords = np.tile(texcoords0,(n,1))
    
    faces = np.tile(np.array([[0,1,2],[0,3,2]]),(n,1))
    faces = faces+np.repeat(np.repeat(4*np.arange(n)[:,np.newaxis],3,axis=-1),2 ,axis=0)
    return verts, faces, texcoords



def unit_quat_random(n:int) -> np.ndarray:
    """generate array of random unit quaternions representing rotations (only spatial part)"""
    # q = np.random.normal(0,1,(n,4))
    # q = q/np.linalg.norm(q, axis=-1, keepdims=True)
    q = Rotation.random(n).as_quat()
    return q[:,1:]

def _unit_quat_3to4(p: np.ndarray) -> np.ndarray:
    w = np.sqrt(1-np.sum(p**2, axis=-1, keepdims=True))
    return np.concatenate((w,p), axis=-1)

def unit_quat_scale(p: np.ndarray, scale: float = 1) -> np.ndarray:
    pp = Rotation.from_quat(_unit_quat_3to4(p))
    qq = Rotation.from_quat(_unit_quat_3to4(q))
    r = Rotation.concatenate((pp,qq)).as_quat()
    return r[:,1:]


def unit_quat_multiply(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    pp = Rotation.from_quat(_unit_quat_3to4(p))
    qq = Rotation.from_quat(_unit_quat_3to4(q))
    r = Rotation.concatenate((pp,qq)).as_quat()
    return r[:,1:]


def rotvec_to_quatvec(p: np.ndarray):
    return Rotation.from_rotvec(p).as_quat()[:,1:]


# def unit_quaternion_multiply(p: np.ndarray, q: np.ndarray) -> np.ndarray:
#     assert p.shape==q.shape and p.ndim==2 and p.shape[1] == 3
#     x0, y0, z0 = p.T
#     w0 = np.sqrt(1-np.linalg.sum(p**2, axis=-1))
#     x1, y1, z1 = q.T
#     w1 = np.sqrt(1-np.linalg.sum(q**2, axis=-1))
#     return np.stack([x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
#                      -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
#                      x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0], axis=-1)

# def unit_quaternion_angle(x: np.ndarray) -> np.ndarray:



if __name__ == "__main__":
    coords = np.random.uniform(0,1,(4,3))

    verts, faces, texc = generate_billboards_2d(coords, size=1)

    print(verts.shape)
    