"""Pylint checker ensure correct usage of datetime module, especially around aware/naive objects."""

from typing import Any

import astroid  # type: ignore
import pylint  # type: ignore
from pylint.checkers import BaseChecker  # type: ignore

# function calls to fromisoformat, strptime and fromisoformat can't be checked - they parse strings
# if the specified timezone is None, still allowed although they produce naive objects


class DatetimeChecker(BaseChecker):  # type: ignore
    """class for custom pylint checker."""

    name = "pylint-datetime"
    priority = -1
    msgs = {
        "W9999": (
            "timedelta() called without keyword arguments",
            "timedelta-no-keyword-args",
            "timedelta() called without keyword arguments.",
        ),
        "W9998": (
            'Function call to "%s"/"replace" should be called with a timezone argument',
            "timezone-no-argument",
            'Function call to "%s"/"replace" should be called with a timezone argument',
        ),
        "W9997": (
            'Function call to "%s" can only produce naive objects',
            "naive-datetime-call",
            'Function call to "%s" can only produce naive objects, aware objects necessary',
        ),
        "W9996": (
            'Attribute access "%s" should be followed by a call to replace with timezone argument',
            "naive-datetime-no-timezone",
            'Attribute access "%s" should be followed by a call to replace with timezone argument',
        ),
    }

    def __init__(self, linter: pylint.lint.PyLinter = None) -> None:
        """Initialize checker.

        Args:
            linter: instance of pylint linter.
        """
        super().__init__(linter)

    def timedelta_with_keywords(
        self, node: astroid.node_classes.NodeNG, name: str
    ) -> None:
        """Check calls to timedelta() and datetime.timedelta() for keyword arguments.

        Args:
            node: the node that visit_call originates from.
            name: name of the function being called.
        """
        if name == "timedelta":
            for _ in node.args:
                self.add_message("timedelta-no-keyword-args", node=node)
            if not node.args and not node.keywords:
                self.add_message("timedelta-no-keyword-args", node=node)

    # check for positional arguments cheesy, uses fact, that they have one Attribute Argument.

    def timezone_argument(self, node: astroid.node_classes.NodeNG, name: str) -> None:
        """Check calls to datetime, now, fromtimestamp, astimezone and time for timezone arg.

        Args:
            node: the node that visit_call originates from.
            name: name of the function being called.
        """
        if name in ("datetime", "now", "fromtimestamp", "astimezone"):
            if not any(
                isinstance(arg, astroid.Keyword) and arg.arg in ("tz", "tzinfo")
                for arg in node.keywords
            ):
                if not any(isinstance(arg, astroid.Attribute) for arg in node.args):
                    self.add_message("timezone-no-argument", node=node, args=(name,))

    def naive_functions(self, node: astroid.node_classes.NodeNG, name: str) -> None:
        """Check that functions producing only naive objects are never called.

        Args:
            node: the node that visit_call originates from
            name: name of the function being called
        """
        if name in ("today", "utcnow", "utcfromtimestamp", "utctimetuple", "time"):
            self.add_message("naive-datetime-call", node=node, args=(name,))

    def visit_call(self, node: astroid.node_classes.NodeNG) -> None:
        """Pylint function responds when any function is called.

        Args:
            node: origin node for function call.
        """
        if hasattr(node.func, "name"):
            name = node.func.name
        elif hasattr(node.func, "attrname"):
            name = node.func.attrname

        self.timedelta_with_keywords(node, name)

        self.timezone_argument(node, name)

        self.naive_functions(node, name)

    def naive_properties_methods_replace(
        self, node: astroid.node_classes.NodeNG, assigned_value: Any, assigned_var: Any
    ) -> None:
        """Check for a replace call specifiying timezone after naive property or function.

        Args:
            node: the node that visit_call originates from.
            assigned_value: the value of the assignment that triggered function call.
            assigned_var: the variable that the value was assigned to.
        """
        next_node = assigned_var
        next_is_empty = True
        if next_node and next_node.next_sibling():
            next_is_empty = False
            next_node = next_node.next_sibling()
            if (
                isinstance(next_node.value, astroid.Call)
                and isinstance(next_node.value.func, astroid.Attribute)
                and next_node.value.func.attrname == "replace"
            ):
                if not any(
                    isinstance(arg, astroid.Keyword) and arg.arg == "tzinfo"
                    for arg in next_node.value.keywords
                ) and (
                    not any(
                        isinstance(arg, astroid.Attribute)
                        for arg in next_node.value.args
                    )
                ):
                    new_node = next_node.value
                    self.add_message(
                        "timezone-no-argument", node=new_node, args=(assigned_value,)
                    )
            else:
                self.add_message(
                    "naive-datetime-no-timezone", node=node, args=(assigned_value,)
                )
        if next_is_empty:
            self.add_message(
                "naive-datetime-no-timezone", node=node, args=(assigned_value,)
            )

    def visit_assign(self, node: astroid.node_classes.NodeNG) -> None:
        """Pylint function responds when any assignment takes place.

        Args:
            node: the node that visit_call originates from.
        """
        assigned_var = node.targets[0]
        assigned_value = node.value

        if isinstance(assigned_var, astroid.AssignName):
            assigned_var_type = assigned_var.inferred()[0]
            if assigned_var_type.qname() in ("datetime.datetime", "datetime.time"):
                if isinstance(assigned_value, astroid.Attribute):
                    if assigned_value.attrname in ("min", "max"):
                        ass_val_name = assigned_value.attrname
                        self.naive_properties_methods_replace(
                            node, ass_val_name, assigned_var
                        )
                if isinstance(assigned_value, astroid.Call):
                    if assigned_value.func.attrname in (
                        "fromordinal",
                        "fromisocalendar",
                    ):
                        ass_val_name = assigned_value.func.attrname
                        self.naive_properties_methods_replace(
                            node, ass_val_name, assigned_var
                        )


def register(linter: pylint.lint.PyLinter) -> None:
    """Pylint function to register checker.

    Args:
        linter: instance of pylint linter.
    """
    linter.register_checker(DatetimeChecker(linter))
