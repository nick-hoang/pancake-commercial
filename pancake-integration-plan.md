# Pancake Integration Plan

Tài liệu này chuyển hóa contract trong `references/pancake-api-contract.md` thành kế hoạch scaffold bộ tool thực tế cho repo.

## 1. Mục tiêu

Biến repo hiện tại từ:
- skill spec
- tài liệu nghiệp vụ
- một template Python tối giản

thành một gói tích hợp có thể:
- gọi REST API của Pancake
- nhận webhook từ Pancake
- chạy monitor logic 20/40/60
- gửi alert ra kênh ngoài
- thực hiện stage 3 handoff an toàn

## 2. Nguyên tắc triển khai

- Bám sát contract trong `references/pancake-api-contract.md`
- Tách rõ user-scoped API và page-scoped API
- Dùng `page_access_token` qua query param cho page APIs
- Ưu tiên polling chạy ổn định trước, webhook sau
- Mọi thao tác write phải có `dry_run`
- Mọi workflow phải idempotent
- Không log token hoặc raw URL chứa token

## 3. Kiến trúc đề xuất

Đề xuất package Python mới:

```text
src/pancake_commercial/
  config.py
  models.py
  errors.py
  logging.py
  client/
    base.py
    user_api.py
    page_api_v1.py
    page_api_v2.py
  domain/
    conversations.py
    messages.py
    roles.py
    stages.py
    handoff.py
    intents.py
    noise.py
  alerts/
    base.py
    telegram.py
    slack.py
    discord.py
  runtime/
    state_store.py
    poller.py
    webhook_server.py
    dedupe.py
  tools/
    pages.py
    conversations.py
    messages.py
    tags.py
    users.py
    handoff.py
    monitor.py
  cli.py
tests/
```

## 4. Deliverables theo phase

### Phase 0 — Khóa contract và tài liệu

Deliverables:
- `references/pancake-api-contract.md`
- `pancake-integration-plan.md`

Mục tiêu:
- chốt auth
- chốt endpoint scope
- chốt webhook assumptions

### Phase 1 — API client nền

Deliverables:
- `BaseClient`
- `UserApiClient`
- `PageApiClientV1`
- `PageApiClientV2`
- model cấu hình
- model dữ liệu chuẩn hóa
- error mapping nội bộ

Yêu cầu:
- gắn token vào query params tự động
- timeout và retry tối thiểu
- redact token trong log
- có unit tests cho request builder

### Phase 2 — Read-only tools

Deliverables:
- tool list pages
- tool list conversations
- tool list messages
- tool list tags
- tool list users
- healthcheck command

Mục tiêu:
- xác minh được kết nối thật với Pancake
- có dữ liệu đủ để xây monitor logic

### Phase 3 — Write tools

Deliverables:
- add tag
- remove tag
- assign conversation
- mark read
- mark unread
- send message

Yêu cầu:
- `dry_run` hỗ trợ cho mọi write action
- response phải được chuẩn hóa
- integration tests ưu tiên cho tag mutation

### Phase 4 — Domain logic cho reminder workflow

Deliverables:
- parse timestamp
- normalize conversations/messages
- detect customer latest unanswered message
- role resolution customer/staff/system
- wait time calculator
- stage resolver 20/40/60
- handoff orchestrator

Yêu cầu:
- stage phải tuần tự
- không nhảy cóc
- không alert khi sale đã reply sau tin khách cuối

### Phase 5 — State store và monitor runtime

Deliverables:
- state store SQLite
- `monitor_run_once`
- `monitor_run_loop`
- audit log tối thiểu

State tối thiểu cần lưu:
- `page_id`
- `conversation_id`
- `last_customer_message_id`
- `last_customer_message_at`
- `last_notified_stage`
- `last_alert_at`
- `handoff_done`
- `last_processed_at`

### Phase 6 — Alert adapters

Deliverables:
- `AlertSender` interface
- Telegram adapter production-ready
- Slack/Discord adapter ở mức tối thiểu hoặc stub

Ưu tiên:
- Telegram trước

Payload alert nên gồm:
- page name / page id
- conversation id
- customer name
- staff hiện tại
- excerpt tin khách
- wait time
- stage
- hành động đề xuất
- trạng thái handoff nếu có

### Phase 7 — Webhook ingestion

Deliverables:
- webhook receiver HTTP server
- payload parser cho `messaging`, `subscription`, `post`
- dedupe layer
- enqueue/background processing

Nguyên tắc:
- trả `200` thật nhanh
- xử lý async
- coi delivery là `at least once`
- không giả định có signature verification từ Pancake

### Phase 8 — Reconciliation giữa polling và webhook

Deliverables:
- cơ chế hợp nhất event source
- polling định kỳ để chống miss event
- webhook chỉ là source tín hiệu real-time

Quy tắc:
- webhook không thay thế polling hoàn toàn
- polling là source of truth để self-heal

## 5. Tool surface cho OpenClaw

Các tool nên expose ở mức người dùng/agent:
- `pancake_pages_list`
- `pancake_conversations_list`
- `pancake_messages_list`
- `pancake_tags_list`
- `pancake_users_list`
- `pancake_conversation_add_tag`
- `pancake_conversation_remove_tag`
- `pancake_conversation_assign`
- `pancake_conversation_mark_read`
- `pancake_conversation_mark_unread`
- `pancake_conversation_send_message`
- `pancake_monitor_run_once`
- `pancake_monitor_run_loop`
- `pancake_webhook_serve`
- `pancake_healthcheck`

## 6. Cấu hình cần thiết

Config production nên mở rộng từ file mẫu hiện tại thành:

```json
{
  "pages": [
    {
      "name": "example-page",
      "page_id": "YOUR_PAGE_ID",
      "page_access_token": "YOUR_PAGE_ACCESS_TOKEN",
      "enabled": true,
      "timezone": "Asia/Bangkok"
    }
  ],
  "staff_mapping": {
    "SALE_A": {
      "name": "Sale A",
      "tag_id": "101",
      "alert_target": "@sale_a",
      "user_id": "optional-pancake-user-id"
    }
  },
  "rules": {
    "stage_1_minutes": 20,
    "stage_2_minutes": 40,
    "stage_3_minutes": 60,
    "noise_patterns": ["xin chao", "da", "ok"],
    "working_hours": {
      "start": "08:00",
      "end": "19:00"
    }
  },
  "alerts": {
    "provider": "telegram",
    "telegram_bot_token": "ENV_ONLY",
    "telegram_chat_id": "ENV_ONLY"
  },
  "runtime": {
    "dry_run": true,
    "poll_interval_seconds": 300,
    "state_backend": "sqlite",
    "state_path": ".pancake_monitor_state.sqlite"
  }
}
```

## 7. Quy tắc model nội bộ

Cần chuẩn hóa dữ liệu vào model nội bộ thay vì phụ thuộc trực tiếp vào payload gốc.

Model tối thiểu:
- `PageConfig`
- `StaffMapping`
- `NormalizedConversation`
- `NormalizedMessage`
- `StageDecision`
- `HandoffPlan`
- `WebhookEnvelope`

Lợi ích:
- cùng một domain logic dùng được cho cả REST polling và webhook events

## 8. Rủi ro kỹ thuật cần xử lý sớm

### 8.1. Sender role ambiguity

Spec chưa có field phân loại sender rõ ràng.

Giải pháp:
- resolver dựa trên `conversation.from.id`
- fallback đối chiếu với users API
- thêm config override cho các trường hợp đặc biệt

### 8.2. Token trong query string

Rủi ro:
- dễ lộ qua logs

Giải pháp:
- redact triệt để
- không log full URL
- tách log request metadata và params an toàn

### 8.3. Webhook duplicate delivery

Rủi ro:
- alert lặp
- handoff lặp

Giải pháp:
- dedupe store
- idempotent key theo `event_type + page_id + message.id`

### 8.4. Thiếu rate-limit contract

Rủi ro:
- bị throttling ngoài tài liệu

Giải pháp:
- concurrency thấp
- retry with jitter
- exponential backoff cho lỗi mạng và 5xx

### 8.5. Thiếu error schema chuẩn

Rủi ro:
- khó phân loại lỗi

Giải pháp:
- log raw error payload đã redact
- map status code + message text vào lỗi nội bộ
- mở rộng sau khi có integration test thật

## 9. Kế hoạch test

### 9.1. Unit tests

- query param auth injection
- token redaction
- conversation pagination cursor builder
- message pagination builder
- stage transition logic
- role resolution logic
- handoff success/failure logic

### 9.2. Fixture tests

- parse conversation payload từ REST
- parse message payload từ REST
- parse webhook `messaging`
- parse webhook `post`
- parse webhook `subscription`

### 9.3. Integration tests

Chỉ chạy khi có token thật trong env:
- list conversations
- list messages
- list tags
- list users
- add/remove tag trên sandbox conversation

### 9.4. Manual verification

- webhook endpoint nhận được `messaging`
- endpoint trả `200` trong dưới 5 giây
- duplicate delivery không tạo alert trùng
- stage 3 không handoff sai nếu tag mutation lỗi nửa chừng

## 10. Thứ tự triển khai khuyến nghị

Thứ tự thực hiện thực tế:
1. tạo package Python và base clients
2. thêm read-only tools
3. thêm tag mutation + assign
4. thêm state store + `monitor_run_once`
5. thêm Telegram adapter
6. thêm webhook receiver
7. thêm reconciliation giữa polling và webhook
8. cập nhật README, SKILL.md, templates

## 11. Tiêu chí hoàn thành tối thiểu

Có thể coi integration hoàn thành mức đầu nếu:
- gọi được conversations/messages/tags/users bằng token thật
- chạy `monitor_run_once` trên ít nhất 1 page
- tạo được alert stage 1 đúng logic
- handoff stage 3 add/remove tag đúng và idempotent
- webhook `messaging` được ingest an toàn
- không lộ token trong logs

## 12. Việc nên làm ngay sau khi scaffold xong

- cập nhật `SKILL.md` để chỉ vào runtime mới thay vì chỉ template
- cập nhật `README.md` với quickstart production
- mở rộng `templates/config.pages.example.json`
- giữ `templates/pancake_monitor_template.py` như file demo, không phải implementation chính
