import numpy as np

np.random.seed(42)
import argparse
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter, TextureFilter


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=3*10**4)
    parser.add_argument("--size", type=float, default=None)
    parser.add_argument("-s", "--shader", type=str, default="sphere")

    args = parser.parse_args()

    np.random.seed(32)

    coords = np.random.uniform(-50, 50, (args.n, 3))

    coords[:, 0] *= 0.05

    if args.size is None:
        size = 5 * np.random.uniform(0.2, 1, len(coords))
        size *= (
            np.prod(coords.max(axis=0) - coords.min(axis=0)) ** (1 / 3)
            / np.mean(size)
            / len(size) ** (1 / 3)
        )
    else:
        size = args.size

    values = np.random.uniform(0.8, 1, len(coords))

    sigmas = np.ones((len(coords), 3))
    sigmas[:, 1:] *= 0.1

    rotvec = np.random.normal(0, 1, (len(coords), 3))

    rotvec = 10*coords/np.max(coords)
    

    layer = Particles(
            coords,
            size=size,
            values=values,
            rotvec=rotvec,
            colormap="Spectral",
            sigmas=sigmas,
            filter=ShaderFilter(args.shader) if args.shader != "" else None,
        )

    v = napari.Viewer()

    layer.add_to_viewer(v)

    v.window.qt_viewer.layer_to_visual[layer].node.canvas.measure_fps()

    layer.blending='opaque'
    layer.contrast_limits = (0, 1)

    v.dims.ndisplay = 3

    v.camera.perspective = 50

    napari.run()
