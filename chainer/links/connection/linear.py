from chainer import cuda
from chainer.functions.connection import linear
from chainer import initializers
from chainer import link
import chainer

import numpy

# from nose.tools import set_trace


class Linear(link.Link):

    """Linear layer (a.k.a. fully-connected layer).

    This is a link that wraps the :func:`~chainer.functions.linear` function,
    and holds a weight matrix ``W`` and optionally a bias vector ``b`` as
    parameters.

    The weight matrix ``W`` is initialized with i.i.d. Gaussian samples, each
    of which has zero mean and deviation :math:`\\sqrt{1/\\text{in_size}}`. The
    bias vector ``b`` is of size ``out_size``. Each element is initialized with
    the ``bias`` value. If ``nobias`` argument is set to True, then this link
    does not hold a bias vector.

    Args:
        in_size (int): Dimension of input vectors. If ``None``, parameter
            initialization will be deferred until the first forward data pass
            at which time the size will be determined.
        out_size (int): Dimension of output vectors.
        nobias (bool): If ``True``, then this function does not use the bias.
        initialW (callable): Weight initializer.
            It should be a callable that takes ``numpy.ndarray`` or
            ``cupy.ndarray`` and edits its value.
            If it is ``None``, the default initializer is used.
            If it is `numpy.ndarray`, the array is used as initial
            weight value.
        initial_bias (callable): Bias initializer.
            It should be a callable that takes ``numpy.ndarray`` or
            ``cupy.ndarray`` and edits its value.
            If ``None``, the default initializer is used.
            If it is `numpy.ndarray`, the array is used as initial bias value.
    .. seealso:: :func:`~chainer.functions.linear`

    Attributes:
        W (~chainer.Variable): Weight parameter.
        b (~chainer.Variable): Bias parameter.

    """

    def __init__(self, in_size, out_size, nobias=False,
                 initialW=None, initial_bias=None):
        super(Linear, self).__init__()

        self.mkld_reshaped = False
        self.out_size = out_size

        if initialW is None:
            initialW = initializers.HeNormal(1.0 / numpy.sqrt(2))
        self.add_param('W', initializer=initializers._get_initializer(
            initialW))
        if in_size is not None:
            self._initialize_params(in_size,)

        if nobias:
            self.b = None
        else:
            if initial_bias is None:
                initial_bias = initializers.Constant(0)
            bias_initializer = initializers._get_initializer(initial_bias)
            self.add_param('b', out_size, initializer=bias_initializer)

    def _initialize_params(self, in_shape):
        if not isinstance(in_shape, tuple):
            in_shape = in_shape,
        self.W.initialize((self.out_size,) + in_shape)

    def __call__(self, x):
        """Applies the linear layer.

        Args:
            x (~chainer.Variable): Batch of input vectors.

        Returns:
            ~chainer.Variable: Output of the linear layer.

        """
        if self.W.data is None:
            if chainer.mkld.available and \
               chainer.should_use_mkldnn('>=auto'):
                self._initialize_params(x.shape[1:])
                self.mkld_reshaped = True
            else:
                self._initialize_params(x.size // x.shape[0])
        elif isinstance(x, cuda.ndarray) or isinstance(x.data, cuda.ndarray):
            return linear.linear(x, self.W, self.b)
        # we only support ndim of x 2 , 4
        elif (chainer.mkld.all_ready((x, self.W), (2, 4))) and \
             (self.mkld_reshaped is False) and \
             (self.W.ndim != x.ndim):
            w_shape = (self.out_size,) + x.shape[1:]
            if self.W.shape != w_shape:
                self.W.mkld_reshape(w_shape)
        return linear.linear(x, self.W, self.b)
