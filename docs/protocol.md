# 协议

`protocol_version` 当前为 **1**。改字段必须升版本，旧消息拒绝并写明原因。

M0 不执行用例。下面的任务消息和结果从现在起锁定，M1 的 `execute(task)` 按此实现。

## 任务消息

Runner 执行期间不回查平台数据库。平台投递时写入快照。

```json
{
  "protocol_version": 1,
  "execution_id": "uuid",
  "env_snapshot": {"base_url": "", "variables": {}},
  "case_snapshot": {},
  "strategy": {"mode": "sequential", "on_failure": "continue", "retry": 0},
  "limits": {"max_duration_sec": 60}
}
```

- `mode`：`sequential` 或 `parallel`
- `on_failure`：`abort` 或 `continue`。`abort` 时后续步骤标记跳过，不发请求
- 结果回传带 `execution_id`。同一 ID 重复回传忽略

## 执行结果

```json
{
  "protocol_version": 1,
  "execution_id": "uuid",
  "status": "SUCCESS",
  "started_at": "",
  "finished_at": "",
  "duration_ms": 0,
  "steps": [],
  "variables_snapshot": {},
  "error": ""
}
```

`status`：`SUCCESS`、`FAILED`、`TIMEOUT`。

`steps[]` 每步至少包含：请求、响应摘要、断言明细（类型、实际值、期望值、是否通过）、耗时、本步提取值、尝试次数。断言失败必须同时有实际值和期望值。

状态机：`PENDING → RUNNING → SUCCESS | FAILED | TIMEOUT`。

- 平台记录 `started_at + max_duration`，超时标 `TIMEOUT`
- `RUNNING` 超过 `max_duration × 2` 视为 Runner 崩溃，重新入队
- 重试仍用原来的 `execution_id`，对外只保留一条成功汇总

## 步骤 JSON（M1 使用，结构已锁定）

```json
{
  "request": {"method": "POST", "url": "/login", "headers": {}, "body": {}},
  "extracts": [{"name": "token", "from": "body", "jsonpath": "$.data.token"}],
  "assertions": [{"type": "status", "target": "", "op": "eq", "expect": 200}],
  "setup": [{"type": "sql", "statement": "SELECT 1"}],
  "teardown": [{"type": "wait", "ms": 100}]
}
```

- `extracts[].from` 为 `body` 时用 `jsonpath`，为文本时用 `regex`，二者只出现一个
- `assertions[].type`：`status`、`jsonpath`、`regex`、`contains`、`response_time`
- `setup` / `teardown` 的 `type`：`sql`、`wait`、`call_case`
- 未知字段拒绝

手工用例步骤是「序号 / 操作 / 预期」，不使用上面的结构。

## 变量

优先级：用例级 > 套件级 > 环境级 > 全局。

- 持久变量存在环境表，接口与 UI 共用
- 提取变量存在 `execution_variables`，只在本次执行内可见，结束即弃
- 禁止跨执行共享

## 认证

- Access 默认 1800 秒，Refresh 默认 604800 秒
- Redis：`refresh:{jti}` 保存 Refresh；轮换或登出写入 `blacklist:{jti}`，TTL 为剩余有效期
- 刷新时先查黑名单。轮换后旧 Refresh 立即失效
- 密码使用 bcrypt。`SECRET_KEY` 只来自环境变量

## 角色

平台角色：`admin` 管理员、`member` 成员、`readonly` 只读。第一个注册用户是管理员，之后注册的用户是成员。

项目角色：`owner` 负责人、`member` 成员、`readonly` 只读。

非成员访问项目返回 403。只读成员的写操作返回 403。管理员不受项目成员限制。

## M0 表

`users`、`projects`、`project_members`。其余表到对应里程碑再加。
