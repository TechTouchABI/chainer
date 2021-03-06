[![GitHub license](https://img.shields.io/github/license/chainer/chainer.svg)](https://github.com/intel/chainer)
[![travis](https://img.shields.io/travis/intel/chainer/master.svg)](https://travis-ci.org/intel/chainer)
[![coveralls](https://img.shields.io/coveralls/intel/chainer.svg)](https://coveralls.io/github/intel/chainer)
[![Read the Docs](https://readthedocs.org/projects/chainer/badge/?version=stable)](http://docs.chainer.org/en/stable/?badge=stable)

# IntelChainer: Optimized-Chainer for Intel architectures

## Requirements

Chainer is tested on Ubuntu 14.04 and CentOS 7. We recommend them to use Chainer, though it may run on other systems as well.

Minimum requirements:
- Python 2.7.6+, 3.4.3+, 3.5.1+, 3.6.0+
- NumPy 1.9, 1.10, 1.11, 1.12
- Six 1.9
- Swig 3.0.9

Requirements for some features:
- CUDA support
  - CUDA 6.5, 7.0, 7.5, 8.0
  - filelock
  - g++ 4.8.4+
- cuDNN support
  - cuDNN v2, v3, v4, v5, v5.1
- Caffe model support
  - Protocol Buffers (pip install protobuf)
    - protobuf>=3.0.0 is required for Py3
- Image dataset support
  - Pillow
- HDF5 serialization support
  - h5py 2.5.0
- Testing utilities
  - Mock
  - Nose

## Installation

### Minimum installation

If you use old ``setuptools``, upgrade it:

```
pip install -U setuptools
```

Then, install Chainer via PyPI:
```
pip install chainer
```

You can also install Chainer from the source code:
```
python setup.py install
```


### Installation with CUDA

If you want to enable CUDA, first you have to install CUDA and set the environment variable `PATH` and `LD_LIBRARY_PATH` for CUDA executables and libraries.
For example, if you are using Ubuntu and CUDA is installed by the official distribution, then CUDA is installed at `/usr/local/cuda`.
In this case, you have to add the following lines to `.bashrc` or `.zshrc` (choose which you are using):
```
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

Chainer had `chainer-cuda-deps` module to enable CUDA in previous version.
Recent version (>=1.3) does not require this module.
So **you do not have to install** `chainer-cuda-deps`.

If you want to enable cuDNN, add a directory containing `cudnn.h` to `CFLAGS`, and add a directory containing `libcudnn.so` to `LDFLAGS` and `LD_LIBRARY_PATH`:
```
export CFLAGS=-I/path/to/cudnn/include
export LDFLAGS=-L/path/to/cudnn/lib
export LD_LIBRARY_PATH=/path/to/cudnn/lib:$LD_LIBRARY_PATH
```
Do not forget to restart your terminal session (or `source` it) to enable these changes.
And then, reinstall Chainer.


### Image dataset support

If you want to use Image dataset (`chainer/datasets/ImageDataset`), please install Pillow manually.
Supported image format depends on your environment.

```
pip install pillow
```


### HDF5 Support

If you want to use HDF5 serialization, please install h5py manually.
h5py requires libhdf5.
Anaconda distribution includes this package.
If you are using another Python distribution, use either of the following commands to install libhdf5 depending on your Linux environment:

```
apt-get install libhdf5-dev
yum install hdf5-devel
```

And then, install h5py via PyPI.
You may need to install Cython for h5py.

```
pip install cython
pip install h5py
```


## Reference

Tokui, S., Oono, K., Hido, S. and Clayton, J.,
Chainer: a Next-Generation Open Source Framework for Deep Learning,
*Proceedings of Workshop on Machine Learning Systems(LearningSys) in
The Twenty-ninth Annual Conference on Neural Information Processing Systems (NIPS)*, (2015)
[URL](http://learningsys.org/papers/LearningSys_2015_paper_33.pdf), [BibTex](chainer_bibtex.txt)


## More information

- Official site: http://chainer.org/
- Official document: http://docs.chainer.org/
- Pfn chainer github: https://github.com/pfnet/chainer
- Intel chainer github: https://github.com/intel/chainer
- Forum: https://groups.google.com/forum/#!forum/chainer
- Forum (Japanese): https://groups.google.com/forum/#!forum/chainer-jp
- Twitter: https://twitter.com/ChainerOfficial
- Twitter (Japanese): https://twitter.com/chainerjp
- External examples: https://github.com/pfnet/chainer/wiki/External-examples
- Research projects using Chainer: https://github.com/pfnet/chainer/wiki/Research-projects-using-Chainer

## License

MIT License (see `LICENSE` file).
