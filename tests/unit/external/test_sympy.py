# pylint: disable=invalid-name,no-self-use

import sympy as sy


class TestSymbol:
    def test_hash(self):
        x = sy.Symbol("a")
        y = sy.Symbol("a")
        assert x == y
        assert x is y
        assert hash(x) == hash(y)
