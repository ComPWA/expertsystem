# cspell: disable srepr
# pylint: disable=invalid-name,no-self-use

import operator
from copy import deepcopy
from functools import reduce

import sympy as sy


class TestFunction:
    def test_hash(self):
        x = sy.Symbol("x")
        f = sy.Function("h")
        g = sy.Function("h")
        assert f is g
        assert f(x) is g(x)
        f = sy.Function("h")(x)
        g = sy.Function("h")(x)
        assert f is g


class TestSymbol:
    def test_hash(self):
        x = sy.Symbol("a")
        y = sy.Symbol("a")
        y_real = sy.Symbol("a", real=True)
        assert x == y
        assert x is y
        assert y != y_real
        assert hash(x) == hash(y)

    def test_name(self):
        # pylint: disable=no-member
        x = sy.Symbol("x; weird-spacing\t.,")
        f = sy.Function("  f.^")
        g = sy.Function("g")(x)
        assert x.name == "x; weird-spacing	.,"
        assert sy.srepr(x) == "Symbol('x; weird-spacing\\t.,')"
        assert f.name == "  f.^"
        assert g.name == "g"
        x.name = "x"
        assert x.name == "x"

    def test_name_change(self):
        x = sy.Symbol("a")
        y = sy.Symbol("a")
        assert x.name == y.name
        assert x == y
        assert x is y
        x.name = "I am x"
        assert y.name == "I am x"
        z = deepcopy(x)
        assert z == x
        assert z is not x
        assert z.name == "I am x"
        z.name = "z"
        assert x.name == "I am x"
        assert z.name == "z"

    def test_product(self):
        symbols = [
            sy.Symbol("x"),
            sy.Symbol("y"),
            sy.Symbol("z"),
        ]
        reduce(operator.mul, symbols)
