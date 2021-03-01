# cspell:ignore numpycode pycode rpow rtruediv
# pylint: disable=no-member,protected-access,unused-argument
"""Tools that make using {mod}`sympy` as a library a bit easier."""

import itertools
from abc import abstractmethod
from collections import abc
from typing import Any, Callable, Iterable, Tuple, Type, Union

import sympy as sy
from sympy.core.sympify import _sympify
from sympy.printing.latex import LatexPrinter
from sympy.printing.pycode import NumPyPrinter
from sympy.printing.str import StrPrinter


class UnevaluatedExpression(sy.Expr):
    @abstractmethod
    def evaluate(self) -> sy.Expr:
        pass

    @abstractmethod
    def _latex(self, printer: LatexPrinter, *args: Any) -> str:
        """Provide a mathematical Latex representation for notebooks."""
        args = tuple(map(printer._print, self.args))
        return f"{self.__class__.__name__}{args}"


def implement_expr(
    n_args: int,
) -> Callable[[Type[UnevaluatedExpression]], sy.Expr]:
    """Decorator for classes that derive from `UnevaluatedExpression`.

    Implement a `~object.__new__` and `~sympy.core.basic.Basic.doit` method for
    a class that derives from `~sympy.core.expr.Expr` (via
    `UnevaluatedExpression`). It is important to derive from
    `~UnevaluatedExpression.evaluate` method has to be implemented
    """

    def decorator(decorated_class: Type[UnevaluatedExpression]) -> sy.Expr:
        def new_method(
            cls: Type,
            *args: sy.Symbol,
            **hints: Any,
        ) -> bool:
            if len(args) != n_args:
                raise ValueError(
                    f"{n_args} parameters expected, got {len(args)}"
                )
            args = sy.sympify(args)
            evaluate = hints.get("evaluate", False)
            if evaluate:
                return sy.Expr.__new__(cls, *args).evaluate()  # type: ignore
            return sy.Expr.__new__(cls, *args)

        def doit_method(self: Any, **hints: Any) -> sy.Expr:
            return type(self)(*self.args, **hints, evaluate=True).doit()

        decorated_class.__new__ = new_method  # type: ignore
        decorated_class.doit = doit_method
        return decorated_class

    return decorator


def implement_mat_expr(
    name: str, n_args: int, shape: Tuple[int, int]
) -> Callable[[Type[sy.MatrixExpr]], sy.MatrixExpr]:
    def decorator(decorated_class: Type[sy.MatrixExpr]) -> sy.Expr:
        def new_method(
            cls: Type,
            *args: sy.Symbol,
            **hints: Any,
        ) -> bool:
            if len(args) != n_args:
                raise ValueError(
                    f"__new__() expects {n_args} positional arguments,"
                    f" got {len(args)}"
                )
            args = sy.sympify(args)
            evaluate = hints.get("evaluate", False)
            if evaluate:
                return sy.MatrixExpr.__new__(cls, *args).evaluate()  # type: ignore
            return sy.MatrixExpr.__new__(cls, *args)

        def _entry(
            self: sy.MatrixExpr, i: Any, j: Any, **kwargs: Any
        ) -> sy.Expr:
            return self.evaluate()[i, j]

        def _latex(
            self: sy.MatrixExpr, printer: LatexPrinter, *args: Any
        ) -> str:
            args = tuple(map(printer._print, self.args))
            args_str = ", ".join(args)
            return fR"\mathbf{{{name}}}\left({args_str}\right)"

        def doit(self: Any, **hints: Any) -> sy.Expr:
            return type(self)(*self.args, **hints, evaluate=True).doit()

        decorated_class.__new__ = new_method  # type: ignore
        decorated_class.doit = doit
        decorated_class._entry = _entry
        decorated_class._latex = _latex
        decorated_class.__rpow__ = lambda s, o: s ** o
        decorated_class.__rtruediv__ = lambda s, o: s / o
        decorated_class.shape = property(lambda self: shape)
        return decorated_class

    return decorator


# Needed until Sympy v1.8 is released
# https://github.com/sympy/sympy/pull/20943
class _ArrayExpr(sy.Expr):
    _iterable = False  # needed for lambdify


class ArraySymbol(_ArrayExpr):
    """Symbol representing an array expression.

    https://github.com/sympy/sympy/pull/20943
    """

    def __new__(
        cls, name: str, shape: Tuple[sy.Expr, ...], *args: Any
    ) -> "ArraySymbol":
        if not isinstance(name, sy.core.symbol.Str):
            name = sy.core.symbol.Str(name)
        sympified_shape = tuple(map(_sympify, shape))
        obj = sy.Expr.__new__(cls, name, sympified_shape, *args)
        return obj

    @property
    def name(self) -> sy.core.symbol.Str:
        return self.args[0]

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.args[1]

    def __getitem__(
        self, indices: Union[int, slice, Tuple[Union[int, slice], ...]]
    ) -> "ArrayElement":
        return ArrayElement(self.name, self.shape, indices)

    def as_explicit(self) -> sy.ImmutableDenseNDimArray:
        data = [
            self[i] for i in itertools.product(*[range(j) for j in self.shape])
        ]
        return sy.ImmutableDenseNDimArray(data).reshape(*self.shape)

    def _latex(self, printer: LatexPrinter) -> str:
        return printer._print(self.name)

    def _numpycode(self, printer: NumPyPrinter) -> str:
        return self._sympystr(printer)

    def _sympystr(self, printer: StrPrinter) -> str:
        return printer._print(self.name)


class ArrayElement(ArraySymbol):
    """An element of an array.

    https://github.com/sympy/sympy/pull/20943
    """

    def __new__(
        cls,
        name: str,
        shape: Tuple[int, ...],
        # https://stackoverflow.com/a/1685450
        indices: Union[int, slice, Tuple[Union[int, slice], ...]],
        *args: Any,
    ) -> "ArrayElement":
        if isinstance(indices, tuple):
            if len(indices) > len(shape):
                raise KeyError(
                    f"Array has rank {len(shape)},"
                    f" but there are {len(indices)} indices"
                )
        for idx, dim in zip(_safe_iter(indices), shape):
            if isinstance(idx, (int, sy.core.numbers.Integer)) and isinstance(
                dim, (int, sy.core.numbers.Integer)
            ):
                if idx >= dim:
                    raise KeyError(f"Index {idx} exceeds shape {shape})")
        return sy.Expr.__new__(cls, name, shape, indices, *args)

    @property
    def indices(self) -> Tuple[Union[int, slice], ...]:
        return self.args[2]

    def _latex(self, printer: LatexPrinter, *__: Any) -> str:
        name = printer._print(self.name)
        indices = list()
        for idx in _safe_iter(self.indices):
            if isinstance(idx, slice):
                indices.append(_slice_to_str(idx))
            else:
                indices.append(printer._print(idx))
        return f"{name}_{{{','.join(indices)}}}"

    def _numpycode(self, printer: NumPyPrinter, *args: Any) -> str:
        return self._sympystr(printer, args)

    def _sympystr(self, printer: StrPrinter, *__: Any) -> str:
        name = printer._print(self.name)
        indices = list()
        for idx in _safe_iter(self.indices):
            if isinstance(idx, slice):
                indices.append(_slice_to_str(idx))
            else:
                indices.append(printer._print(idx))
        return f"{name}[{', '.join(indices)}]"


def _safe_iter(iterable: Any) -> Iterable:
    if isinstance(iterable, abc.Iterable):
        return iterable
    return iter([iterable])


def _slice_to_str(instance: slice) -> str:
    slice_str = map(
        lambda i: "" if i is None else str(i),
        [
            instance.start,
            instance.stop,
            instance.step,
        ],
    )
    output = ":".join(slice_str)
    if instance.step in {None, 1}:
        return output[:-1]
    return output
