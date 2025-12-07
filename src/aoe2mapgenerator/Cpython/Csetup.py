from setuptools import setup, Extension

module = Extension('knn', sources=['knn.c'])

setup(name='knn',
      version='1.0',
      description='KNN C extension',
      ext_modules=[module])