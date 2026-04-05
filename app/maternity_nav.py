"""Build 母嬰 mega menu from product_categories / product_details (DB)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from flask import url_for
from sqlalchemy import func

from app import db
from app.models import ProductCategory, ProductDetail, Supplier


def _collect_descendant_category_ids(
    root_id: int, children_by_parent: dict[int, list[ProductCategory]]
) -> list[int]:
    out: list[int] = []
    stack = [root_id]
    while stack:
        cid = stack.pop()
        out.append(cid)
        for ch in children_by_parent.get(cid, []):
            stack.append(ch.product_categories_id)
    return out


def _top_suppliers_for_categories(category_ids: list[int], limit: int = 8) -> list[dict[str, Any]]:
    if not category_ids:
        return []
    rows = (
        db.session.query(Supplier.supplier_id, Supplier.supplier_name)
        .join(ProductDetail, ProductDetail.supplier_id == Supplier.supplier_id)
        .filter(ProductDetail.product_categories_id.in_(category_ids))
        .group_by(Supplier.supplier_id, Supplier.supplier_name)
        .order_by(func.count(ProductDetail.product_categories_uuid).desc())
        .limit(limit)
        .all()
    )
    return [{'supplier_id': r[0], 'name': r[1]} for r in rows]


def _pane_sections_for_l2(
    l2: ProductCategory,
    children_by_parent: dict[int, list[ProductCategory]],
) -> list[dict[str, Any]]:
    """Subsections with optional title; L4 under L3, or consecutive leaf L3 in one grid."""
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
        l4_list = children_by_parent.get(l3.product_categories_id, [])
        if l4_list:
            flush_flat()
            sections.append(
                {
                    'title': l3.product_categories_name,
                    'category_id': l3.product_categories_id,
                    'view_all_url': url_for('catalog_category', category_id=l3.product_categories_id),
                    'links': [
                        {
                            'name': x.product_categories_name,
                            'url': url_for('catalog_category', category_id=x.product_categories_id),
                            'visual_ix': (i % 8) + 1,
                        }
                        for i, x in enumerate(l4_list)
                    ],
                }
            )
        else:
            flat_buffer.append(
                {
                    'name': l3.product_categories_name,
                    'url': url_for('catalog_category', category_id=l3.product_categories_id),
                    'visual_ix': 1,
                }
            )

    flush_flat()
    return sections


def build_maternity_mega_nav() -> dict[str, Any] | None:
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
            if c.product_categories_name in ('母婴', '母嬰') and (c.parent_id is None or c.level == 1)
        ),
        None,
    )
    if root is None:
        root = next(
            (c for c in all_cats if c.product_categories_name in ('母婴', '母嬰')),
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
                'sections': _pane_sections_for_l2(l2, children_by_parent),
                'brands': brands,
            }
        )

    return {'tabs': tabs, 'root_name': root.product_categories_name}
