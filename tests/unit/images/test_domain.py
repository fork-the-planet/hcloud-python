from __future__ import annotations

import datetime
from datetime import timezone

import pytest

from hcloud.images import Image


@pytest.mark.parametrize(
    "value",
    [
        (Image(id=1),),
    ],
)
def test_eq(value):
    assert value == value


class TestImage:
    def test_created_is_datetime(self):
        image = Image(id=1, created="2016-01-30T23:50+00:00")
        assert image.created == datetime.datetime(
            2016, 1, 30, 23, 50, tzinfo=timezone.utc
        )
