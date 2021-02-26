# cspell:ignore rpow rtruediv
# pylint: disable=no-member,protected-access,unused-argument
"""Tools that make using {mod}`sympy` as a library a bit easier."""

from abc import abstractmethod
from typing import Any, Callable, Tuple, Type

import sympy as sy
from sympy.printing.latex import LatexPrinter


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
