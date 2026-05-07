# 智盾 Agent 前后端联调放开顺序

本文档与 `src/api/services.ts`、`src/types/api.ts` 对齐，目标是完成：

1. 接入真实大模型调用链；
2. 输入阶段结合真实注册工具进行风险判断；
3. 决策过程实时写入证据链并反映到报告；
4. Dashboard / EventList / AuditDetail 等页面统一实时更新。

## 阶段一：已有基础接口（当前可联调）

- `fetchDashboardOverview`
- `fetchRiskMatrixSummary`
- `createChatSession`
- `sendChatMessage`
- `listSecurityEvents`
- `getAuditEventDetail`
- `requestAuditReport`

建议先保证：`sendChatMessage` 返回 `ChatMessageResponse`，其中 `assistant` 至少包含：

- `riskScoreR`
- `scoreBreakdown`
- `isBlock` / `isMasked`
- `eventId`

## 阶段二：策略引擎与工具注册

放开：

- `listRegisteredTools`
- `evaluateInputRisk`

后端需对齐类型：

- `RegisteredTool[]`
- `InputRiskEvaluateRequest`
- `InputRiskEvaluateResponse`

目标：输入时基于真实工具注册信息（工具级别、角色、参数约束）参与判定。

## 阶段三：审计闭环与实时快照

放开：

- `appendAuditTrace`
- `getAuditReportJobStatus`
- `fetchDashboardRealtimeSnapshot`

后端需对齐类型：

- `AppendAuditTraceRequest / AppendAuditTraceResponse`
- `ReportJobStatusResponse`
- `DashboardRealtimeSnapshot`

目标：决策步骤增量写入 -> 证据链详情可追踪 -> 报告状态可轮询 -> 总览可统一刷新。

## 阶段四：SSE 实时推送（注释块）

在 `services.ts` 解除 `subscribeSecurityStream` 注释前，请确认后端已提供：

- `GET /api/v1/security/stream`（`text/event-stream`）
- 事件 payload 对齐 `SecurityRealtimeEvent`

建议事件类型：

- `event.created`
- `event.updated`
- `dashboard.updated`
- `report.updated`
- `audit.trace.appended`

这样可实现多页面统一实时更新（建议配合 Pinia 单一状态源）。

## 一键切换（轮询 / 推送）

本项目已内置统一实时 store：`src/stores/securityRealtime.ts`。

通过环境变量切换模式即可，无需逐页改代码：

- `VITE_SECURITY_REALTIME_MODE=auto`（默认，优先推送，失败自动降级轮询）
- `VITE_SECURITY_REALTIME_MODE=push`（强制 SSE）
- `VITE_SECURITY_REALTIME_MODE=poll`（强制轮询）
- `VITE_SECURITY_POLL_INTERVAL_MS=5000`（轮询间隔，可调）
