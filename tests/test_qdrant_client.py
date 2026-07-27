from types import SimpleNamespace
from unittest.mock import MagicMock

from app.vectordb.qdrant_client import QdrantDB


def _make_db():
    db = object.__new__(QdrantDB)
    db.client = MagicMock()
    db.collection_name = "omnibrain"
    return db


def test_search_adds_exact_page_number_filter():
    db = _make_db()
    db.client.query_points.return_value = SimpleNamespace(points=[])

    db.search(query_embedding=[0.1, 0.2], page_number=3)

    kwargs = db.client.query_points.call_args.kwargs
    query_filter = kwargs["query_filter"]

    assert query_filter is not None
    assert len(query_filter.must) == 1
    assert query_filter.must[0].key == "page_number"
    assert query_filter.must[0].match.value == 3


def test_search_adds_page_list_filter():
    db = _make_db()
    db.client.query_points.return_value = SimpleNamespace(points=[])

    db.search(query_embedding=[0.1, 0.2], page_numbers=[2, 3, 4])

    kwargs = db.client.query_points.call_args.kwargs
    query_filter = kwargs["query_filter"]

    assert query_filter is not None
    assert len(query_filter.should) == 3
    assert {condition.match.value for condition in query_filter.should} == {2, 3, 4}


def test_search_adds_page_range_filter():
    db = _make_db()
    db.client.query_points.return_value = SimpleNamespace(points=[])

    db.search(query_embedding=[0.1, 0.2], page_range=(2, 4))

    kwargs = db.client.query_points.call_args.kwargs
    query_filter = kwargs["query_filter"]

    assert query_filter is not None
    assert len(query_filter.must) == 1
    assert query_filter.must[0].key == "page_number"
    assert query_filter.must[0].range.gte == 2
    assert query_filter.must[0].range.lte == 4
