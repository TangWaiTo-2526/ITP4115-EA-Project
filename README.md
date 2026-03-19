# 資料庫表設計

## 表結構總覽

| 表（Table） | 说明 | 字段（Columns） |
| --- | --- | --- |
| `user` | 用戶表 | `user_uuid`, `user_name`, `phone_number`, `mail`, `create_time` |
| `user_address` | 用戶收貨地址 | `user_address_uuid`, `user_uuid`, `user_address`, `phone_number`, `create_time` |
| `membership` | 會員促銷/積分 | `user_uuid`, `membership_point`, `create_time` |

## 約束（Constraints）

### 主键（PK）

- user: PK = user_uuid
- user_address: PK = user_address_uuid
- membership: PK = user_uuid

### 外键（FK）

- user_address.user_uuid -> user.user_uuid
- membership.user_uuid -> user.user_uuid

## Sample Data

### 用戶表（`user`）

- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 用戶名字（`user_name`）: `user-1`
- 用戶電話號碼（`phone_number`）: `12345678`
- 用戶電子郵箱（`mail`）: `xxxx@mail.com`
- 建立日期（`create_time`）: `2026:01:01:11:11:11`

### 用戶收貨地址（`user_address`）

- 用戶收貨地址唯一識別符（`user_address_uuid`）: `8f0f4d4f-7f1e-4b6a-9a2a-2f1a7d9c3b10`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 用戶收貨地址（`user_address`）: `香港xxxxxxxxxxxxxxxx`
- 收貨電話（`phone_number`）: `12345678`
- 建立日期（`create_time`）: `2026:01:02:12:00:00`

### 會員促銷/積分（`membership`）

- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 會員積分（`membership_point`）: `1200`
- 建立日期（`create_time`）: `2026:01:01:11:11:11`

## 新增商品相關表

| 表（Table） | 说明 | 字段（Columns） |
| --- | --- | --- |
| `product_categories` | 貨物分類 | `product_categories_id`, `product_categories_name`, `create_time` |
| `supplier` | 供應商 | `supplier_id`, `supplier_name`, `supplier_png`, `create_time` |
| `product_details` | 貨物詳情 | `product_categories_uuid`, `product_categories_id`, `supplier_id`, `product_name`, `product_details`, `price`, `create_time` |

## Sample Data (商品)

### 貨物分類（`product_categories`）

- 商品分類識別符（`product_categories_id`）：3
- 商品分類名字（`product_categories_name`）：飲品
- 建立日期（`create_time`）：2026:01:03:09:30:00

### 供應商（`supplier`）

- 供應商識別符（`supplier_id`）：1
- 供應商名字（`supplier_name`）：可口可樂代理商
- 供應商圖片（`supplier_png`）：coke-supplier.png
- 建立日期（`create_time`）：2026:01:03:10:00:00

### 貨物詳情（`product_details`）

- 商品分類識別符（`product_categories_id`）：3
- 供應商識別符（`supplier_id`）：1
- 商品唯一識別符（`product_categories_uuid`）：dd7660db-700d-4b1a-866a-16e1cd2ee4dd
- 商品名稱（`product_name`）：可樂
- 商品詳情（`product_details`）：330ml 罐裝，冰鎮更佳
- 商品單價（`price`）：8.50
- 建立日期（`create_time`）：2026:01:03:11:00:00
