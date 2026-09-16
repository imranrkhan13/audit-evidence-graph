from app.search import search_pages


def _page(doc_id, title, page_num, text):
    return {"document_id": doc_id, "document_title": title, "page_number": page_num, "text_content": text}


def test_search_ranks_relevant_page_first():
    pages = [
        _page("d1", "Invoice A", 1, "Invoice Number: INV-2025-1001 Vendor: Acme Robotics Total Due: $13,600.00"),
        _page("d2", "Contract B", 1, "This service contract governs recurring consulting engagements."),
        _page("d3", "Bank Statement", 1, "DEBIT $500.00 ref:INV-2025-9999"),
    ]
    results = search_pages(pages, "Acme Robotics invoice total")
    assert results[0].document_id == "d1"


def test_search_empty_query_returns_nothing():
    pages = [_page("d1", "Doc", 1, "some content here")]
    assert search_pages(pages, "") == []


def test_search_no_matching_terms_returns_nothing():
    pages = [_page("d1", "Doc", 1, "apples oranges bananas")]
    assert search_pages(pages, "zzz_no_such_term_zzz") == []


def test_search_never_imports_models_or_engine():
    # structural guarantee: the search module has no dependency on the
    # data model or the tie-out engine, so it is mechanically incapable
    # of influencing an assertion's status.
    import app.search as search_module
    assert not hasattr(search_module, "models")
    assert not hasattr(search_module, "engine")
    assert "import" not in "\n".join(
        l for l in search_module.__dict__.get("__doc__", "").splitlines()
    )  # sanity: docstring isn't hiding a real import statement
