from app.ingestion.retrieval_filter import RetrievalFilter


def test_retrieval_filter_keeps_only_scores_at_or_above_threshold():
    results = [
        {"score": 0.96},
        {"score": 0.88},
        {"score": 0.74},
        {"score": 0.61},
        {"score": 0.30},
    ]

    retrieval_filter = RetrievalFilter(threshold=0.75)

    filtered = retrieval_filter.filter_results(results)

    assert filtered == [
        {"score": 0.96},
        {"score": 0.88},
    ]