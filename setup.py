#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext


ext_modules = [
    Pybind11Extension(
        "paroctree",
        ["src/napari_particles/octree/lib/myoctree.cpp"],
        cxx_std=14,
        language="c++",
    ),
]


setup(ext_modules=ext_modules)