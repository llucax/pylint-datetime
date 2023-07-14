# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.pylint_datetime package."""
import pytest

from frequenz.pylint_datetime import delete_me


def test_pylint_datetime_succeeds() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function succeeds."""
    assert delete_me() is True


def test_pylint_datetime_fails() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function fails."""
    with pytest.raises(RuntimeError, match="This function should be removed!"):
        delete_me(blow_up=True)
