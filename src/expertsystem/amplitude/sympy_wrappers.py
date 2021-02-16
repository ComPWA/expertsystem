"""Wrappers that form a bridge between `sympy` and the `.amplitude` module."""
from collections import abc
from typing import (
    Dict,
    ItemsView,
    KeysView,
    Mapping,
    Optional,
    Union,
    ValuesView,
)

import sympy as sy


class SymbolDefinitions(abc.MutableMapping):
    def __init__(
        self,
        parameters: Optional[Mapping[Union[sy.Symbol, str], sy.Expr]] = None,
    ) -> None:
        self.__definitions: Dict[sy.Symbol, sy.Expr] = dict()
        if parameters is not None:
            if not isinstance(parameters, abc.Mapping):
                raise TypeError(
                    f"{self.__class__.__name__} requires a mapping"
                )
            if not all(
                map(lambda k: isinstance(k, (sy.Symbol, str)), parameters)
            ):
                raise TypeError(
                    f"Not all keys are of type {sy.Symbol.__class__} or str"
                )
            for par, value in parameters.items():
                if isinstance(par, sy.Symbol):
                    par_symbol = par
                else:
                    par_symbol = sy.Symbol(par)
                self.__definitions[par_symbol] = value

    def __delitem__(self, key: Union[sy.Symbol, str]) -> None:
        if isinstance(key, str):
            key = sy.Symbol(key)
        del self.__definitions[key]

    def __getitem__(self, key: Union[sy.Symbol, str]) -> sy.Expr:
        if isinstance(key, sy.Symbol):
            found_symbol = key
        else:
            found_symbol = None
            for symbol in self.__definitions:
                if key == symbol.name:
                    found_symbol = symbol
            if found_symbol is None:
                raise ValueError(f"No {sy.Symbol.__name__} with name {key}")
        return self.__definitions[found_symbol]

    def __iter__(self) -> sy.Symbol:
        return iter(self.__definitions)

    def __len__(self) -> int:
        return len(self.__definitions)

    def __repr__(self) -> str:
        str_dict = {p.name: v for p, v in self.items()}
        return f"{self.__class__.__name__}({str_dict})"

    def __setitem__(self, key: Union[sy.Symbol, str], value: sy.Expr) -> None:
        if isinstance(key, sy.Symbol):
            symbol = key
        else:
            symbol = sy.Symbol(key)
        self.__definitions[symbol] = value

    def items(self) -> ItemsView[sy.Symbol, sy.Expr]:
        return self.__definitions.items()

    def keys(self) -> KeysView[sy.Symbol]:
        return self.__definitions.keys()

    def values(self) -> ValuesView[sy.Expr]:
        return self.__definitions.values()

    def _repr_latex_(self) -> str:
        output = "$"
        for key, value in self.items():
            output += fR"{sy.latex(key)} = {sy.latex(value)} \\"
        output = output[:-2]
        output += "$"
        return output
