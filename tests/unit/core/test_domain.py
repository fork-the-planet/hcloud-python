from __future__ import annotations

import pytest
from dateutil.parser import isoparse

from hcloud.core import BaseDomain, DomainIdentityMixin, Meta, Pagination


class TestMeta:
    @pytest.mark.parametrize("json_content", [None, "", {}])
    def test_parse_meta_empty_json(self, json_content):
        result = Meta.parse_meta(json_content)
        assert result is not None

    def test_parse_meta_json_no_paginaton(self):
        json_content = {"meta": {}}
        result = Meta.parse_meta(json_content)
        assert isinstance(result, Meta)
        assert result.pagination is None

    def test_parse_meta_json_ok(self):
        json_content = {
            "meta": {
                "pagination": {
                    "page": 2,
                    "per_page": 10,
                    "previous_page": 1,
                    "next_page": 3,
                    "last_page": 10,
                    "total_entries": 100,
                }
            }
        }
        result = Meta.parse_meta(json_content)
        assert isinstance(result, Meta)
        assert isinstance(result.pagination, Pagination)
        assert result.pagination.page == 2
        assert result.pagination.per_page == 10
        assert result.pagination.next_page == 3
        assert result.pagination.last_page == 10
        assert result.pagination.total_entries == 100


class SomeDomain(BaseDomain, DomainIdentityMixin):
    __api_properties__ = ("id", "name")
    __slots__ = __api_properties__

    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name


class TestDomainIdentityMixin:
    @pytest.mark.parametrize(
        "domain,expected_result",
        [
            (SomeDomain(id=1, name="name"), 1),
            (SomeDomain(id=1), 1),
            (SomeDomain(name="name"), "name"),
        ],
    )
    def test_id_or_name_ok(self, domain, expected_result):
        assert domain.id_or_name == expected_result

    def test_id_or_name_exception(self):
        domain = SomeDomain()

        with pytest.raises(ValueError) as exception_info:
            _ = domain.id_or_name
        error = exception_info.value
        assert str(error) == "id or name must be set"

    @pytest.mark.parametrize(
        "domain, id_or_name, expected",
        [
            (SomeDomain(id=1, name="name1"), 1, True),
            (SomeDomain(id=1, name="name1"), "1", True),
            (SomeDomain(id=1, name="name1"), "name1", True),
            (SomeDomain(id=1, name="name1"), 2, False),
            (SomeDomain(id=1, name="name1"), "2", False),
            (SomeDomain(id=1, name="name1"), "name2", False),
            (SomeDomain(id=1, name="3"), 3, True),
            (SomeDomain(id=3, name="1"), "3", True),
        ],
    )
    def test_has_id_or_name(
        self,
        domain: SomeDomain,
        id_or_name: str | int,
        expected: bool,
    ):
        assert domain.has_id_or_name(id_or_name) == expected


class ActionDomain(BaseDomain, DomainIdentityMixin):
    __api_properties__ = ("id", "name", "started")
    __slots__ = __api_properties__

    def __init__(self, id, name="name1", started=None):
        self.id = id
        self.name = name
        self.started = isoparse(started) if started else None


class SomeOtherDomain(BaseDomain):
    __api_properties__ = ("id", "name", "child")
    __slots__ = __api_properties__

    def __init__(self, id=None, name=None, child=None):
        self.id = id
        self.name = name
        self.child = child


class TestBaseDomain:
    @pytest.mark.parametrize(
        "data_dict,expected_result",
        [
            ({"id": 1}, {"id": 1, "name": "name1", "started": None}),
            ({"id": 2, "name": "name2"}, {"id": 2, "name": "name2", "started": None}),
            (
                {"id": 3, "foo": "boo", "description": "new"},
                {"id": 3, "name": "name1", "started": None},
            ),
            (
                {
                    "id": 4,
                    "foo": "boo",
                    "description": "new",
                    "name": "name-name3",
                    "started": "2016-01-30T23:50+00:00",
                },
                {
                    "id": 4,
                    "name": "name-name3",
                    "started": isoparse("2016-01-30T23:50+00:00"),
                },
            ),
        ],
    )
    def test_from_dict_ok(self, data_dict, expected_result):
        model = ActionDomain.from_dict(data_dict)
        for k, v in expected_result.items():
            assert getattr(model, k) == v

    @pytest.mark.parametrize(
        "data,expected",
        [
            (
                SomeOtherDomain(id=1, name="name1"),
                "SomeOtherDomain(id=1, name='name1', child=None)",
            ),
            (
                SomeOtherDomain(
                    id=2,
                    name="name2",
                    child=SomeOtherDomain(id=3, name="name3"),
                ),
                "SomeOtherDomain(id=2, name='name2', child=SomeOtherDomain(id=3, name='name3', child=None))",
            ),
        ],
    )
    def test_repr_ok(self, data, expected):
        assert data.__repr__() == expected

    def test__eq__(self):
        a1 = ActionDomain(id=1, name="action")
        assert a1 == ActionDomain(id=1, name="action")
        assert a1 != ActionDomain(id=2, name="action")
        assert a1 != ActionDomain(id=1, name="something")
        assert a1 != SomeOtherDomain(id=1, name="action")

    def test_nested__eq__(self):
        child1 = ActionDomain(id=1, name="child")
        d1 = SomeOtherDomain(id=1, name="parent", child=child1)
        d2 = SomeOtherDomain(id=1, name="parent", child=child1)

        assert d1 == d2

        d2.child = ActionDomain(id=2, name="child2")

        assert d1 != d2

    def test_nested_list__eq__(self):
        child1 = ActionDomain(id=1, name="child")
        d1 = SomeOtherDomain(id=1, name="parent", child=[child1])
        d2 = SomeOtherDomain(id=1, name="parent", child=[child1])

        assert d1 == d2

        d2.child = [ActionDomain(id=2, name="child2")]

        assert d1 != d2
