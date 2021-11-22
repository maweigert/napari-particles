"""
A billboarded mesh layer with texture support

Consists of 

Billboards layer class
and 

todo:

- intensity modulation / cmap 

"""

import numpy as np 
from abc import ABC
from napari.layers import Surface
from napari.layers.utils.layer_utils import calc_data_range
from vispy.visuals.filters import Filter
from vispy.visuals.shaders import Function, Varying
from vispy.gloo import Texture2D, VertexBuffer

from .utils import generate_billboards_2d


class BillboardsFilter(Filter):
    """ Billboard geometry filter (transforms vertices to always face camera) 
    """
    def __init__(self):
        vfunc = Function("""
        void apply(){
            
            // eye coordinates of the (constant) particle squad, e.g. [5,5] for size 5 
            vec4 pos = $transform_inv(gl_Position);
            vec2 tex = $texcoords;

            //$camera(pos);
            vec3 camera_right = $camera_inv(vec4(1,0,0,0)).xyz;
            vec3 camera_up    = $camera_inv(vec4(0,1,0,0)).xyz;

            // when particles become too small, lock texture size and apply antialiasing (only used when antialias=1)
            // decrease this value to increase antialiasing
            float len_cutoff = .1 * max(abs(pos.x), abs(pos.y)) ;                     
            
            float len = length(camera_right);

            camera_right = normalize(camera_right);
            camera_up    = normalize(camera_up);

            vec3 pos_real  = $vertex_center.xyz + camera_right*pos.x + camera_up*pos.y;
            gl_Position = $transform(vec4(pos_real, 1.0));
            
            $v_texcoords = tex;
            }
        """)

        ffunc = Function("""
        void apply() {   
            $texcoords;         
        }
        """)

        self._texcoord_varying = Varying('v_texcoord', 'vec2')
        vfunc['v_texcoords'] = self._texcoord_varying
        ffunc['texcoords'] = self._texcoord_varying
        
        self._texcoords_buffer = VertexBuffer(
            np.zeros((0, 2), dtype=np.float32)
        )
        vfunc['texcoords'] = self._texcoords_buffer

        
        self._centercoords_buffer = VertexBuffer(
            np.zeros((0, 3), dtype=np.float32))

        vfunc['vertex_center'] = self._centercoords_buffer

        super().__init__(vcode=vfunc, vhook='post',fcode=ffunc, fhook='post')

        

    @property
    def centercoords(self):
        """The vertex center coordinates as an (N, 3) array of floats."""
        return self._centercoords

    @centercoords.setter
    def centercoords(self, centercoords):
        self._centercoords = centercoords
        self._update_coords_buffer(centercoords)

    def _update_coords_buffer(self, centercoords):
        if not self._attached or self._visual is None:
            return
        print('setting coords', centercoords.shape)
        self._centercoords_buffer.set_data(centercoords[:,::-1], convert=True)

    @property
    def texcoords(self):
        """The texture coordinates as an (N, 2) array of floats."""
        return self._texcoords

    @texcoords.setter
    def texcoords(self, texcoords):
        self._texcoords = texcoords
        self._update_texcoords_buffer(texcoords)

    def _update_texcoords_buffer(self, texcoords):
        if not self._attached or self._visual is None:
            return
        print('setting texture coords', texcoords.shape)
        self._texcoords_buffer.set_data(texcoords[:,::-1], convert=True)

    def _attach(self, visual):
        tr = visual.transforms.get_transform()
        self.vshader['transform'] = tr
        self.vshader['transform_inv'] = tr.inverse
        self.vshader['camera_inv'] = visual.transforms.get_transform('document', 'scene')
        self.vshader['camera'] = visual.transforms.get_transform('scene', 'document')
        super()._attach(visual)
        

class Billboards(Surface):
    """ Billboards Layer that renders camera facing quads of given size
        Can be combined with other (e.g. texture) filter to create particle systems etc 
    """
    def __init__(self, coords, size=10, values=1, filters=None, **kwargs):

        kwargs.setdefault('shading', 'none')
        kwargs.setdefault('blending', 'additive')
        
        coords = np.asarray(coords)   
        if np.isscalar(values):
            values = values * np.ones(len(coords))
        if np.isscalar(size):
            size = size * np.ones(len(coords))        

        if not coords.ndim == 2 :
            raise ValueError(f'coords should be of shape (M,D)')
    
        # add dummy z if 2d coords 
        if coords.shape[1] == 2:
            coords = np.concatenate([np.zeros((len(coords),1)), coords], axis=-1)

        vertices, faces, texcoords = generate_billboards_2d(coords, size=size)        
        
        # repeat values for each 4 vertices
        centercoords = np.repeat(coords, 4, axis=0)
        values = np.repeat(values, 4, axis=0)
        self._coords = coords
        self._centercoords = centercoords
        self._size = size
        self._texcoords = texcoords 
        self._billboard_filter = BillboardsFilter()
        self._other_filters = filters if filters is not None else ()
        super().__init__((vertices, faces, values), **kwargs)

    def _set_view_slice(self):
        """Sets the view given the indices to slice with."""
        super()._set_view_slice()
        self._update_billboard_filter()

    def _update_billboard_filter(self):
        if self._billboard_filter._attached:
            faces = self._view_faces.flatten()
            self._billboard_filter.texcoords    = self._texcoords[faces]
            self._billboard_filter.centercoords = self._centercoords[faces][:,-3:]


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
            size = np.repeat(self._size[:,np.newaxis], self.ndim, axis=-1)
            size[:,:-2] *=0
            maxs = np.max(self._coords+.5*size, axis=0)
            mins = np.min(self._coords-.5*size, axis=0)
            extrema = np.vstack([mins, maxs])
        return extrema

    def get_visual(self, viewer):
        return viewer.window.qt_viewer.layer_to_visual[self].node

    def add_to_viewer(self, viewer):
        viewer.add_layer(self)
        visual = self.get_visual(viewer)
        visual.attach(self._billboard_filter)
        self._update_billboard_filter()

        for f in self._other_filters:
            visual.attach(f)
        



if __name__ == "__main__":
    layer = Billboards()