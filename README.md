# 資料庫表設計

## 表結構總覽

以下 `user`、`user_address` 欄位與 Alembic 遷移 `a3c1d9f4b210_create_shop_user`、`f6b2a0c81d7e_create_shop_user_address` 及 `app.models` 一致。

| 表（Table） | 说明 | 字段（Columns） |
| --- | --- | --- |
| `user` | 用戶表 | `user_uuid`, `user_name`, `phone_number`, `mail`, `password_hash`, `create_time`, `salutation`, `birthday`, `nationality`, `communication_language`, `marketing_opt_out`, `brand_fortress`, `brand_parknshop`, `brand_watsons`, `brand_moneyback` |
| `user_address` | 用戶收貨地址 | `user_address_uuid`, `user_uuid`, `user_address`, `unit`, `floor`, `building_street`, `region`, `district`, `phone_number`, `home_phone`, `create_time` |
| `registration_verification_code` | 註冊驗證碼 | `id`, `client_ip`, `code`, `mail`, `created_at`, `expires_at`, `last_sent_at`, `consumed_at` |
| `membership` | 會員促銷/積分 | `user_uuid`, `membership_point`, `create_time` |
| `cart` | 購物車表 | `user_uuid`, `product_details_uuid`, `create_time` |
| `orders` | 訂單主表 | `order_uuid`, `user_uuid`, `order_status`, `receiver_name`, `receiver_phone`, `receiver_address_snapshot`, `total_price`, `create_time` |
| `order_items` | 訂單明細表 | `order_item_uuid`, `order_uuid`, `product_details_uuid`, `quantity`, `unit_price`, `line_total`, `create_time` |

## 約束（Constraints）

### 主键（PK）

- user: PK = user_uuid；`mail` 唯一（`uq_user_mail`）；索引 `ix_user_user_name`、`ix_user_phone_number`
- user_address: PK = user_address_uuid；索引 `ix_user_address_user_uuid`
- registration_verification_code: PK = id
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
- 密碼雜湊（`password_hash`）: `pbkdf2:sha256:...`
- 建立日期（`create_time`）: `2026:01:01:11:11:11`
- 稱謂（`salutation`）: `先生`（可空）
- 生日（`birthday`）: `1990-05-20`（可空）
- 國籍（`nationality`）: `中國香港`（可空）
- 通訊語言（`communication_language`）: `繁體`（預設）
- 拒收推廣（`marketing_opt_out`）: `false`（預設）
- 品牌訂閱 — 豐澤（`brand_fortress`）: `true`（預設）
- 品牌訂閱 — 百佳（`brand_parknshop`）: `true`（預設）
- 品牌訂閱 — 屈臣氏（`brand_watsons`）: `true`（預設）
- 品牌訂閱 — MoneyBack（`brand_moneyback`）: `true`（預設）

### 用戶收貨地址（`user_address`）

- 用戶收貨地址唯一識別符（`user_address_uuid`）: `8f0f4d4f-7f1e-4b6a-9a2a-2f1a7d9c3b10`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 完整地址文字（`user_address`）: `香港九龍尖沙咀彌敦道 100 號`（與表單合成展示用）
- 單位（`unit`）: `A`（可空）
- 樓層（`floor`）: `12`（可空）
- 大廈／街道（`building_street`）: `彌敦道 100 號某某大廈`（可空）
- 地區（`region`）: `九龍`（可空）
- 分區（`district`）: `油尖旺區`（可空）
- 聯絡電話（`phone_number`）: `91234567`（可空）
- 住宅電話（`home_phone`）: `21234567`（可空）
- 建立日期（`create_time`）: `2026:01:02:12:00:00`

### 註冊驗證碼（`registration_verification_code`）

- 主鍵（`id`）: `1`
- 申請時 IP（`client_ip`）: `203.0.113.10`
- 6 位驗證碼（`code`）: `042681`
- 註冊信箱（`mail`）: `xxxx@mail.com`
- 建立時間（`created_at`）: `2026-01-01T12:00:00+00:00`
- 驗證碼有效至（`expires_at`）: `2026-01-01T12:15:00+00:00`
- 最後寄出驗證信時間（`last_sent_at`）: `2026-01-01T12:00:05+00:00`（含「重新發送」時會更新）
- 完成註冊時間（`consumed_at`）: `2026-01-01T12:08:00+00:00`

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

## 新增配送、支付與評價相關表

| 表（Table） | 说明 | 字段（Columns） |
| --- | --- | --- |
| `delivery` | 商品配送 | `delivery_uuid`, `user_uuid`, `order_uuid`, `deliver_time`, `create_time` |
| `payment_log` | 支付日誌 | `payment_uuid`, `user_uuid`, `order_uuid`, `payment_methods`, `price`, `state`, `create_time` |
| `refund` | 售後退款 | `refund_uuid`, `order_uuid`, `user_uuid`, `create_time` |
| `evaluate` | 商品評價 | `evaluate_uuid`, `product_details_uuid`, `user_uuid`, `evaluate_txt`, `create_time` |

## 約束（Constraints）- 配送、支付與評價

### 主键（PK）

- delivery: PK = delivery_uuid
- payment_log: PK = payment_uuid
- refund: PK = refund_uuid
- evaluate: PK = evaluate_uuid

### 外键（FK）

- delivery.user_uuid -> user.user_uuid
- delivery.order_uuid -> orders.order_uuid
- payment_log.user_uuid -> user.user_uuid
- payment_log.order_uuid -> orders.order_uuid
- refund.user_uuid -> user.user_uuid
- refund.order_uuid -> orders.order_uuid
- evaluate.user_uuid -> user.user_uuid
- evaluate.product_details_uuid -> product_details.product_categories_uuid

## Sample Data (配送、支付與評價)

### 商品配送（`delivery`）

- 配送唯一識別符（`delivery_uuid`）: `9d1c7a0a-2b7a-4b7b-8c4e-4b8baf0c1e22`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 訂單唯一識別符（`order_uuid`）: `7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f`
- 配送時間（`deliver_time`）: `2026:01:05:10:00:00`
- 建立日期（`create_time`）: `2026:01:05:09:00:00`

### 支付日誌（`payment_log`）

- 支付唯一識別符（`payment_uuid`）: `3a4b3c2d-8d57-4b0f-9c6a-0f4a0f1d2c33`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 訂單唯一識別符（`order_uuid`）: `7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f`
- 支付方式（`payment_methods`）: `credit_card`
- 支付金額（`price`）: `25.50`
- 支付狀態（`state`）: `paid`
- 建立日期（`create_time`）: `2026:01:04:14:21:10`

### 售後退款（`refund`）

- 退款唯一識別符（`refund_uuid`）: `6b2e4f6b-3f12-4d1a-9c0f-7b0a0b1c2d3e`
- 訂單唯一識別符（`order_uuid`）: `7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 建立日期（`create_time`）: `2026:01:06:16:00:00`

### 商品評價（`evaluate`）

- 評價唯一識別符（`evaluate_uuid`）: `1f2e3d4c-5b6a-7c8d-9e0f-1a2b3c4d5e6f`
- 商品唯一識別符（`product_details_uuid`）: `dd7660db-700d-4b1a-866a-16e1cd2ee4dd`
- 用戶唯一識別符（`user_uuid`）: `55f7d0f9-fba6-4833-b113-8f55e069c5b6`
- 評價內容（`evaluate_txt`）: `送貨快，包裝完好，味道很好`
- 建立日期（`create_time`）: `2026:01:07:20:30:00`
