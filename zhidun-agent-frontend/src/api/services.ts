import { USE_MOCK } from '@/config/env';
import { request } from '@/api/client';
import * as mock from '@/api/backendMock';
import type {
  AgentApp,
  AlertRoute,
  AppendAuditTraceRequest,
  AppendAuditTraceResponse,
  AuditEventDetail,
  BackendChatMessageData,
  BackendOutputDiff,
  BackendReportData,
  BackendRbacResult,
  BackendRbacPolicyData,
  BackendRiskComponents,
  BackendRuleListData,
  BackendRuleHit,
  BackendSecurityEvent,
  BackendSecurityEventListData,
  BackendSecurityRule,
  BackendTestCaseListData,
  ChatMessageResponse,
  DashboardOverview,
  DashboardRealtimeSnapshot,
  InjectionRule,
  InputRiskEvaluateRequest,
  InputRiskEvaluateResponse,
  MaskTemplate,
  OperationLog,
  Paginated,
  ReportJobResponse,
  ReportJobStatusResponse,
  RegisteredTool,
  RiskMatrixSummary,
  SecurityEventListItem,
  SecurityRealtimeEvent,
  SecurityEventQuery,
  SecurityTestCase,
  SensitiveAsset,
  ToolInvocationRecord,
  ToolPolicy,
  ToolPolicyCreate,
  ToolPolicyUpdate,
  TopologyGraph,
} from '@/types/api';
import { apiUrl } from '@/config/env';

function pickNumber(...values: unknown[]): number | undefined {
  for (const value of values) {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
  }
  return undefined;
}

function pickText(...values: unknown[]): string | undefined {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value;
  }
  return undefined;
}

function normalizeDecision(action?: string, decision?: string): 'block' | 'allow' {
  const value = `${action ?? ''} ${decision ?? ''}`.toLowerCase();
  return value.includes('block') ? 'block' : 'allow';
}

function displayRiskLevel(level?: string): string {
  const value = (level ?? '').toLowerCase();
  if (value === 'high' || value === 'critical') return '高危';
  if (value === 'medium' || value === 'mid') return '中危';
  if (value === 'low' || value === 'normal' || value === 'safe') return '低危';
  return level || '低危';
}

function displayRiskType(type?: string): string {
  const value = (type ?? '').toLowerCase();
  if (value === 'prompt_injection') return '提示注入';
  if (value === 'rule_override') return '规则覆盖';
  if (value === 'privilege_escalation') return '工具越权';
  if (value === 'sensitive_data_exfiltration') return '敏感泄露';
  if (value === 'normal') return '正常请求';
  return type || '未知';
}

function displayDecision(value?: string): string {
  const text = (value ?? '').toLowerCase();
  if (text.includes('block')) return '拦截';
  if (text.includes('allow') || text.includes('pass')) return '放行';
  return value || '未知';
}

function ruleCategory(riskType?: string): InjectionRule['category'] {
  const value = (riskType ?? '').toLowerCase();
  if (value === 'privilege_escalation') return '越权诱导';
  if (value === 'sensitive_data_exfiltration') return '敏感诱导';
  if (value === 'rule_override') return '系统提示泄露';
  return '提示注入';
}

function sensitivityLevelFromResources(resources: string[] = []): ToolPolicy['level'] {
  const joined = resources.join(' ').toLowerCase();
  if (joined.includes('/admin') || joined.includes('db_credentials') || joined.includes('secret')) {
    return 'L4';
  }
  if (joined.includes('token') || joined.includes('key')) return 'L3';
  return 'L2';
}

function getRuleHits(data: BackendChatMessageData | BackendSecurityEvent): BackendRuleHit[] {
  return data.ruleHits ?? data.rule_hits ?? [];
}

function mapRuleHit(hit: BackendRuleHit) {
  const ruleId = pickText(hit.ruleId, hit.rule_id) ?? 'unknown-rule';
  return {
    ruleId,
    template: pickText(hit.name, hit.riskType, hit.risk_type) ?? ruleId,
    weight: pickNumber(hit.score) ?? 0,
  };
}

function getRiskComponents(data: BackendChatMessageData | BackendSecurityEvent): BackendRiskComponents {
  return data.riskComponents ?? data.risk_components ?? {};
}

function getRiskScore(data: BackendChatMessageData | BackendSecurityEvent): number {
  return pickNumber(data.riskScore, data.risk_score_total) ?? 0;
}

function getScoreBreakdown(data: BackendChatMessageData | BackendSecurityEvent) {
  const components = getRiskComponents(data);
  const ruleScore =
    pickNumber(components.ruleScore, components.rule_score) ??
    Math.min(
      getRuleHits(data).reduce((sum, hit) => sum + (pickNumber(hit.score) ?? 0), 0),
      70
    );
  const contextScore = pickNumber(components.contextScore, components.context_score) ?? 0;
  const resourceScore =
    pickNumber(components.resourceSensitivityScore, components.resource_sensitivity_score) ?? 0;
  const semanticScore =
    pickNumber(components.semanticScore, components.semantic_score) ??
    Math.max(0, getRiskScore(data) - ruleScore - contextScore - resourceScore);

  return {
    sRule: Math.min(100, ruleScore),
    sCls: Math.min(100, semanticScore),
    sCtx: Math.min(100, contextScore),
    sRes: Math.min(100, resourceScore),
  };
}

function getRbacResult(data: BackendChatMessageData | BackendSecurityEvent): BackendRbacResult {
  return data.rbacResult ?? data.rbac_result ?? {};
}

function getOutputDiff(data: BackendChatMessageData | BackendSecurityEvent): BackendOutputDiff {
  return data.outputDiff ?? data.output_diff ?? {};
}

function mapBackendChatMessage(
  data: BackendChatMessageData,
  fallbackSessionId: string | undefined
): ChatMessageResponse {
  const outputDiff = getOutputDiff(data);
  const rbac = getRbacResult(data);
  return {
    sessionId: pickText(data.sessionId, data.session_id, fallbackSessionId) ?? `sess-${Date.now()}`,
    assistant: {
      role: 'agent',
      content: pickText(data.reply, outputDiff.after, outputDiff.masked) ?? '',
      isBlock: Boolean(data.blocked || data.decision === 'BLOCKED'),
      isMasked: Boolean(outputDiff.changed),
      riskType: pickText(data.riskType, data.risk_type, data.riskLevel, data.risk_level),
      reason: pickText(rbac.reason, data.auditConclusion, data.audit_conclusion),
      riskScoreR: getRiskScore(data),
      scoreBreakdown: getScoreBreakdown(data),
      eventId: pickText(data.eventId, data.event_id) ?? undefined,
    },
  };
}

function mapBackendEventList(
  data: BackendSecurityEventListData,
  page: number,
  pageSize: number
): Paginated<SecurityEventListItem> {
  const items = data.items ?? [];
  return {
    items: items.map((item) => ({
      id: pickText(item.eventId, item.event_id) ?? '',
      time: pickText(item.timestamp) ?? '',
      type: displayRiskType(pickText(item.riskType, item.risk_type)),
      level: displayRiskLevel(pickText(item.riskLevel, item.risk_level)),
      result: displayDecision(pickText(item.decision, item.action)),
    })),
    total: data.total ?? items.length,
    page: data.page ?? page,
    pageSize: data.pageSize ?? pageSize,
  };
}

function mapBackendAuditDetail(data: BackendSecurityEvent): AuditEventDetail {
  const outputDiff = getOutputDiff(data);
  const rbac = getRbacResult(data);
  const action = normalizeDecision(data.action, data.decision);
  const passed = typeof rbac.allowed === 'boolean' ? rbac.allowed : Boolean(rbac.passed);
  const scoreBreakdown = getScoreBreakdown(data);

  return {
    event_id: pickText(data.event_id, data.eventId) ?? '',
    timestamp: pickText(data.timestamp) ?? '',
    scenario: '对话安全演示',
    risk_level: pickText(data.risk_level, data.riskLevel) ?? 'low',
    action,
    user_input: pickText(data.user_input, data.userInput) ?? '',
    risk_scores: {
      rule_score: scoreBreakdown.sRule,
      semantic_score: scoreBreakdown.sCls,
      context_score: scoreBreakdown.sCtx,
      resource_score: scoreBreakdown.sRes,
    },
    risk_score_total: getRiskScore(data),
    rule_hits: getRuleHits(data).map(mapRuleHit),
    function_call: data.function_call ?? data.functionCall ?? {},
    rbac_result: {
      passed,
      matched_role: pickText(rbac.matched_role, rbac.role) ?? 'demo_user',
      reject_reason: passed ? '' : pickText(rbac.reject_reason, rbac.reason) ?? '',
    },
    audit_conclusion: pickText(data.audit_conclusion, data.auditConclusion) ?? '',
    output_diff: {
      original: pickText(outputDiff.original, outputDiff.before) ?? '',
      masked: pickText(outputDiff.masked, outputDiff.after) ?? '',
    },
  };
}

function mapBackendReport(data: BackendReportData, eventId: string): ReportJobResponse {
  const resolvedEventId = pickText(data.event_id, data.eventId, eventId) ?? eventId;
  return {
    jobId: `report-${resolvedEventId}`,
    status: 'done',
    eventId: resolvedEventId,
    title: data.title,
    generatedAt: pickText(data.generated_at, data.generatedAt),
    summary: data.summary,
    sections: data.sections,
    recommendation: data.recommendation,
  };
}

function mapBackendRule(rule: BackendSecurityRule): InjectionRule {
  const patterns = rule.patterns ?? [];
  const riskType = rule.risk_type ?? '';
  return {
    id: rule.id,
    name: rule.name,
    type: patterns.length > 1 ? 'keyword' : 'regex',
    pattern: patterns.join(' | '),
    category: ruleCategory(riskType),
    weight: Math.min(1, Math.max(0, (rule.score ?? 0) / 100)),
    enabled: true,
    hits7d: 0,
    description: `${displayRiskType(riskType)} · ${rule.severity ?? 'unknown'}`,
  };
}

function mapBackendRbacPolicy(data: BackendRbacPolicyData): ToolPolicy[] {
  const roles = data.roles ?? {};
  const rows: ToolPolicy[] = [];

  Object.entries(roles).forEach(([role, policy]) => {
    const allowedTools = policy.allowed_tools ?? [];
    const deniedTools = policy.denied_tools ?? [];

    allowedTools.forEach((tool, index) => {
      const resources = tool.resources ?? [];
      rows.push({
        id: `${role}-allow-${tool.name ?? index}`,
        name: tool.name ?? 'unknown_tool',
        desc: 'RBAC 白名单工具',
        constraints: resources.length ? `允许资源：${resources.join(', ')}` : '允许资源：未指定',
        level: sensitivityLevelFromResources(resources),
        rbac: [role],
        active: true,
        blockCount: 0,
      });
    });

    deniedTools.forEach((tool, index) => {
      const resources = tool.resources ?? [];
      rows.push({
        id: `${role}-deny-${tool.name ?? index}`,
        name: tool.name ?? 'unknown_tool',
        desc: 'RBAC 拒绝策略工具',
        constraints: resources.length ? `拒绝资源：${resources.join(', ')}` : '拒绝资源：未指定',
        level: sensitivityLevelFromResources(resources),
        rbac: [role],
        active: true,
        blockCount: 0,
      });
    });
  });

  return rows;
}

/** 风险总览 + 趋势序列 */
export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  if (USE_MOCK) return mock.mockGetDashboardOverview();
  return request<DashboardOverview>('/dashboard/overview');
}

/** 事件列表页顶部矩阵摘要（监控节点数、高危区等） */
export async function fetchRiskMatrixSummary(): Promise<RiskMatrixSummary> {
  if (USE_MOCK) return mock.mockGetRiskMatrix();
  return request<RiskMatrixSummary>('/dashboard/risk-matrix');
}

export async function createChatSession(): Promise<{ sessionId: string }> {
  if (USE_MOCK) return mock.mockCreateChatSession();
  return { sessionId: `sess-${Date.now()}` };
}

export async function sendChatMessage(
  sessionId: string | undefined,
  content: string
): Promise<ChatMessageResponse> {
  if (USE_MOCK) return mock.mockSendChatMessage(sessionId, content);
  const data = await request<BackendChatMessageData>('/chat/messages', {
    method: 'POST',
    body: JSON.stringify({ sessionId, content }),
  });
  return mapBackendChatMessage(data, sessionId);
}

export async function listToolPolicies(): Promise<ToolPolicy[]> {
  if (USE_MOCK) return mock.mockListToolPolicies();
  const data = await request<BackendRbacPolicyData>('/security/rbac');
  return mapBackendRbacPolicy(data);
}

export async function createToolPolicy(body: ToolPolicyCreate): Promise<ToolPolicy> {
  if (USE_MOCK) return mock.mockCreateToolPolicy(body);
  void body;
  throw new Error('当前阶段 RBAC 策略为只读模式');
}

export async function updateToolPolicy(id: string, body: ToolPolicyUpdate): Promise<ToolPolicy> {
  if (USE_MOCK) return mock.mockUpdateToolPolicy(id, body);
  void id;
  void body;
  throw new Error('当前阶段 RBAC 策略为只读模式');
}

export async function listSecurityEvents(
  query: SecurityEventQuery
): Promise<Paginated<SecurityEventListItem>> {
  const page = query.page ?? 1;
  const pageSize = query.pageSize ?? 10;
  if (USE_MOCK) return mock.mockListEvents(page, pageSize);
  const q = new URLSearchParams({
    page: String(page),
    pageSize: String(pageSize),
  });
  if (query.type) q.set('type', query.type);
  if (query.level) q.set('level', query.level);
  const data = await request<BackendSecurityEventListData>(`/security/events?${q.toString()}`);
  return mapBackendEventList(data, page, pageSize);
}

export async function getAuditEventDetail(eventId: string): Promise<AuditEventDetail> {
  if (USE_MOCK) return mock.mockGetEventDetail(eventId);
  const data = await request<BackendSecurityEvent>(
    `/security/events/${encodeURIComponent(eventId)}`
  );
  return mapBackendAuditDetail(data);
}

/** 触发异步导出；真实环境可轮询 job 或直接使用 downloadUrl */
export async function requestAuditReport(eventId: string): Promise<ReportJobResponse> {
  if (USE_MOCK) return mock.mockRequestAuditReport(eventId);
  const data = await request<BackendReportData>(`/security/events/${encodeURIComponent(eventId)}/report`, {
    method: 'POST',
    body: '{}',
  });
  return mapBackendReport(data, eventId);
}

export async function listSecurityTestCases(): Promise<SecurityTestCase[]> {
  if (USE_MOCK) return [];
  const data = await request<BackendTestCaseListData>('/security/test-cases');
  return data.items ?? [];
}

/**
 * [阶段二可放开] 拉取后端真实工具注册表
 * 对齐类型：RegisteredTool[]
 * 放开条件：
 * 1) 后端已实现 /tools/registry
 * 2) 响应字段与 RegisteredTool 对齐（含 inputSchema / allowedRoles / level）
 */
export async function listRegisteredTools(): Promise<RegisteredTool[]> {
  if (USE_MOCK) {
    return [
      {
        id: 'tool-mock-read-file',
        name: 'read_system_file',
        description: '读取内部文件系统文档',
        level: 'L3',
        active: true,
        inputSchema: { type: 'object', properties: { path: { type: 'string' } }, required: ['path'] },
        allowedRoles: ['admin', 'manager'],
        constraints: { pathPrefix: ['/public', '/docs'] },
      },
      {
        id: 'tool-mock-db-query',
        name: 'query_database_record',
        description: '业务数据库查询',
        level: 'L4',
        active: true,
        inputSchema: { type: 'object', properties: { table: { type: 'string' } }, required: ['table'] },
        allowedRoles: ['admin', 'dba'],
        constraints: { deniedFields: ['password', 'token', 'secret'] },
      },
      {
        id: 'tool-mock-faq',
        name: 'search_campus_faq',
        description: '校园/公开知识库检索',
        level: 'L1',
        active: true,
        inputSchema: { type: 'object', properties: { q: { type: 'string' }, top_k: { type: 'number' } } },
        allowedRoles: ['student', 'guest', 'manager', 'admin'],
        constraints: { topKMax: 10 },
      },
      {
        id: 'tool-mock-external',
        name: 'invoke_external_api',
        description: '外联受控 HTTP 接口',
        level: 'L2',
        active: true,
        inputSchema: { type: 'object', properties: { url: { type: 'string' } }, required: ['url'] },
        allowedRoles: ['admin', 'manager', 'analyst'],
        constraints: { hostAllowlist: ['*.partner.internal'] },
      },
      {
        id: 'tool-mock-export',
        name: 'export_user_batch',
        description: '批量导出用户数据',
        level: 'L4',
        active: true,
        inputSchema: { type: 'object', properties: { limit: { type: 'number' } } },
        allowedRoles: ['admin', 'dpo'],
        constraints: { limitMax: 1000, requireApproval: true },
      },
    ];
  }
  return request<RegisteredTool[]>('/tools/registry');
}

/**
 * [阶段二可放开] 输入阶段风险评估（规则 + 分类 + 资源敏感度）
 * 对齐类型：
 * - 请求：InputRiskEvaluateRequest
 * - 响应：InputRiskEvaluateResponse
 * 放开条件：
 * 1) 后端策略引擎可在 LLM 调用前返回风险分与决策
 * 2) 响应包含 scoreBreakdown 与 decision
 */
export async function evaluateInputRisk(
  body: InputRiskEvaluateRequest
): Promise<InputRiskEvaluateResponse> {
  if (USE_MOCK) {
    const hasHighRiskHint = /忽略|越权|读取|\/admin|系统提示/i.test(body.content);
    if (hasHighRiskHint) {
      return {
        riskScoreR: 88,
        level: 'high',
        decision: 'block',
        hitRules: [{ ruleId: 'rule-injection-001', template: '忽略系统规则', weight: 0.95 }],
        reason: '命中高危提示注入与越权诱导特征',
        scoreBreakdown: { sRule: 90, sCls: 85, sCtx: 72, sRes: 88 },
      };
    }
    return {
      riskScoreR: 18,
      level: 'low',
      decision: 'allow',
      hitRules: [],
      reason: '未发现高风险输入特征',
      scoreBreakdown: { sRule: 12, sCls: 20, sCtx: 15, sRes: 22 },
    };
  }
  return request<InputRiskEvaluateResponse>('/security/input-evaluate', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * [阶段三可放开] 事件证据链追加（用于“决策过程实时反映在报告”）
 * 对齐类型：
 * - 请求：AppendAuditTraceRequest
 * - 响应：AppendAuditTraceResponse
 * 放开条件：
 * 1) 后端支持 trace 增量写入与版本控制
 * 2) AuditDetail 页面按 traceId / latestVersion 拉取最新步骤
 */
export async function appendAuditTrace(
  body: AppendAuditTraceRequest
): Promise<AppendAuditTraceResponse> {
  if (USE_MOCK) {
    return {
      eventId: body.eventId,
      traceId: body.traceId || `trace-${body.eventId}`,
      accepted: true,
      latestVersion: Date.now(),
    };
  }
  return request<AppendAuditTraceResponse>(
    `/security/events/${encodeURIComponent(body.eventId)}/trace`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    }
  );
}

/**
 * [阶段三可放开] 报告任务轮询状态（配合 requestAuditReport）
 * 对齐类型：ReportJobStatusResponse
 * 放开条件：
 * 1) 后端返回 pending/running/done/failed
 * 2) done 状态返回 downloadUrl
 */
export async function getAuditReportJobStatus(jobId: string): Promise<ReportJobStatusResponse> {
  if (USE_MOCK) {
    return {
      jobId,
      status: 'done',
      progress: 100,
      message: 'Mock 报告生成完成',
      downloadUrl: `/api/v1/security/reports/${encodeURIComponent(jobId)}.pdf`,
    };
  }
  return request<ReportJobStatusResponse>(`/security/reports/jobs/${encodeURIComponent(jobId)}`);
}

/**
 * [阶段三可放开] 获取总览页实时快照（未上 SSE 时可短轮询）
 * 对齐类型：DashboardRealtimeSnapshot
 * 放开条件：
 * 1) 后端已实现 dashboard + latestEvents 聚合接口
 * 2) 前端多页面统一读同一 store / snapshot
 */
export async function fetchDashboardRealtimeSnapshot(): Promise<DashboardRealtimeSnapshot> {
  if (USE_MOCK) {
    const overview = await mock.mockGetDashboardOverview();
    const events = await mock.mockListEvents(1, 12);
    return {
      overview,
      latestEvents: events.items,
      serverTime: new Date().toISOString(),
    };
  }
  return request<DashboardRealtimeSnapshot>('/dashboard/realtime-snapshot');
}

/**
 * [阶段四再放开] SSE 推送（全页面统一实时更新）
 *
 * 对齐类型：SecurityRealtimeEvent（见 src/types/api.ts）
 * 推荐后端事件类型：
 * - event.created / event.updated
 * - dashboard.updated
 * - report.updated
 * - audit.trace.appended
 *
 * 放开条件：
 * 1) 后端提供 GET /security/stream（SSE）并返回 text/event-stream
 * 2) 鉴权方式明确（Cookie 或 Bearer）
 *
 * // 使用示例：
 * // const close = subscribeSecurityStream((evt) => { ... });
 * // onBeforeUnmount(() => close());
 */
export function subscribeSecurityStream(
  onMessage: (evt: SecurityRealtimeEvent) => void,
  onError?: (error: Event) => void
): () => void {
  // mock 模式下模拟“推送”事件，便于前端先打通实时联动逻辑。
  if (USE_MOCK) {
    const timer = window.setInterval(() => {
      onMessage({
        type: 'dashboard.updated',
        timestamp: new Date().toISOString(),
      });
    }, 6000);
    return () => window.clearInterval(timer);
  }

  const es = new EventSource(apiUrl('/security/stream'));
  es.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data) as SecurityRealtimeEvent);
    } catch {
      // ignore malformed payload
    }
  };
  es.onerror = (error) => {
    onError?.(error);
    es.close();
  };
  return () => es.close();
}

/* ============================================================
 * 资产拓扑、调用流水、规则、脱敏、应用、资产、告警、操作日志
 * （Mock 优先，真实接口按注释开放）
 * ============================================================ */

export async function fetchTopologyGraph(): Promise<TopologyGraph> {
  if (USE_MOCK) return mock.mockGetTopologyGraph();
  return request<TopologyGraph>('/dashboard/topology');
}

export async function listToolInvocations(
  page = 1,
  pageSize = 10
): Promise<Paginated<ToolInvocationRecord>> {
  if (USE_MOCK) return mock.mockListToolInvocations(page, pageSize);
  return request<Paginated<ToolInvocationRecord>>(
    `/security/tool-invocations?page=${page}&pageSize=${pageSize}`
  );
}

export async function getToolInvocation(id: string): Promise<ToolInvocationRecord | null> {
  if (USE_MOCK) return mock.mockGetToolInvocation(id);
  return request<ToolInvocationRecord>(`/security/tool-invocations/${encodeURIComponent(id)}`);
}

export async function listInjectionRules(): Promise<InjectionRule[]> {
  if (USE_MOCK) return mock.mockListInjectionRules();
  const data = await request<BackendRuleListData>('/security/rules');
  return (data.items ?? []).map(mapBackendRule);
}

export async function saveInjectionRule(row: InjectionRule): Promise<InjectionRule> {
  if (USE_MOCK) return mock.mockSaveInjectionRule(row);
  void row;
  throw new Error('当前阶段规则库为只读模式');
}

export async function deleteInjectionRule(id: string): Promise<void> {
  if (USE_MOCK) return mock.mockDeleteInjectionRule(id);
  void id;
  throw new Error('当前阶段规则库为只读模式');
}

export async function listMaskTemplates(): Promise<MaskTemplate[]> {
  if (USE_MOCK) return mock.mockListMaskTemplates();
  return request<MaskTemplate[]>('/policy/mask-templates');
}

export async function saveMaskTemplate(row: MaskTemplate): Promise<MaskTemplate> {
  if (USE_MOCK) return mock.mockSaveMaskTemplate(row);
  return request<MaskTemplate>('/policy/mask-templates', {
    method: 'POST',
    body: JSON.stringify(row),
  });
}

export async function deleteMaskTemplate(id: string): Promise<void> {
  if (USE_MOCK) return mock.mockDeleteMaskTemplate(id);
  await request<void>(`/policy/mask-templates/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export async function listAgentApps(): Promise<AgentApp[]> {
  if (USE_MOCK) return mock.mockListAgentApps();
  return request<AgentApp[]>('/assets/agent-apps');
}

export async function saveAgentApp(row: AgentApp): Promise<AgentApp> {
  if (USE_MOCK) return mock.mockSaveAgentApp(row);
  return request<AgentApp>('/assets/agent-apps', { method: 'POST', body: JSON.stringify(row) });
}

export async function listSensitiveAssets(): Promise<SensitiveAsset[]> {
  if (USE_MOCK) return mock.mockListSensitiveAssets();
  return request<SensitiveAsset[]>('/assets/sensitive');
}

export async function saveSensitiveAsset(row: SensitiveAsset): Promise<SensitiveAsset> {
  if (USE_MOCK) return mock.mockSaveSensitiveAsset(row);
  return request<SensitiveAsset>('/assets/sensitive', { method: 'POST', body: JSON.stringify(row) });
}

export async function listAlertRoutes(): Promise<AlertRoute[]> {
  if (USE_MOCK) return mock.mockListAlertRoutes();
  return request<AlertRoute[]>('/settings/alert-routes');
}

export async function saveAlertRoute(row: AlertRoute): Promise<AlertRoute> {
  if (USE_MOCK) return mock.mockSaveAlertRoute(row);
  return request<AlertRoute>('/settings/alert-routes', { method: 'POST', body: JSON.stringify(row) });
}

export async function listOperationLogs(
  page = 1,
  pageSize = 20
): Promise<Paginated<OperationLog>> {
  if (USE_MOCK) return mock.mockListOperationLogs(page, pageSize);
  return request<Paginated<OperationLog>>(
    `/settings/operation-logs?page=${page}&pageSize=${pageSize}`
  );
}
