import pytest

# NOTE: import path should be adjusted to the actual location in your app.
# Example (current repo): from app.routes.plan_routes import paginate_items
from app.routes.plan_routes import paginate_items


@pytest.mark.parametrize(
    "items,page,per_page,expected_slice,expected_page,expected_total_pages",
    [
        ([], None, 5, [], 1, 1),
        ([1, 2], 1, 10, [1, 2], 1, 1),
    ],
)
def test_paginate_items_basic_cases(
    items, page, per_page, expected_slice, expected_page, expected_total_pages
):
    result_slice, result_page, result_total_pages = paginate_items(items, page, per_page)

    assert result_slice == expected_slice
    assert result_page == expected_page
    assert result_total_pages == expected_total_pages


@pytest.mark.parametrize(
    "page,expected_page",
    [
        (None, 1),
        (0, 1),
        (-3, 1),
        (1, 1),
        (4, 4),
        (999, 4),
    ],
)
def test_paginate_items_page_is_clamped_to_valid_range(page, expected_page):
    items = list(range(10))  # total_items=10
    per_page = 3  # total_pages=4

    _, result_page, result_total_pages = paginate_items(items, page, per_page)

    assert result_total_pages == 4
    assert result_page == expected_page


@pytest.mark.parametrize(
    "page,expected_slice",
    [
        (1, [0, 1, 2]),
        (2, [3, 4, 5]),
        (3, [6, 7, 8]),
        (4, [9]),
    ],
)
def test_paginate_items_returns_correct_slice(page, expected_slice):
    items = list(range(10))
    per_page = 3

    result_slice, result_page, result_total_pages = paginate_items(items, page, per_page)

    assert result_total_pages == 4
    assert result_page == page
    assert result_slice == expected_slice


def test_paginate_items_per_page_zero_raises_error():
    # TODO: Decide whether per_page <= 0 should raise or be sanitized.
    # Current implementation raises ZeroDivisionError when total_items > 0.
    items = [1, 2, 3]

    with pytest.raises(ZeroDivisionError):
        paginate_items(items, page=1, per_page=0)
