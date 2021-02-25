"""Tools that make using {mod}`sympy` as a library a bit easier."""

from abc import abstractmethod
from typing import Any, Callable, Type

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
                return sy.Expr.__new__(cls, *args).evaluate()  # type: ignore  # pylint: disable=no-member
            return sy.Expr.__new__(cls, *args)

        def doit_method(self: Any, **hints: Any) -> sy.Expr:
            return type(self)(*self.args, **hints, evaluate=True)

        decorated_class.__new__ = new_method  # type: ignore
        decorated_class.doit = doit_method
        return decorated_class

    return decorator
