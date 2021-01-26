# cspell: disable srepr
# pylint: disable=invalid-name,no-self-use

import operator
from functools import reduce

import sympy as sy


class TestSymbol:
    def test_hash(self):
        x = sy.Symbol("a")
        y = sy.Symbol("a")
        assert x == y
        assert x is y
        assert hash(x) == hash(y)
        f = sy.Function("h")
        g = sy.Function("h")
        assert f is g
        assert f is g
        f = sy.Function("h")(x)
        g = sy.Function("h")(x)
        assert f is g
        assert f is g

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

    def test_product(self):
        symbols = [
            sy.Symbol("x"),
            sy.Symbol("y"),
            sy.Symbol("z"),
        ]
        reduce(operator.mul, symbols)
