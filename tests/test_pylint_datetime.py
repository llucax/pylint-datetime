# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.pylint_datetime package."""
from typing import Any

import astroid  # type: ignore
import pylint.testutils  # type: ignore

from pylint_datetime import DatetimeChecker

# tz=None and tzinfo=None is always allowed

# it makes a difference for astroid if for example timedelta is called or datetime.timedelta
# maybe this needs to be tested more thoroughly


class TestDatetimeChecker(pylint.testutils.CheckerTestCase):  # type: ignore
    """Test class for DatetimeChecker."""

    CHECKER_CLASS = DatetimeChecker

    def asserting_messages_calls(
        self,
        msg_id: str,
        node: Any,
        args: Any = None,
    ) -> None:
        """Assert messages for calls.

        Args:
            msg_id: message id.
            node: node to check.
            args: arguments to pass to the message.
        """
        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id=msg_id,
                node=node,
                args=args,
            ),
            ignore_position=True,
        ):
            self.checker.visit_call(node)

    def asserting_messages_assign(
        self,
        msg_id: str,
        node: Any,
        node2: Any = None,
        args: Any = None,
    ) -> None:
        """Assert messages for assignments.

        Args:
            msg_id: message id.
            node: node to check.
            node2: second node to check.
            args: arguments to pass to the message.
        """
        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id=msg_id,
                node=node if node2 is None else node2,
                args=args,
            ),
            ignore_position=True,
        ):
            self.checker.visit_assign(node)

    def test_timedelta_without_kargs(self) -> None:
        """Test timedelta without keyword arguments."""
        call_node_1, call_node_2 = astroid.extract_node(
            """
        import datetime
        from datetime import timedelta
        timedelta(1) #@
        datetime.timedelta(1) #@
        """
        )
        self.asserting_messages_calls("timedelta-no-keyword-args", call_node_1)
        self.asserting_messages_calls("timedelta-no-keyword-args", call_node_2)

    def test_timedelta_with_kargs(self) -> None:
        """Test timedelta with keyword arguments."""
        call_node_1, call_node_2 = astroid.extract_node(
            """
        import datetime
        from datetime import timedelta
        timedelta(seconds=1) #@
        datetime.timedelta(seconds=1) #@
        """
        )
        with self.assertNoMessages():
            self.checker.visit_call(call_node_1)
            self.checker.visit_call(call_node_2)

    def test_no_timezone_argument(self) -> None:
        """Test missing timezone arguments."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
        ) = astroid.extract_node(
            """
        import datetime
        from datetime import datetime
        datetime.now() #@
        datetime.fromtimestamp(1)  #@
        datetime(1, 1, 1, 1, 1, 1, 1)  #@
        datetime.astimezone()  #@
        """
        )
        self.asserting_messages_calls(
            "timezone-no-argument", call_node_1, args=("now",)
        )
        self.asserting_messages_calls(
            "timezone-no-argument", call_node_2, args=("fromtimestamp",)
        )
        self.asserting_messages_calls(
            "timezone-no-argument", call_node_3, args=("datetime",)
        )
        self.asserting_messages_calls(
            "timezone-no-argument", call_node_4, args=("astimezone",)
        )

    def test_passed_timezone_argument(self) -> None:
        """Test correctly passed timezone arguments."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
        ) = astroid.extract_node(
            """
        import datetime
        from datetime import datetime, timezone
        datetime.now(tz=timezone.utc) #@
        datetime.fromtimestamp(1, timezone.utc)  #@
        datetime(1, 1, 1, 1, 1, 1, 1, timezone.utc)  #@
        datetime.astimezone(tzinfo=timezone.utc)  #@
        """
        )
        with self.assertNoMessages():
            self.checker.visit_call(call_node_1)
            self.checker.visit_call(call_node_2)
            self.checker.visit_call(call_node_3)
            self.checker.visit_call(call_node_4)

    def test_no_naive_methods(self) -> None:
        """Test wrong naive method calls."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
        ) = astroid.extract_node(
            """
        import datetime
        from datetime import datetime
        datetime.today() #@
        datetime.utcnow() #@
        datetime.utcfromtimestamp(1)  #@
        datetime.utctimetuple()  #@
        datetime.time()  #@
        """
        )
        self.asserting_messages_calls(
            "naive-datetime-call", call_node_1, args=("today",)
        )
        self.asserting_messages_calls(
            "naive-datetime-call", call_node_2, args=("utcnow",)
        )
        self.asserting_messages_calls(
            "naive-datetime-call", call_node_3, args=("utcfromtimestamp",)
        )
        self.asserting_messages_calls(
            "naive-datetime-call", call_node_4, args=("utctimetuple",)
        )
        self.asserting_messages_calls(
            "naive-datetime-call", call_node_5, args=("time",)
        )

    def test_naive_objects_not_replaced(self) -> None:
        """Test naive objects without subsequent call to replace."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
            call_node_6,
        ) = astroid.extract_node(
            """
        import datetime
        dt_min = datetime.datetime.min #@
        dt_max = datetime.datetime.max #@
        dt1 = datetime.datetime.fromisocalendar(1, 1, 1) #@
        dt2 = datetime.datetime.fromordinal(1) #@
        t_min = datetime.time.min #@
        t_max = datetime.time.max #@
        """
        )
        self.asserting_messages_assign(
            "naive-datetime-no-timezone", call_node_1, args=("min",)
        )
        self.asserting_messages_assign(
            "naive-datetime-no-timezone", call_node_2, args=("max",)
        )
        self.asserting_messages_assign(
            "naive-datetime-no-timezone", call_node_3, args=("fromisocalendar",)
        )
        self.asserting_messages_assign(
            "naive-datetime-no-timezone", call_node_4, args=("fromordinal",)
        )
        self.asserting_messages_assign(
            "naive-datetime-no-timezone", call_node_5, args=("min",)
        )
        self.asserting_messages_assign(
            "naive-datetime-no-timezone", call_node_6, args=("max",)
        )

    def test_naive_objects_falsely_replaced(self) -> None:
        """Test naive objects with subsequent call to replace but lacking timezone info."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
            call_node_6,
            call_node_7,
            call_node_8,
            call_node_9,
            call_node_10,
            call_node_11,
            call_node_12,
        ) = astroid.extract_node(
            """
        import datetime
        dt_min = datetime.datetime.min #@
        dt_min.replace(1) #@
        dt_max = datetime.datetime.max #@
        dt_max.replace(1) #@
        dt1 = datetime.datetime.fromisocalendar(1, 1, 1) #@
        dt1.replace(1) #@
        dt2 = datetime.datetime.fromordinal(1) #@
        dt2.replace(year=1) #@
        t_min = datetime.time.min #@
        t_min.replace(year=1) #@
        t_max = datetime.time.max #@
        t_max.replace(year=1) #@

        """
        )
        self.asserting_messages_assign(
            "timezone-no-argument", call_node_1, call_node_2, args=("min",)
        )
        self.asserting_messages_assign(
            "timezone-no-argument", call_node_3, call_node_4, args=("max",)
        )
        self.asserting_messages_assign(
            "timezone-no-argument", call_node_5, call_node_6, args=("fromisocalendar",)
        )
        self.asserting_messages_assign(
            "timezone-no-argument", call_node_7, call_node_8, args=("fromordinal",)
        )
        self.asserting_messages_assign(
            "timezone-no-argument", call_node_9, call_node_10, args=("min",)
        )
        self.asserting_messages_assign(
            "timezone-no-argument", call_node_11, call_node_12, args=("max",)
        )

    def test_naive_objects_correctly_replaced(self) -> None:
        """Test naive objects with subsequent call to replace including timezone info."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
            call_node_6,
        ) = astroid.extract_node(
            """
        import datetime
        dt_min = datetime.datetime.min #@
        dt_min.replace(tzinfo=1)
        dt_max = datetime.datetime.max #@
        dt_max.replace(tzinfo=1)
        dt1 = datetime.datetime.fromisocalendar(1, 1, 1) #@
        dt1.replace(tzinfo=1)
        dt2 = datetime.datetime.fromordinal(1) #@
        dt2.replace(tzinfo=1)
        t_min = datetime.time.min #@
        t_min.replace(tzinfo=1)
        t_max = datetime.time.max #@
        t_max.replace(tzinfo=1)
        """
        )
        with self.assertNoMessages():
            self.checker.visit_assign(call_node_1)
            self.checker.visit_assign(call_node_2)
            self.checker.visit_assign(call_node_3)
            self.checker.visit_assign(call_node_4)
            self.checker.visit_assign(call_node_5)
            self.checker.visit_assign(call_node_6)
