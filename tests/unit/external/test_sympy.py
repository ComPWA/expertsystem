# cspell: disable srepr
# pylint: disable=invalid-name,no-self-use

import sympy as sy


class TestSymbol:
    def test_hash(self):
        x = sy.Symbol("a")
        y = sy.Symbol("a")
        assert x == y
        assert x is y
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
