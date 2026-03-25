# Pancake API Contract

Tài liệu này tổng hợp contract tích hợp Pancake dựa trên 2 nguồn spec chuẩn trong repo:
- `pancake-openapi-document-bundled.yaml` — REST API
- `pancake-webhook-openapi-document-bundled.yaml` — Webhook API

Mục tiêu của tài liệu này là khóa các giả định kỹ thuật trước khi scaffold bộ tool production cho OpenClaw.

## 1. Base URLs và cơ chế xác thực

Pancake dùng 3 base URL:
- `https://pages.fm/api/v1` — user-scoped API
- `https://pages.fm/api/public_api/v1` — page-scoped API v1
- `https://pages.fm/api/public_api/v2` — page-scoped API v2

### 1.1. User access token

Dùng cho các API cấp tài khoản:
- `GET /pages`
- `POST /pages/{page_id}/generate_page_access_token`

Auth được truyền bằng query param:
- `access_token`

### 1.2. Page access token

Dùng cho các page-scoped API như conversations, messages, tags, users.

Auth được truyền bằng query param:
- `page_access_token`

Yêu cầu implementation:
- Không dùng `Authorization` header làm mặc định cho Pancake page APIs.
- Mọi logger phải redact `page_access_token` và `access_token` khỏi URL log vì token nằm trong query string.

## 2. REST endpoints cần cho skill hiện tại

Use case hiện tại của skill chỉ cần một tập con của Pancake APIs.

### 2.1. Page discovery và bootstrap

- `GET /pages`
  - base URL: `https://pages.fm/api/v1`
  - auth: `access_token`
  - mục đích: liệt kê pages để onboarding hoặc verify cấu hình

- `POST /pages/{page_id}/generate_page_access_token`
  - base URL: `https://pages.fm/api/v1`
  - auth: `access_token`
  - params: `page_id`
  - mục đích: sinh hoặc refresh `page_access_token`

### 2.2. Conversations

- `GET /pages/{page_id}/conversations`
  - base URL: `https://pages.fm/api/public_api/v2`
  - auth: `page_access_token`
  - trả về tối đa 60 conversations mỗi request

Query/filter hợp lệ:
- `last_conversation_id`
- `tags`
- `type`
- `post_ids`
- `since`
- `until`
- `unread_first`
- `order_by`

Ý nghĩa:
- `last_conversation_id`: cursor lấy trang tiếp theo theo hướng cũ hơn
- `tags`: string comma-separated tag IDs
- `type`: mảng loại hội thoại, ví dụ `INBOX`, `COMMENT`
- `post_ids`: filter theo post IDs
- `since` / `until`: unix timestamp, đơn vị giây
- `unread_first`: ưu tiên unread conversations
- `order_by`: `inserted_at` hoặc `updated_at`

Pagination:
- không có `limit`
- không có `offset`
- không có `cursor` kiểu opaque token
- dùng `last_conversation_id` để đi tiếp

### 2.3. Conversation tag mutation

- `POST /pages/{page_id}/conversations/{conversation_id}/tags`
  - base URL: `https://pages.fm/api/public_api/v1`
  - auth: `page_access_token`

Payload:
```json
{
  "action": "add",
  "tag_id": "123"
}
```

`action` hợp lệ:
- `add`
- `remove`

Response:
- `data`: danh sách tag IDs sau update
- `success`: boolean
- `timestamp`: integer

Contract vận hành cho skill:
- Stage 3 handoff phải kiểm tra `success == true`.
- Không coi handoff hoàn tất nếu một trong hai bước remove/add thất bại.

### 2.4. Assign conversation

- `POST /pages/{page_id}/conversations/{conversation_id}/assign`
  - base URL: `https://pages.fm/api/public_api/v1`
  - auth: `page_access_token`

Payload:
```json
{
  "assignee_ids": ["user-id-1", "user-id-2"]
}
```

Hiện chưa phải luồng bắt buộc của skill, nhưng nên thiết kế sẵn vì có thể thay handoff tag bằng assign về sau.

### 2.5. Mark read / unread

- `POST /pages/{page_id}/conversations/{conversation_id}/read`
- `POST /pages/{page_id}/conversations/{conversation_id}/unread`

Hiện không phải thao tác bắt buộc của logic nhắc sale, nhưng nên có tool vì có thể dùng trong admin workflows.

### 2.6. Messages

- `GET /pages/{page_id}/conversations/{conversation_id}/messages`
  - base URL: `https://pages.fm/api/public_api/v1`
  - auth: `page_access_token`

Query:
- `current_count`

Pagination:
- mỗi call trả 30 messages lùi về trước từ vị trí `current_count`
- không có `offset` và `limit` cho message API chính

### 2.7. Send message

- `POST /pages/{page_id}/conversations/{conversation_id}/messages`
  - base URL: `https://pages.fm/api/public_api/v1`
  - auth: `page_access_token`

Spec cho phép 4 kiểu payload:
- `InboxMessage`
- `ReplyComment`
- `PrivateReply`
- `WhatsappTemplateMessage`

#### InboxMessage

```json
{
  "action": "reply_inbox",
  "message": "Xin chao"
}
```

Optional fields:
- `content_ids`
- `sender_id`
- `reply_message_id`

Ràng buộc quan trọng:
- `message` và `content_ids` là mutually exclusive
- gửi đồng thời cả hai có thể gây `500 error`

#### ReplyComment

```json
{
  "action": "reply_comment",
  "message_id": "comment-id",
  "message": "Noi dung reply"
}
```

Optional fields:
- `content_ids`
- `sender_id`
- `mentions`

#### PrivateReply

```json
{
  "action": "private_replies",
  "post_id": "post-id",
  "message_id": "comment-id",
  "message": "Noi dung private reply"
}
```

Optional fields:
- `from_id`
- `sender_id`

#### WhatsappTemplateMessage

```json
{
  "action": "reply_inbox",
  "template_id": "approved-template-id"
}
```

Optional fields:
- `conversation_id`
- `template_params`
- `sender_id`

Kết luận cho repo hiện tại:
- skill reminder hiện chưa cần tool gửi message để hoạt động cốt lõi
- nhưng nên scaffold sẵn vì có thể dùng sau này cho auto-reply/handoff messaging

### 2.8. Metadata endpoints cần cho orchestration

- `GET /pages/{page_id}/tags`
  - dùng để resolve `tag_id -> tag_name`

- `GET /pages/{page_id}/users`
  - dùng để map `user_id -> staff info`
  - dùng để phân biệt message của staff so với customer trong tầng ứng dụng

## 3. Schema dữ liệu cốt lõi

### 3.1. Conversation schema

REST conversation schema có các field chính:
- `id`
- `type`
- `page_uid`
- `updated_at`
- `inserted_at`
- `tags`
- `last_message.text`
- `last_message.sender`
- `last_message.created_at`
- `participants[]`

Webhook conversation schema giàu hơn và hữu ích hơn cho runtime:
- `id`
- `assignee_ids`
- `from`
- `is_combined`
- `is_removed`
- `is_replied`
- `read_watermarks`
- `seen`
- `snippet`
- `tags`
- `type`

Khuyến nghị implementation:
- tạo model nội bộ `NormalizedConversation`
- merge các field REST và webhook vào cùng một shape thống nhất

### 3.2. Message schema

REST message schema:
- `conversation_id`
- `from`
- `has_phone`
- `inserted_at`
- `is_hidden`
- `is_removed`
- `message`
- `page_id`
- `type`

Webhook message schema giàu hơn:
- `id`
- `conversation_id`
- `page_id`
- `message`
- `original_message`
- `rich_message`
- `type`
- `inserted_at`
- `from.id`
- `from.name`
- `from.page_customer_id`
- `attachments`
- `has_phone`
- `phone_info`
- `is_hidden`
- `is_parent`
- `is_parent_hidden`
- `is_removed`
- `like_count`
- `user_likes`
- `edit_history`
- `parent_id`
- `private_reply_conversation`
- `removed_by`
- `show_info`
- `can_comment`
- `can_hide`
- `can_like`
- `can_remove`
- `can_reply_privately`

Khuyến nghị implementation:
- tạo model nội bộ `NormalizedMessage`
- chấp nhận cả payload nghèo hơn từ REST lẫn payload giàu hơn từ webhook

## 4. Phân biệt customer, staff và system message

Spec không cung cấp field chuẩn hóa như:
- `sender_role`
- `is_staff`
- `is_customer`
- `is_system`

`message.type` trong webhook chỉ cho biết ngữ cảnh:
- `INBOX`
- `COMMENT`

Nó không cho biết sender là customer hay sale.

Contract suy luận an toàn cho application layer:
- customer message:
  - ưu tiên xác định bằng `message.from.id == conversation.from.id`
- staff message:
  - xác định bằng cách đối chiếu `message.from.id` với `/pages/{page_id}/users`
- system message:
  - không có schema chuẩn hóa trong spec
  - phải dùng rules nội bộ theo pattern text, metadata thực tế, hoặc allowlist/denylist sender

Khuyến nghị implementation:
- đóng gói logic trong `MessageRoleResolver`
- không hard-code dựa riêng vào `type`
- cho phép override qua config nếu gặp page/platform đặc thù

## 5. Webhook contract

Pancake Webhooks gửi HTTP `POST` tới endpoint đã đăng ký khi có event mới.

### 5.1. Event types

Spec xác nhận 3 event:
- `messaging`
- `subscription`
- `post`

Use case của skill hiện tại chủ yếu dùng:
- `messaging`

### 5.2. Messaging webhook payload

Payload chuẩn:
```json
{
  "page_id": "page-id",
  "event_type": "messaging",
  "data": {
    "conversation": {},
    "message": {},
    "post": null
  }
}
```

Quy tắc:
- `data.post` chỉ có ý nghĩa khi conversation/message là `COMMENT`
- với `INBOX`, `data.post` có thể là `null`

### 5.3. Subscription webhook payload

Payload:
```json
{
  "event_type": "subscription",
  "data": {
    "subscription": {}
  }
}
```

Use case hiện tại:
- không bắt buộc cho reminder logic
- có thể dùng sau này cho admin monitoring

### 5.4. Post webhook payload

Payload:
```json
{
  "page_id": "page-id",
  "event_type": "post",
  "data": {
    "post": {}
  }
}
```

Use case hiện tại:
- không phải thành phần cốt lõi
- có thể hữu ích nếu sau này muốn đồng bộ comment-related metadata

## 6. Webhook delivery behavior

### 6.1. Acknowledgement

Endpoint nhận webhook phải:
- chấp nhận HTTP `POST`
- trả `HTTP 200` để xác nhận đã nhận event

Nếu không trả `2xx`, request bị coi là failure.

### 6.2. Failure conditions

Một lần delivery bị tính là failed nếu:
- endpoint trả HTTP ngoài `2xx`
- endpoint timeout hoặc không phản hồi
- có network connection error khi Pancake gửi request

### 6.3. Automatic suspension

Webhook có thể bị tự động suspend nếu trong 30 phút:
- error rate > 80%
- số failed requests >= 300

Sau khi bị suspend:
- Pancake ngừng gửi webhook events tới endpoint
- phải vào Webhook Settings để enable lại thủ công

### 6.4. Retry semantics

Spec không công bố retry schedule/backoff cụ thể.

Tuy nhiên spec khuyến nghị:
- xử lý theo hướng idempotent
- chấp nhận việc một event có thể được gửi hơn một lần

Contract vận hành:
- coi webhook delivery là `at least once`
- không được giả định `exactly once`
- cần có cơ chế dedupe theo event fingerprint nội bộ

## 7. Signature verification và bảo mật inbound webhook

Spec webhook hiện không mô tả:
- header chữ ký
- shared secret
- HMAC validation
- timestamp signature

Vì vậy contract hiện tại phải coi:
- không có security primitive chuẩn từ spec để verify sender

Khuyến nghị triển khai:
- dùng endpoint path secret hoặc reverse-proxy secret
- giới hạn IP nếu hạ tầng cho phép
- ghi audit log cho raw inbound metadata đã redact

## 8. Rate limit, throttling và error conventions

### 8.1. REST rate limit

Spec hiện không mô tả:
- `429 Too Many Requests`
- `Retry-After`
- `X-RateLimit-*`
- burst/window quota

Kết luận:
- chưa có contract rate limit chính thức từ spec
- client phải tự bảo vệ bằng retry/backoff thận trọng và concurrency thấp

### 8.2. Webhook throttling

Spec không mô tả rate limit webhook.

Behavior gần nhất là:
- suspend webhook khi error rate quá cao

### 8.3. Error schema

REST spec đa số chỉ khai báo response `200`.
Spec không cung cấp error body schema chuẩn hóa.

Một behavior lỗi cụ thể đã biết:
- nếu gửi cả `message` và `content_ids` trong inbox send-message request, API có thể trả `500 error`

Contract client nên chuẩn hóa lỗi nội bộ thành:
- `AuthError`
- `PermissionError`
- `ValidationError`
- `NotFoundError`
- `RateLimitError`
- `ServerError`
- `NetworkError`

Việc map các lỗi trên sẽ phải dựa trên status code thực tế khi test integration.

## 9. Quy tắc code-level cho bộ tool

### 9.1. Base client

Base client phải:
- tự gắn `page_access_token` hoặc `access_token` vào query params
- redact token khi log
- set timeout ngắn và retry có kiểm soát
- hỗ trợ `dry_run` cho write actions

### 9.2. Read/write split

Tách riêng:
- `UserApiClient` cho `/api/v1`
- `PageApiClientV1` cho `/api/public_api/v1`
- `PageApiClientV2` cho `/api/public_api/v2`

Lý do:
- conversations nằm ở v2
- nhiều write endpoints nằm ở v1

### 9.3. Idempotency

Các thao tác cần idempotent ở application layer:
- webhook ingestion
- alert dispatch
- stage transition
- stage 3 handoff tag mutation

### 9.4. Monitoring strategy

Không dùng webhook-only.

Chiến lược đúng cho skill này:
- webhook để nhận tín hiệu gần real-time
- polling định kỳ để reconciliation và chống miss event

## 10. Scope tối thiểu để scaffold Phase 1

Phase 1 chỉ cần:
- list pages
- list conversations
- list messages
- list tags
- list users
- add/remove tag
- assign conversation
- read/unread
- monitor run once

Webhook server nên làm ở Phase 2, nhưng data model phải chuẩn bị ngay từ đầu để nhận được cả REST payload lẫn webhook payload.

## 11. Những điểm vẫn cần xác minh bằng integration test thật

Spec đã đủ để scaffold, nhưng vẫn còn các điểm chỉ có thể khóa bằng test thật:
- status code thực tế khi token sai/hết quyền
- format error body thực tế
- serialization thật của array query params như `type` và `post_ids`
- mức độ ổn định của `message.from.id` khi sender là staff
- hình dạng dữ liệu system message ngoài docs
- có hay không duplicate webhook trong thực tế
- ngưỡng timeout thực tế của webhook delivery

## 12. Kết luận vận hành

Contract hiện tại đủ để bắt đầu scaffold bộ tool production cho repo này với các nguyên tắc:
- page-scoped auth qua query param `page_access_token`
- polling + webhook hybrid
- dedupe và idempotency là bắt buộc
- không phụ thuộc vào error schema/rate limit từ spec
- tách role resolution vào tầng ứng dụng, không dựa mù vào `message.type`
