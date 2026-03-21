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

### 購物車表（`cart`）

- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 商品唯一識別符（`product_details_uuid`）: `dd7660db-700d-4b1a-866a-16e1cd2ee4dd`
- 建立日期（`create_time`）: `2026:01:03:12:00:00`

### 訂單主表（`orders`）

- 訂單唯一識別符（`order_uuid`）: `e8a5f1d9-c2a5-4f07-b31f-1e18c6cded1b`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 訂單狀態（`order_status`）: `pending`
- 收件人（`receiver_name`）: `王小明`
- 收件人電話（`receiver_phone`）: `91234567`
- 收貨地址快照（`receiver_address_snapshot`）: `香港九龍尖沙咀...`
- 訂單總價（`total_price`）: `25.00`
- 建立日期（`create_time`）: `2026:01:04:13:00:00`

### 訂單明細表（`order_items`）

- 訂單明細唯一識別符（`order_item_uuid`）: `f1a7b2c3-d4e5-4f67-a8b9-0123456789ab`
- 所屬訂單（`order_uuid`）: `e8a5f1d9-c2a5-4f07-b31f-1e18c6cded1b`
- 商品唯一識別符（`product_details_uuid`）: `dd7660db-700d-4b1a-866a-16e1cd2ee4dd`
- 購買數量（`quantity`）: `2`
- 單價（`unit_price`）: `8.50`
- 行小計（`line_total`）: `17.00`
- 建立日期（`create_time`）: `2026:01:04:13:01:00`

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

【商品配送表格(delivery)】
配送唯一識別符(delivery_uuid): 9d1c7a0a-2b7a-4b7b-8c4e-4b8baf0c1e22
用戶唯一識別符(user_uuid): 55f7d0f9-fba6-4833-b113-8f55e069c5b6
訂單唯一識別符(order_uuid): 7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f
配送時間(deliver_time): 2026:01:05:10:00:00
建立日期(create_time): 2026:01:05:09:00:00


【支付日誌(payment_log)】
支付唯一識別符(payment_uuid): 3a4b3c2d-8d57-4b0f-9c6a-0f4a0f1d2c33
用戶唯一識別符(user_uuid): 55f7d0f9-fba6-4833-b113-8f55e069c5b6
訂單唯一識別符(order_uuid): 7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f
支付方式(payment_methods): credit_card
支付金額(price): 25.50
支付狀態(state): paid
建立日期(create_time): 2026:01:04:14:21:10

【售後/退款表格(refund)】
退款唯一識別符(refund_uuid): 6b2e4f6b-3f12-4d1a-9c0f-7b0a0b1c2d3e
訂單唯一識別符(order_uuid): 7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f
用戶唯一識別符(user_uuid): 55f7d0f9-fba6-4833-b113-8f55e069c5b6
建立日期(create_time): 2026:01:06:16:00:00



【商品用後評價(evaluate)】
評價唯一識別符(evaluate_uuid): 1f2e3d4c-5b6a-7c8d-9e0f-1a2b3c4d5e6f
商品唯一識別符(product_details_uuid): dd7660db-700d-4b1a-866a-16e1cd2ee4dd
用戶唯一識別符(user_uuid): 55f7d0f9-fba6-4833-b113-8f55e069c5b6
評價內容(evalate_txt): 送貨快，包裝完好，味道很好
建立日期(create_time): 2026:01:07:20:30:00
