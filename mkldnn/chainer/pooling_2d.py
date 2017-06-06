import math
import collections
from chainer import function
from chainer.utils import type_check
from chainer.utils import conv

from mkldnn.chainer.runtime import Engine
from mkldnn.compute_complex import *

# Most important thing
from mkldnn.api.support import *
import mkldnn.api.memory as m
import mkldnn.api.pooling_forward as pooling_forward
import mkldnn.api.pooling_backward as pooling_backward
from mkldnn.mdarray import *

def _pair(x):
    if isinstance(x, collections.Iterable):
        return x
    return x, x

class Pooling2DForward(ComputeComplex):
    cc_type = 'f'

    def __init__(self, inputs, alg_kind, ksize, stride=None, pad=0,
            cover_all=True, pos=None, e=Engine()):
        super(Pooling2DForward, self).__init__()
        self.alg_kind = alg_kind
        # super(Pooling2DForward, self).__init__()
        x = inputs[0]
        if self.new:
            self._create_cc(x, ksize, stride, pad, cover_all, e)
        else:
            self._reuse(x)

    def _create_cc(self, x, ksize, stride, pad, cover_all, e):
        self.ksize = ksize
        self.stride = stride
        self.pad = pad
        self.cover_all = cover_all
        self.x = array(x, m.memory.nchw, e)

        # TODO: check avx512?

        n, c, h, w = x.shape
        sy, sx = _pair(stride)
        kh, kw = _pair(ksize)
        p_upper, p_left = _pair(pad)

        yh = conv.get_conv_outsize(h, kh, sy, p_upper, cover_all = cover_all)
        assert yh > 0, 'Height in the output should be positive.'
        yw = conv.get_conv_outsize(w, kw, sx, p_left, cover_all = cover_all)
        assert yw > 0, 'Width in the output should be positive.'

        y_shape = (n, c, yh, yw)
        p_down = sy * (yh - 1) + kh - h - p_upper
        p_right = sx * (yw - 1) + kw - w - p_left
        y_md = m.desc(y_shape, m.memory.f32, m.memory.any)
        x_md = self.x.memory.get_primitive_desc().desc()
        cc_d = pooling_forward.desc(forward_training, self.alg_kind, x_md, y_md,
                stride, ksize, (p_upper, p_left), (p_down, p_right), zero)
        cc_pd = pooling_forward.primitive_desc(cc_d, e)
        y = mdarray(cc_pd.dst_primitive_desc())

        if self.alg_kind is pooling_max:
            ws = mdarray(cc_pd.workspace_primitive_desc())
            self.dag_.push_back(pooling_forward.pooling_forward(cc_pd, at(self.x.memory), y.memory, ws.memory))
        else:
            # There is no workspace for average pooling
            ws = None
            self.dag_.push_back(pooling_forward.pooling_forward(cc_pd, at(self.x.memory), y.memory))

        self._hint = cc_pd
        self.outputs = y,
        self.ws = ws

    def _reuse(self, x):
        reuse_buffer(self.x, x)

    def match(self, inputs, alg_kind, ksize, stride=1, pad=0, cover_all=False, **kwargs):
        x = inputs[0]
        # assert self.alg_kind == alg_kind
        return  (self.x.shape == x.shape) and (self.ksize == ksize) \
                and (self.stride == stride) and (self.pad == pad) \
                and (self.cover_all == cover_all)

class Pooling2DBackward(ComputeComplex):
    cc_type = 'bd'

    def __init__(self, inputs, gy, hint, ws, alg_kind,
            ksize, stride=None, pad=0, cover_all=True,
            pos=None, e=Engine()):
        super(Pooling2DBackward, self).__init__()
        x = inputs[0]
        self.alg_kind = alg_kind
        if self.new:
            self._create_cc(x, gy, hint, ws, ksize, stride, pad, cover_all, e)
        else:
            self._reuse(x, gy)

    def _create_cc(self, x, gy, hint, ws, ksize, stride, pad, cover_all, e):
        self.ksize = ksize
        self.stride = stride
        self.pad = pad
        self.cover_all = cover_all
        self.x = array(x, m.memory.nchw, e)

        gy = array(gy, m.memory.nchw, e)
        gy_md = gy.memory.get_primitive_desc().desc()
        gx_md = m.desc(x.shape, m.memory.f32, m.memory.any)

        n, c, h, w = x.shape
        sy, sx = _pair(stride)
        kh, kw = _pair(ksize)
        p_upper, p_left = _pair(pad)

        yh = conv.get_conv_outsize(h, kh, sy, p_upper, cover_all = cover_all)
        assert yh > 0, 'Height in the output should be positive.'
        yw = conv.get_conv_outsize(w, kw, sx, p_left, cover_all = cover_all)
        assert yw > 0, 'Width in the output should be positive.'

        p_down = sy * (yh - 1) + kh - h - p_upper
        p_right = sx * (yw - 1) + kw - w - p_left

        cc_d = pooling_backward.desc(self.alg_kind, gx_md, gy_md,
                stride, ksize, (p_upper, p_left), (p_down, p_right), zero)

        cc_pd = pooling_backward.primitive_desc(cc_d, e, hint)
        gx = mdarray(cc_pd.diff_src_primitive_desc())

        if self.alg_kind is pooling_max:
            self.dag_.push_back(pooling_backward.pooling_backward(cc_pd, at(gy.memory), at(ws.memory), gx.memory))
        else:
            # There is no workspace for average pooling
            self.dag_.push_back(pooling_backward.pooling_backward(cc_pd, at(gy.memory), gx.memory))

        self._hint = hint
        self.gy = gy
        self.outputs = gx,

    def _reuse(self, x, gy):
        reuse_buffer(self.x, x)
        reuse_buffer(self.gy, gy)

    def match(self, inputs, gy, hint, ws, alg_kind, ksize, stride=1, pad=0, cover_all=False, **kwargs):
        x = inputs[0]
        assert self.alg_kind == alg_kind
        return  (self.x.shape == x.shape) and (self.ksize == ksize) \
                and (self.stride == stride) and (self.pad == pad) \
                and (self.cover_all == cover_all) and (self.hint == hint)


class Pooling2DMKLDNN(function.Function):

    """ pooling over a set of 2d planes."""

    def __init__(self, ksize, stride=None, pad=0, cover_all=True):
        if stride is None:
            stride = ksize
        # A but here: must be real number, not tuple
        # ksize = math.floor(ksize)
        # stride = math.floor(stride)
        # pad = math.floor(pad)
        self.kh, self.kw = _pair(ksize)
        self.sy, self.sx = _pair(stride)
        self.ph, self.pw = _pair(pad)

        self.cover_all = cover_all
        self._used_cudnn = False

    def check_type_forward(self, in_types):
        type_check.expect(
            in_types.size() == 1,
            in_types[0].dtype.kind == 'f',
            in_types[0].ndim == 4
        )
