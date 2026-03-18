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
