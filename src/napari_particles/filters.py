"""


"""


import numpy as np 
from abc import ABC
from vispy.visuals.filters import Filter
from vispy.visuals.shaders import Function, Varying
from vispy.gloo import Texture2D, VertexBuffer

# TODO: Add mipmapping 
class TextureFilter(Filter):
    def __init__(self, texture, **kwargs):
        kwargs.setdefault('fhook', 'post')

        self._fcode = Function("""
        void apply() {
            gl_FragColor *= texture2D($u_texture, v_texcoord);
        }
        """)
        texture = np.asarray(texture).astype(np.float32)
        if not texture.ndim==3:
            raise ValueError('texure needs to be array of size (M,N,1)')
        self.texture = texture
        super().__init__(fcode=self._fcode, **kwargs)

    @property
    def texture(self):
        """The texture image."""
        return self._texture

    @texture.setter
    def texture(self, texture):
        self._texture = texture
        self._fcode['u_texture'] = Texture2D(texture)


# ShaderFilters

_shader_functions = {
    'gaussian': """
            float func(vec2 x){
                float r = 2*length(x);
                float val = exp(-r*r);
                return val;
            }
            """,
    'bubbles': """
            float func(vec2 x){
                float r = length(x);
                float r1 = .8;
                float r2 = .9;
                if (r<r1)
                    return (sqrt(r2*r2-r*r)-sqrt(r1*r1-r*r))/sqrt(r2*r2-r1*r1);
                if (r<r2)
                    return sqrt(r2*r2-r*r)/sqrt(r2*r2-r1*r1);
                else
                    return 0;
            }
            """,
    'bubbles2': """
            float func(vec2 x){
                float r = length(x);
                float r0 = .9;
                float val = exp(-400*(r-r0)*(r-r0));
                if (r<r0){
                    val = max(val,r*r/r0/r0);
                }
                return val;
            }
            """
}

class ShaderFilter(Filter):
    def __init__(self, mode='gaussian', **kwargs):        
        kwargs.setdefault('fhook', 'post')

        fcode = Function("""
        void apply() {
            float val = $func(2*(v_texcoord-.5));
            gl_FragColor *= val;
        }""")
        if mode in _shader_functions: 
            fcode['func']=Function(_shader_functions[mode])
        else:
            fcode=mode

        super().__init__(fcode=fcode, **kwargs)
