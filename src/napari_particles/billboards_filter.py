import numpy as np
from vispy.visuals.filters import Filter
from vispy.visuals.shaders import Function, Varying
from vispy.gloo import VertexBuffer



quat_mult = Function("""
    vec4 quaternion_mult(vec4 p, vec4 q){

        float s = p.w*q.w - dot(p.xyz, q.xyz); 
        vec3 r = p.w*q.xyz + q.w*p.xyz + cross(p.xyz, q.xyz);
        return float4(s, r.xyz);
        
    }
    """)


quaternion_rot3 = Function("""
    // https://fgiesen.wordpress.com/2019/02/09/rotating-a-single-vector-using-a-quaternion/
    vec3 quaternion_rot3(vec4 q, vec3 r){

        vec3 t = 2*cross(q.xyz, r);
        return r + q.w*t + cross(q.xyz, t);
    }
    """)

quaternion_rot4 = Function("""
    vec4 quaternion_rot4(vec4 q, vec4 r){

        vec3 t = 2*cross(q.xyz, r.xyz);
        return vec4(r.xyz + q.w*t + cross(q.xyz, t), 0);
    }
    """)

quaternion_mat3 = Function("""
    mat3 quaternion_mat3(vec4 q){

    float x2 = q.x * q.x; 
    float y2 = q.y * q.y; 
    float z2 = q.z * q.z; 
    float xy = q.x * q.y; 
    float xz = q.x * q.z; 
    float yz = q.y * q.z; 
    float wx = q.w * q.x; 
    float wy = q.w * q.y; 
    float wz = q.w * q.z;

    return mat3( 1. - 2. * (y2 + z2), 2. * (xy - wz), 2. * (xz + wy), 
                2. * (xy + wz), 1. - 2. * (x2 + z2), 2. * (yz - wx), 
                2. * (xz - wy), 2. * (yz + wx), 1. - 2. * (x2 + y2));
    }
    """)

quaternion_mat4 = Function("""
    mat4 quaternion_mat4(vec4 q){

    float x2 = q.x * q.x; 
    float y2 = q.y * q.y; 
    float z2 = q.z * q.z; 
    float xy = q.x * q.y; 
    float xz = q.x * q.z; 
    float yz = q.y * q.z; 
    float wx = q.w * q.x; 
    float wy = q.w * q.y; 
    float wz = q.w * q.z;


    return mat4( 1. - 2. * (y2 + z2), 2. * (xy - wz), 2. * (xz + wy), 0., 
                2. * (xy + wz), 1. - 2. * (x2 + z2), 2. * (yz - wx), 0., 
                2. * (xz - wy), 2. * (yz + wx), 1. - 2. * (x2 + y2), 0., 
                0., 0., 0., 1.);

    }
    """)

class BillboardsFilter(Filter):
    """Billboard geometry filter (transforms vertices to always face camera)"""

    def __init__(self, antialias=0):
        vmat_inv = Function(
            """ 
            mat2 inverse(mat2 m) {
                return mat2(m[1][1],-m[0][1],-m[1][0], m[0][0]) / (m[0][0]*m[1][1] - m[0][1]*m[1][0]);
            }
        """
        )

        vfunc = Function(
            """
        varying float v_z_center;
        varying float v_scale_intensity;
        varying mat2 covariance_inv;

        void apply(){            
            // original world coordinates of the (constant) particle squad, e.g. [5,5] for size 5 
            vec4 pos = $transform_inv(gl_Position);

            pos.z *= pos.w; 

            float quat_w = length($quatvec);
            quat_w = sqrt(1-quat_w*quat_w);
            vec4 quat = vec4($quatvec,quat_w);

            

            //quat = vec4(0,0,.7,.7);

            mat4 quatmat = $quaternion_mat4(quat);
            
            //dummy 
            $quaternion_rot3(quat, vec3(0));
            $quaternion_rot4(quat, vec4(0));
            $quaternion_mat3(quat);
            $quaternion_mat4(quat);

            vec2 tex = $texcoords;

            mat4 cov = mat4(1.0);            
            
            cov[0][0] = sqrt($sigmas[0]);
            cov[1][1] = sqrt($sigmas[1]);
            cov[2][2] = sqrt($sigmas[2]);

            cov = transpose(quatmat)*cov*quatmat;

            
            vec4 ex = vec4(1,0,0,0);
            vec4 ey = vec4(0,1,0,0);
            vec4 ez = vec4(0,0,1,0);


            // get new inverse covariance matrix (for rotating a gaussian)
            vec3 ex2 = $camera(cov*$camera_inv(ex)).xyz;
            vec3 ey2 = $camera(cov*$camera_inv(ey)).xyz;
            vec3 ez2 = $camera(cov*$camera_inv(ez)).xyz;

            mat3 Rmat = mat3(ex2, ey2, ez2);
            covariance_inv = mat2(transpose(Rmat)*mat3(cov)*Rmat);
            covariance_inv = $inverse(covariance_inv);

    
            // get first and second column of view (which is the inverse of the camera) 
            vec3 camera_right = $camera_inv(vec4(1,0,0,0)).xyz;
            vec3 camera_up    = $camera_inv(vec4(0,1,0,0)).xyz;

            // when particles become too small, lock texture size and apply antialiasing (only used when antialias=1)
            // decrease this value to increase antialiasing
            //float dist_cutoff = .2 * max(abs(pos.x), abs(pos.y));

            // increase this value to increase antialiasing
            float dist_cutoff = $antialias;                                          
            
            float len = length(camera_right);

            //camera_right = normalize(camera_right);
            //camera_up    = normalize(camera_up);

            camera_right = camera_right/len;
            camera_up    = camera_up/len;                      

            vec4 p1 = $transform(vec4($vertex_center.xyz + camera_right*pos.x + camera_up*pos.y, 1.));
            vec4 p2 = $transform(vec4($vertex_center,1));
            float dist = length(p1.xy/p1.w-p2.xy/p2.w); 

            
            // if antialias and far away zoomed out, keep sprite size constant and shrink texture...
            // else adjust sprite size 
            if (($antialias>0) && (dist<dist_cutoff)) {
                
                float scale = dist_cutoff/dist;
                tex = .5+(tex-.5)*clamp(scale,1,10);
                
                camera_right = camera_right*scale;
                camera_up    = camera_up*scale;
                v_scale_intensity = scale;
                
            }
            vec3 pos_real  = $vertex_center.xyz + camera_right*pos.x + camera_up*pos.y;
            gl_Position = $transform(vec4(pos_real, 1.));            
            vec4 center = $transform(vec4($vertex_center,1));
            v_z_center = center.z/center.w;


            // flip tex coords neccessary since 0.4.13 and vispy bump
            // TODO: investigate  
            
            $v_texcoords = vec2(tex.y, tex.x);

            }
        """
        )

        ffunc = Function(
            """
        varying float v_scale_intensity;
        varying float v_z_center;
        
        void apply() {   
            gl_FragDepth = v_z_center;
            $texcoords;
        }
        """
        )

        self._texcoord_varying = Varying("v_texcoord", "vec2")
        vfunc["inverse"] = vmat_inv
        vfunc["v_texcoords"] = self._texcoord_varying
        ffunc["texcoords"] = self._texcoord_varying

        self._texcoords_buffer = VertexBuffer(np.zeros((0, 2), dtype=np.float32))
        vfunc["texcoords"] = self._texcoords_buffer
        vfunc["antialias"] = float(antialias)

        self._centercoords_buffer = VertexBuffer(np.zeros((0, 3), dtype=np.float32))
        self._sigmas_buffer = VertexBuffer(np.zeros((0, 3), dtype=np.float32))
        self._quatvec_buffer = VertexBuffer(np.zeros((0, 3), dtype=np.float32))

        vfunc["vertex_center"] = self._centercoords_buffer
        vfunc["sigmas"] = self._sigmas_buffer
        vfunc["quatvec"] = self._quatvec_buffer
        vfunc["quaternion_rot3"] = quaternion_rot3
        vfunc["quaternion_rot4"] = quaternion_rot4
        vfunc["quaternion_mat3"] = quaternion_mat3
        vfunc["quaternion_mat4"] = quaternion_mat4

        super().__init__(vcode=vfunc, vhook="post", fcode=ffunc, fhook="post")

    @property
    def centercoords(self):
        """The vertex center coordinates as an (N, 3) array of floats."""
        return self._centercoords

    @centercoords.setter
    def centercoords(self, centercoords):
        self._centercoords = centercoords
        self._update_coords_buffer(centercoords)

    def _update_coords_buffer(self, centercoords):
        if self._attached and self._visual is not None:
            self._centercoords_buffer.set_data(centercoords[:, ::-1], convert=True)

    @property
    def sigmas(self):
        """The vertex center coordinates as an (N, 3) array of floats."""
        return self._sigmas

    @sigmas.setter
    def sigmas(self, sigmas):
        self._sigmas = sigmas
        self._update_sigmas_buffer(sigmas)

    def _update_sigmas_buffer(self, sigmas):
        if self._attached and self._visual is not None:
            self._sigmas_buffer.set_data(sigmas[:, ::-1], convert=True)

    @property
    def quatvec(self):
        return self._quatvec

    @quatvec.setter
    def quatvec(self, quatvec):
        self._quatvec = quatvec
        self._update_quatvec_buffer(quatvec)

    def _update_quatvec_buffer(self, quatvec):
        if self._attached and self._visual is not None:
            self._quatvec_buffer.set_data(quatvec[:, ::-1], convert=True)

    @property
    def texcoords(self):
        """The texture coordinates as an (N, 2) array of floats."""
        return self._texcoords

    @texcoords.setter
    def texcoords(self, texcoords):
        self._texcoords = texcoords
        self._update_texcoords_buffer(texcoords)

    def _update_texcoords_buffer(self, texcoords):
        if self._attached or self._visual is not None:
            self._texcoords_buffer.set_data(texcoords[:, ::-1], convert=True)

    def _attach(self, visual):

        # the full projection model view
        self.vshader["transform"] = visual.transforms.get_transform("visual", "render")
        # the inverse of it
        self.vshader["transform_inv"] = visual.transforms.get_transform(
            "render", "visual"
        )

        # the modelview
        self.vshader["camera_inv"] = visual.transforms.get_transform(
            "document", "scene"
        )
        # inverse of it
        self.vshader["camera"] = visual.transforms.get_transform("scene", "document")

        super()._attach(visual)
