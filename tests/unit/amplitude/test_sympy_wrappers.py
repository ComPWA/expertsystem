# pylint: disable=no-self-use
import sympy as sy

from expertsystem.amplitude.sympy_wrappers import SymbolDefinitions


class TestSymbolDefinitions:
    def test_getitem_and_subs(self):
        definitions = SymbolDefinitions(
            {
                "x": 1,
                "y": 2,
                "z": sum(sy.symbols("x:y")),
            }
        )
        x, y, z, a = sy.symbols("x:z a")
        assert len(definitions) == 3
        assert set(definitions) == {x, y, z}
        assert definitions[sy.Symbol("x")] == definitions["x"]
        assert definitions["x"] == 1
        assert definitions["y"] == 2
        assert definitions["z"] == x + y
        assert definitions["z"].subs(definitions) == 3
        definitions[a] = x + y + z
        assert set(definitions) == {a, x, y, z}
        assert definitions[a].subs(definitions) == x + y + 3
