"""
A billboarded particle layer with texture/shader support

"""

from typing import Optional, Union
import numpy as np
from abc import ABC
from collections.abc import Iterable
from napari.layers import Surface
from napari.layers.utils.layer_utils import calc_data_range

from .utils import generate_billboards_2d
from .billboards_filter import BillboardsFilter
from .filters import ShaderFilter, _shader_functions
from .utils import rotvec_to_quatvec

class Particles(Surface):
    """Billboarded particle layer that renders camera facing quads of given size
    Can be combined with other (e.g. texture) filter to create particle systems etc
    """

    def __init__(
        self,
        coords: np.ndarray,
        size: Union[float, np.ndarray] = 10,
        sigmas: Union[float, tuple, np.ndarray] = (1, 1, 1),
        rotvec: Union[tuple, np.ndarray] = (1,0,0),
        values: Union[float, np.ndarray] = 1,
        filter: ShaderFilter = ShaderFilter("gaussian"),
        
        antialias: bool = False,
        **kwargs,
    ):
        """Creates a particle layer from coordinates

        Parameters
        ----------
        coords : np.ndarray
            the 3d coordinates of the center of the particles, array of shape (N, 3)
        size : Union[float, np.ndarray], optional
            the size of the particles, by default 10
        sigmas : Union[float, tuple, np.ndarray], optional
            the sigmas, by default (1, 1, 1)
        rotvec : Union[tuple, np.ndarray], optional
            3 dimensional rotation axis, its norm is the amount of rotation
        values : Union[float, np.ndarray], optional
            values for each particle (used for determining the color), by default 1
        filter : ShaderFilter, optional
            the shader to be used, by default ShaderFilter("gaussian")
        antialias : bool, optional
            by default False
        """
        kwargs.setdefault("shading", "none")
        kwargs.setdefault("blending", "additive")

        coords = np.asarray(coords)
        sigmas = np.asarray(sigmas, dtype=np.float32)
        rotvec = np.asarray(rotvec, dtype=np.float32)

        if np.isscalar(values):
            values = values * np.ones(len(coords))

        values = np.broadcast_to(values, len(coords))
        size = np.broadcast_to(size, len(coords))

        sigmas = np.broadcast_to(sigmas, (len(coords), 3))
        rotvec = np.broadcast_to(rotvec, (len(coords), 3))


        if not coords.ndim == 2:
            raise ValueError(f"coords should be of shape (M,D)")

        if not len(size) == len(coords) == len(sigmas):
            raise ValueError()

        # add dummy z if 2d coords
        if coords.shape[1] == 2:
            coords = np.concatenate([np.zeros((len(coords), 1)), coords], axis=-1)

        assert coords.shape[-1] == sigmas.shape[-1] == 3

        vertices, faces, texcoords = generate_billboards_2d(coords, size=size)

        # repeat values for each 4 vertices
        centercoords = np.repeat(coords, 4, axis=0)
        sigmas = np.repeat(sigmas, 4, axis=0)
        rotvec = np.repeat(rotvec, 4, axis=0)
        values = np.repeat(values, 4, axis=0)
        self._coords = coords
        self._centercoords = centercoords
        self._sigmas = sigmas
        self.rotvec = rotvec
        # self._orient = orient
        self._size = size
        self._texcoords = texcoords
        self._billboard_filter = BillboardsFilter(antialias=antialias)
        self.filter = filter
        self._viewer = None
        super().__init__((vertices, faces, values), **kwargs)

    def _set_view_slice(self):
        """Sets the view given the indices to slice with."""
        super()._set_view_slice()
        self._update_billboard_filter()

    def _update_billboard_filter(self):
        faces = self._view_faces.flatten()
        if self._billboard_filter._attached and len(faces) > 0:
            self._billboard_filter.texcoords = self._texcoords[faces]
            self._billboard_filter.centercoords = self._centercoords[faces][:, -3:]
            self._billboard_filter.sigmas = self._sigmas[faces][:, -3:]
            self._billboard_filter.quatvec = self._quatvec[faces][:, -3:]
        
    @property
    def rotvec(self):        
        return self._rotvec

    @rotvec.setter
    def rotvec(self, value):        
        self._rotvec = value
        self._quatvec = rotvec_to_quatvec(self._rotvec)
        return self._rotvec


    @property
    def filter(self):
        """The filter property."""
        return self._filter

    @filter.setter
    def filter(self, value):
        if value is None:
            value = ()
        elif not isinstance(value, Iterable):
            value = (value,)
        self._filter = tuple(value)

    @property
    def _extent_data(self) -> np.ndarray:
        """Extent of layer in data coordinates.
        Returns
        -------
        extent_data : array, shape (2, D)
        """
        if len(self._coords) == 0:
            extrema = np.full((2, self.ndim), np.nan)
        else:
            size = np.repeat(self._size[:, np.newaxis], self.ndim, axis=-1)
            size[:, :-2] *= 0
            maxs = np.max(self._coords + 0.5 * size, axis=0)
            mins = np.min(self._coords - 0.5 * size, axis=0)
            extrema = np.vstack([mins, maxs])
        return extrema

    @property
    def shading(self):
        return str(self._shading)

    @shading.setter
    def shading(self, shading):
        self._shading = shading
        self._detach_filter()
        self.filter = ShaderFilter(shading)
        self._attach_filter()


    @property
    def gamma(self):
        return self._gamma

    @gamma.setter
    def gamma(self, gamma):
        # just a little hack to add random rotations
        if not hasattr(self, '_tmp_rotvec0'):
            self._tmp_rotvec0 = self.rotvec.copy() 

        self.rotvec = self._tmp_rotvec0 * (gamma-1)
        self._update_billboard_filter()
        self.refresh()

    def _detach_filter(self):
        for f in self.filter:
            self._visual.detach(f)

    def _attach_filter(self):
        for f in self.filter:
            self._visual.attach(f)

    def get_visual(self, viewer):
        return viewer.window.qt_viewer.layer_to_visual[self].node

    def add_to_viewer(self, viewer):
        self._viewer = viewer
        self._viewer.add_layer(self)
        self._visual = self.get_visual(viewer)

        self._visual.attach(self._billboard_filter)
        self._update_billboard_filter()
        self._attach_filter()

        # update combobox
        shading_ctrl = self._viewer.window.qt_viewer.controls.widgets[self]
        combo = shading_ctrl.shadingComboBox

        

        combo.clear()
        for k in _shader_functions.keys():
            combo.addItem(k, k)
