#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

#include <iostream>
#include <vector>

#include "Vec3.h"
#include "Octree.h"
#include "OctreePoint.h"

class Particle : public OctreePoint
{
public:
    int id;
    float size;
    float value;

public:
    Particle(const int id, const Vec3 &pos, const float value, const float size) : id(id), value(value), size(size)
    {
        setPosition(pos);
    };
    Particle(const int id, const std::vector<Particle *> parts)
    {
        float size = 0;
        float value = 0;
        Vec3 pos = Vec3(0, 0, 0);

        for (auto &p : parts)
        {
            size += p->size;
            value += p->value;
            pos += p->getPosition();
        }
        value = value / parts.size();
        pos = pos / parts.size();

        this->id = id;
        this->value = value;
        this->size = size;
        setPosition(pos);
    }
};

class ParticleCloud
{
public:
    Octree *tree;
    std::vector<Particle> particles;
    std::vector<float> p_pos;
    std::vector<float> p_values;
    std::vector<float> p_sizes;

public:
    ParticleCloud(const Vec3 &origin, const Vec3 &halfDimension)
    {
        tree = new Octree(origin, halfDimension);
    };
    ~ParticleCloud()
    {
        delete tree;
    };

    void foo(py::array_t<float> x)
    {

        py::buffer_info info = x.request();
        auto ptr = static_cast<float *>(info.ptr);

        int n = 1;
        for (auto r : info.shape)
        {
            n *= r;
        }

        float s = 0.0;
        for (int i = 0; i < n; i++)
        {
            *ptr++ = 10;
        }
    };

    void init(py::array_t<float> coords, bool verbose = false)
    {

        py::buffer_info buf = coords.request();
        auto ptr = static_cast<float *>(buf.ptr);

        std::cout << "init with position of shape " << buf.shape[0] << " x " << buf.shape[1] << std::endl;

        // add initial particles
        for (size_t i = 0; i < buf.shape[0]; i++)
        {
            Vec3 pos = Vec3(ptr[3 * i], ptr[3 * i + 1], ptr[3 * i + 2]);
            Particle p(i, pos, 1.0, 10);
            particles.push_back(p);

            if (verbose)
                std::cout << pos.x << " " << pos.y << std::endl;

            tree->insert(&particles.back());
        }

        // add intermediates
        insertIntermediates(tree, verbose);
        populateVectors();
    }

    void insertIntermediates(Octree *root, bool verbose = false)
    {
        if (root->isLeafNode())
            return;
        else
        {
            if (verbose)
                std::cout << "non leaf node: " << std::endl;

            // insert children
            for (int i = 0; i < 8; ++i)
            {
                if (root->children[i] != NULL)
                    insertIntermediates(root->children[i], verbose = verbose);
            }

            // insert itself
            std::vector<Particle *> parts;
            for (int i = 0; i < 8; ++i)
            {
                if ((root->children[i] != NULL) && (root->children[i]->data != NULL))
                    parts.push_back(reinterpret_cast<Particle *>(root->children[i]->data));
            }

            Particle p(particles.size(), parts);
            particles.push_back(p);
            root->data = &particles.back();
            if (verbose)
                std::cout << "new intermediate: " << p.id << std::endl;
        }
    };

    void populateVectors()
    {

        for (auto p : particles)
        {
            Vec3 pos = p.getPosition();
            p_pos.push_back(pos.z);
            p_pos.push_back(pos.y);
            p_pos.push_back(pos.x);
            p_sizes.push_back(p.size);
            p_values.push_back(p.value);
        }
    }

    py::array_t<float> getPos()
    {
        return py::array_t<float>(p_pos.size(), // shape
                                (float*)p_pos.data()          // the data pointer
        );
    }

    py::array_t<float> getSize()
    {
        return py::array_t<float>(p_sizes.size(), // shape
                                (float*)p_sizes.data()          // the data pointer
        );
    }

    py::array_t<float> getValue()
    {
        return py::array_t<float>(p_values.size(), // shape
                                (float*)p_values.data()          // the data pointer
        );
    }

};

PYBIND11_MODULE(paroctree, m)
{
    m.doc() = "pybind11 example plugin"; // optional module docstring

    // m.def("add", &add, "A function that adds two numbers");
    py::class_<Vec3>(m, "Vec3")
        .def(py::init<const float, const float, const float>());

    py::class_<Octree>(m, "Octree")
        .def(py::init<const Vec3 &, const Vec3 &>());

    py::class_<ParticleCloud>(m, "ParticleCloud")
        .def(py::init<const Vec3 &, const Vec3 &>())
        .def("foo", &ParticleCloud::foo, "")
        .def("init", &ParticleCloud::init, "", py::arg("coords"), py::arg("verbose") = false)
        .def("__repr__",
             [](const ParticleCloud &a)
             {
                 return "Particle Cloud with " + std::to_string(a.particles.size()) + " particles";
             })
        .def("getPos", &ParticleCloud::getPos, "")
        .def("getValue", &ParticleCloud::getValue, "")
        .def("getSize", &ParticleCloud::getSize, "")
        ;
}
