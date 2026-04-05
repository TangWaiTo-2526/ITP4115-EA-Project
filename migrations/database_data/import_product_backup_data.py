"""
從本目錄的備份檔將資料寫入資料庫：supplier → product_categories → product_details。

備份檔須定義（與 product_backup 一致）：
  SUPPLIER_BACKUP_DATA
  PRODUCT_CATEGORY_BACKUP_DATA
  PRODUCT_BACKUP_DATA

支援檔名（擇一，優先順序如下）：
  product_backup_data.py
  product_backup_data（無副檔名）

在專案根目錄執行：
  python migrations/database_data/import_product_backup_data.py

若表內已有相同主鍵資料會報錯；要先整批重灌可加 --replace（會刪除三張表內既有列再匯入）。
"""

from __future__ import annotations

import argparse
import sys
import uuid
from decimal import Decimal
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent
_ROOT = _DATA_DIR.parent.parent

BACKUP_KEYS = ('SUPPLIER_BACKUP_DATA', 'PRODUCT_CATEGORY_BACKUP_DATA', 'PRODUCT_BACKUP_DATA')


def _resolve_backup_file() -> Path:
    for name in ('product_backup_data.py', 'product_backup_data'):
        p = _DATA_DIR / name
        if p.is_file() and p.stat().st_size > 0:
            return p
    for name in ('product_backup_data.py', 'product_backup_data'):
        p = _DATA_DIR / name
        if p.is_file():
            print(f'備份檔為空：{p}，請先儲存完整內容。', file=sys.stderr)
            sys.exit(1)
    print(
        f'找不到備份檔：請在 {_DATA_DIR} 放置 product_backup_data.py 或 product_backup_data',
        file=sys.stderr,
    )
    sys.exit(1)


def _load_namespace(path: Path) -> dict:
    ns: dict = {}
    exec(path.read_text(encoding='utf-8'), ns)
    return ns


def main() -> None:
    parser = argparse.ArgumentParser(description='將 product 備份寫入資料庫')
    parser.add_argument(
        '--replace',
        action='store_true',
        help='先清空 product_details、product_categories、supplier 再匯入',
    )
    parser.add_argument(
        '--path',
        type=Path,
        default=None,
        help='指定備份檔路徑（預設自動找本目錄下的 product_backup_data）',
    )
    args = parser.parse_args()

    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))

    backup_path = args.path.expanduser().resolve() if args.path else _resolve_backup_file()
    if args.path is not None:
        if not backup_path.is_file():
            print(f'找不到檔案：{backup_path}', file=sys.stderr)
            sys.exit(1)
        if backup_path.stat().st_size == 0:
            print(f'備份檔為空：{backup_path}', file=sys.stderr)
            sys.exit(1)

    ns = _load_namespace(backup_path)
    suppliers = ns.get('SUPPLIER_BACKUP_DATA') or []
    categories = ns.get('PRODUCT_CATEGORY_BACKUP_DATA') or []
    products = ns.get('PRODUCT_BACKUP_DATA') or []

    if not suppliers and not categories and not products:
        print('備份內沒有任何 SUPPLIER / CATEGORY / PRODUCT 資料。', file=sys.stderr)
        sys.exit(1)

    from app import app, db
    from app.models import ProductCategory, ProductDetail, Supplier

    with app.app_context():
        if args.replace:
            ProductDetail.query.delete()
            ProductCategory.query.delete()
            Supplier.query.delete()
            db.session.commit()

        for row in suppliers:
            db.session.add(
                Supplier(
                    supplier_id=row['supplier_id'],
                    supplier_name=row['supplier_name'],
                    supplier_png=row.get('supplier_png'),
                )
            )
        db.session.commit()

        for row in sorted(categories, key=lambda r: (r.get('level') or 0, r.get('product_categories_id') or 0)):
            db.session.add(
                ProductCategory(
                    product_categories_id=row['product_categories_id'],
                    product_categories_name=row['product_categories_name'],
                    parent_id=row.get('parent_id'),
                    level=row.get('level') or 1,
                )
            )
        db.session.commit()

        for row in products:
            disc = row.get('discount_price')
            db.session.add(
                ProductDetail(
                    product_categories_uuid=uuid.UUID(str(row['product_uuid'])),
                    product_categories_id=row['product_categories_id'],
                    supplier_id=row['supplier_id'],
                    product_name=row['product_name'],
                    specification=row.get('specification'),
                    image_path=row.get('image_path'),
                    product_details=row.get('product_details'),
                    price=Decimal(str(row['price'])),
                    discount_price=Decimal(str(disc)) if disc is not None else None,
                )
            )
        db.session.commit()

    print(
        f'已從 {backup_path.name} 匯入：supplier {len(suppliers)}、'
        f'category {len(categories)}、product {len(products)} 筆。'
        + ('（已使用 --replace）' if args.replace else '')
    )


if __name__ == '__main__':
    main()
