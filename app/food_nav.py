"""Build 食品及飲品 mega menu from product_categories / product_details (DB)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from flask import url_for

from app.maternity_nav import _collect_descendant_category_ids, _top_suppliers_for_categories
from app.models import ProductCategory

FOOD_ROOT_NAMES = frozenset({'食品及飲品', '食品及饮料'})


def _pane_sections_for_l2_food(
    l2: ProductCategory,
    children_by_parent: dict[int, list[ProductCategory]],
) -> list[dict[str, Any]]:
    l3_list = children_by_parent.get(l2.product_categories_id, [])
    sections: list[dict[str, Any]] = []
    flat_buffer: list[dict[str, Any]] = []

    def flush_flat() -> None:
        if not flat_buffer:
            return
        for i, lk in enumerate(flat_buffer):
            lk['visual_ix'] = (i % 8) + 1
        sections.append(
            {
                'title': None,
                'category_id': None,
                'view_all_url': None,
                'links': flat_buffer.copy(),
            }
        )
        flat_buffer.clear()

    for l3 in l3_list:
        flat_buffer.append(
            {
                'name': l3.product_categories_name,
                'url': url_for('catalog_category', category_id=l3.product_categories_id),
                'visual_ix': 1,
            }
        )

    flush_flat()
    return sections


def build_food_mega_nav() -> dict[str, Any] | None:
    """
    Returns { 'tabs': [ { tab_key, name, sections, brands, view_all_url } ] }
    or None if DB / schema unavailable.
    """
    try:
        all_cats = (
            ProductCategory.query.order_by(
                ProductCategory.level.asc(),
                ProductCategory.product_categories_id.asc(),
            ).all()
        )
    except Exception:
        return None

    if not all_cats:
        return None

    root = next(
        (
            c
            for c in all_cats
            if c.product_categories_name in FOOD_ROOT_NAMES
            and (c.parent_id is None or c.level == 1)
        ),
        None,
    )
    if root is None:
        root = next(
            (c for c in all_cats if c.product_categories_name in FOOD_ROOT_NAMES),
            None,
        )
    if root is None:
        return None

    children_by_parent: dict[int, list[ProductCategory]] = defaultdict(list)
    for c in all_cats:
        if c.parent_id is not None:
            children_by_parent[c.parent_id].append(c)

    for pid in children_by_parent:
        children_by_parent[pid].sort(key=lambda x: x.product_categories_id)

    l2_list = children_by_parent.get(root.product_categories_id, [])
    if not l2_list:
        return {'tabs': [], 'root_name': root.product_categories_name}

    tabs: list[dict[str, Any]] = []
    for l2 in l2_list:
        desc_ids = _collect_descendant_category_ids(l2.product_categories_id, children_by_parent)
        brands_raw = _top_suppliers_for_categories(desc_ids, limit=8)
        brands = [
            {
                'name': b['name'],
                'url': url_for(
                    'catalog_category',
                    category_id=l2.product_categories_id,
                    supplier_id=b['supplier_id'],
                ),
            }
            for b in brands_raw
        ]

        tabs.append(
            {
                'tab_key': f'cat-{l2.product_categories_id}',
                'category_id': l2.product_categories_id,
                'name': l2.product_categories_name,
                'view_all_url': url_for('catalog_category', category_id=l2.product_categories_id),
                'sections': _pane_sections_for_l2_food(l2, children_by_parent),
                'brands': brands,
            }
        )

    return {'tabs': tabs, 'root_name': root.product_categories_name}
