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
    'particle': """
            float func(vec2 x){
                float r = length(x);
                float val = .05/((max(r,.01)-0.01)+0.05);
                return val;
            }
            """,

    'airy': """
            float func(vec2 x){
                float r = 8*length(x);
                float val = abs(sin(r)/(1e-8+r));
                return val;
            }
            """,

    'fresnel': """
            float func(vec2 x){
                float r = length(x);
                float d = .7;
                float val = 1.;
                if (r>d){
                    val = exp(-4*(r-d));
                    val *= cos(1000*(r-d)*(r-d));

                }
                return val;
            }
            """,
    
    'sphere': """        
            float func(vec2 x){

                float r = length(x);
                float r0 = .8;
                if (r<r0)
                    return sqrt(r0*r0-r*r);
                else
                    discard;
            }
            """,

    'bubble': """
            float func(vec2 x){
                float r = length(x);
                float r1 = .8;
                float r2 = .9;
                if (r<r1)
                    return (sqrt(r2*r2-r*r)-sqrt(r1*r1-r*r))/sqrt(r2*r2-r1*r1);
                if (r<r2)
                    return sqrt(r2*r2-r*r)/sqrt(r2*r2-r1*r1);
                else
                    discard;
            }
            """,
    'bubble2': """
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
    def __init__(self, mode='gaussian', distance_intensity_increase=1, **kwargs):        
        kwargs.setdefault('fhook', 'post')

        fcode = Function("""
        void apply() {
            float val = $func(2*(v_texcoord-.5));

            // if particle is far away, ramp up intensity
            float infinity_raise = $distance_intensity_increase*length(fwidth(v_texcoord));
            
            gl_FragColor *= val*(1+infinity_raise);
        }""")

        if mode in _shader_functions: 
            fcode['func']=Function(_shader_functions[mode])
            fcode['distance_intensity_increase'] = 20*distance_intensity_increase
        else:
            fcode=mode

        super().__init__(fcode=fcode, **kwargs)
