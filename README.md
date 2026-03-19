# 資料庫表設計

## 表結構總覽

| 表（Table） | 说明 | 字段（Columns） |
| --- | --- | --- |
| `user` | 用戶表 | `user_uuid`, `user_name`, `phone_number`, `mail`, `create_time` |
| `user_address` | 用戶收貨地址 | `user_address_uuid`, `user_uuid`, `user_address`, `phone_number`, `create_time` |
| `membership` | 會員促銷/積分 | `user_uuid`, `membership_point`, `create_time` |
| `cart` | 購物車表 | `user_uuid`, `product_details_uuid`, `create_time` |
| `orders` | 訂單主表 | `order_uuid`, `user_uuid`, `order_status`, `receiver_name`, `receiver_phone`, `receiver_address_snapshot`, `total_price`, `create_time` |
| `order_items` | 訂單明細表 | `order_item_uuid`, `order_uuid`, `product_details_uuid`, `quantity`, `unit_price`, `line_total`, `create_time` |

## 約束（Constraints）

### 主键（PK）

- user: PK = user_uuid
- user_address: PK = user_address_uuid
- membership: PK = user_uuid
- cart: PK = user_uuid, product_details_uuid
- orders: PK = order_uuid
- order_items: PK = order_item_uuid

### 外键（FK）

- user_address.user_uuid -> user.user_uuid
- membership.user_uuid -> user.user_uuid
- orders.user_uuid -> user.user_uuid
- order_items.order_uuid -> orders.order_uuid
- order_items.product_details_uuid -> product_details.product_categories_uuid
- cart.user_uuid -> user.user_uuid
- cart.product_details_uuid -> product_details.product_categories_uuid

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

### 訂單主表（`orders`）

- 訂單唯一識別符（`order_uuid`）: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 訂單狀態（`order_status`）: `pending`
- 收件人（`receiver_name`）: `user-1`
- 收件人電話（`receiver_phone`）: `12345678`
- 收貨地址快照（`receiver_address_snapshot`）: `香港xxxxxxxxxxxxxxxx`
- 訂單總價（`total_price`）: `100.00`
- 建立日期（`create_time`）: `2026:03:19:10:00:00`

### 訂單明細表（`order_items`）

- 訂單明細唯一識別符（`order_item_uuid`）: `b2c3d4e5-f6a7-8901-bcde-f23456789012`
- 訂單唯一識別符（`order_uuid`）: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- 商品明細唯一識別符（`product_details_uuid`）: `c3d4e5f6-a7b8-9012-cdef-345678901234`
- 購買數量（`quantity`）: `2`
- 單價（`unit_price`）: `50.00`
- 行小計（`line_total`）: `100.00`
- 建立日期（`create_time`）: `2026:03:19:10:00:00`
