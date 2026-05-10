/** 与后端约定的通用包装（可按团队规范增删字段） */
export interface ApiEnvelope<T> {
  code: number;
  message?: string;
  data: T;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface DashboardStats {
  totalEvents: number;
  highRiskEvents: number;
  toolAuditCount: number;
  leakBlockCount: number;
  /** 风险事件总数周同比，百分比数字，如 12.5 */
  weekChangePercent?: number;
}

export interface DashboardTrend {
  dates: string[];
  injection: number[];
  toolAbuse: number[];
  dataLeak: number[];
}

export interface RiskTypeDistributionItem {
  type: string;
  label: string;
  count: number;
}

export interface DashboardOverview {
  stats: DashboardStats;
  trend: DashboardTrend;
  riskTypeDistribution?: RiskTypeDistributionItem[];
  risk_type_distribution?: RiskTypeDistributionItem[];
}

export interface RiskMatrixSummary {
  monitoredNodes: number;
  highRiskZones: number;
}

/** 对话：后端返回的助手消息（与前端展示对齐） */
export interface ChatAssistantPayload {
  role: 'agent';
  content: string;
  isBlock: boolean;
  isMasked: boolean;
  riskType?: string;
  reason?: string;
  /** 综合风险 R，0–100 */
  riskScoreR?: number;
  scoreBreakdown?: {
    sRule: number;
    sCls: number;
    sCtx: number;
    sRes: number;
  };
  /** 若产生安全事件，用于跳转证据链 */
  eventId?: string;
}

export interface ChatMessageRequest {
  sessionId?: string;
  content: string;
}

export interface ChatMessageResponse {
  sessionId: string;
  assistant: ChatAssistantPayload;
}

export interface BackendRuleHit {
  ruleId?: string;
  rule_id?: string;
  name?: string;
  riskType?: string;
  risk_type?: string;
  severity?: string;
  score?: number;
  matchedPatterns?: string[];
  matched_patterns?: string[];
}

export interface BackendRiskComponents {
  ruleScore?: number;
  rule_score?: number;
  semanticScore?: number;
  semantic_score?: number;
  contextScore?: number;
  context_score?: number;
  resourceSensitivityScore?: number;
  resource_sensitivity_score?: number;
}

export interface BackendRbacResult {
  allowed?: boolean;
  role?: string;
  reason?: string;
  passed?: boolean;
  matched_role?: string;
  reject_reason?: string;
  matchedPolicy?: unknown;
  matched_policy?: unknown;
}

export interface BackendOutputDiff {
  before?: string;
  after?: string;
  original?: string;
  masked?: string;
  changed?: boolean;
  redactions?: unknown[];
}

export interface BackendChatMessageData {
  sessionId?: string;
  session_id?: string;
  reply?: string;
  blocked?: boolean;
  decision?: string;
  action?: string;
  riskLevel?: string;
  risk_level?: string;
  riskType?: string;
  risk_type?: string;
  riskScore?: number;
  risk_score_total?: number;
  riskComponents?: BackendRiskComponents;
  risk_components?: BackendRiskComponents;
  ruleHits?: BackendRuleHit[];
  rule_hits?: BackendRuleHit[];
  functionCall?: Record<string, unknown> | null;
  function_call?: Record<string, unknown> | null;
  rbacResult?: BackendRbacResult;
  rbac_result?: BackendRbacResult;
  outputDiff?: BackendOutputDiff;
  output_diff?: BackendOutputDiff;
  eventId?: string | null;
  event_id?: string | null;
  auditConclusion?: string;
  audit_conclusion?: string;
}

export interface BackendSecurityEvent extends BackendChatMessageData {
  eventId?: string;
  event_id?: string;
  timestamp?: string;
  action?: string;
  userInput?: string;
  user_input?: string;
}

export interface BackendSecurityEventListData {
  items?: BackendSecurityEvent[];
  total?: number;
  page?: number;
  pageSize?: number;
}

export interface BackendReportData {
  eventId?: string;
  event_id?: string;
  generatedAt?: string;
  generated_at?: string;
  title?: string;
  summary?: string | Record<string, unknown>;
  decision?: string;
  riskLevel?: string;
  risk_level?: string;
  riskScore?: number;
  risk_score_total?: number;
  sections?: ReportSection[];
  recommendation?: string;
}

export interface BackendRuleListData {
  items?: BackendSecurityRule[];
  total?: number;
}

export interface BackendSecurityRule {
  id: string;
  name: string;
  risk_type?: string;
  severity?: string;
  score?: number;
  patterns?: string[];
  hits7d?: number;
  hits_7d?: number;
}

export interface BackendRbacPolicyData {
  roles?: Record<string, BackendRbacRolePolicy>;
  summary?: {
    roleCount?: number;
    allowedPolicyCount?: number;
    deniedPolicyCount?: number;
  };
}

export interface BackendRbacRolePolicy {
  allowed_tools?: BackendRbacToolPolicy[];
  denied_tools?: BackendRbacToolPolicy[];
}

export interface BackendRbacToolPolicy {
  name?: string;
  resources?: string[];
}

export interface BackendTestCaseListData {
  items?: SecurityTestCase[];
  total?: number;
}

export interface SecurityTestCase {
  id: string;
  title: string;
  category: string;
  content: string;
  expectedDecision: string;
  expectedRiskLevel: string;
  description?: string;
}

export interface DesensitizeRedaction {
  type: string;
  value: string;
}

export interface DesensitizePreviewResponse {
  original: string;
  masked: string;
  before?: string;
  after?: string;
  changed: boolean;
  redactions: DesensitizeRedaction[];
}

export type SensitivityLevel = 'L1' | 'L2' | 'L3' | 'L4';

export interface ToolPolicy {
  id: string;
  name: string;
  desc: string;
  constraints: string;
  level: SensitivityLevel;
  rbac: string[];
  active: boolean;
  blockCount: number;
}

export interface ToolPolicyCreate {
  name: string;
  desc: string;
  constraints: string;
  level: SensitivityLevel;
  rbac: string[];
}

export interface ToolPolicyUpdate extends Partial<ToolPolicyCreate> {
  active?: boolean;
}

export interface SecurityEventListItem {
  id: string;
  time: string;
  type: string;
  level: string;
  result: string;
}

export interface SecurityEventQuery {
  page?: number;
  pageSize?: number;
  type?: string;
  level?: string;
}

export interface RuleHit {
  ruleId: string;
  template: string;
  weight: number;
}

export interface AuditEventDetail {
  event_id: string;
  timestamp: string;
  scenario: string;
  risk_level: string;
  action: string;
  user_input: string;
  risk_scores: {
    rule_score: number;
    semantic_score: number;
    context_score: number;
    resource_score: number;
  };
  risk_score_total?: number;
  rule_hits?: RuleHit[];
  function_call: Record<string, unknown>;
  rbac_result: {
    passed: boolean;
    matched_role: string;
    reject_reason: string;
  };
  audit_conclusion: string;
  output_diff?: {
    original: string;
    masked: string;
  };
}

export interface ReportJobResponse {
  jobId: string;
  status: 'pending' | 'done' | 'failed';
  downloadUrl?: string;
  eventId?: string;
  title?: string;
  generatedAt?: string;
  summary?: string | Record<string, unknown>;
  sections?: ReportSection[];
  recommendation?: string;
}

export interface ReportSection {
  key: string;
  title: string;
  items?: Array<{
    label: string;
    value: unknown;
  }>;
}

/**
 * ====== 后端联调闭环（阶段化）契约 ======
 * 说明：
 * - 下列类型用于“输入检测 -> 决策 -> 执行审计 -> 报告/看板实时更新”的完整链路。
 * - 当前前端可继续用 mock，待后端对应接口上线后，按 services.ts 中注释分阶段放开。
 */

/** 工具注册中心中的真实工具定义（用于“输入时结合真实注册工具判断风险”） */
export interface RegisteredTool {
  id: string;
  name: string;
  description: string;
  level: SensitivityLevel;
  active: boolean;
  /** JSON Schema 或简化约束描述 */
  inputSchema: Record<string, unknown>;
  allowedRoles: string[];
  /** 参数范围/路径白名单等约束 */
  constraints?: Record<string, unknown>;
}

/** 输入阶段风险评估请求（可在调用大模型前执行） */
export interface InputRiskEvaluateRequest {
  sessionId: string;
  content: string;
  role?: string;
  /** 当前会话可用工具（建议由后端按 RBAC 回填） */
  candidateTools?: Array<Pick<RegisteredTool, 'name' | 'level' | 'active'>>;
}

/** 输入阶段风险评估结果 */
export interface InputRiskEvaluateResponse {
  riskScoreR: number;
  level: 'low' | 'medium' | 'high' | 'critical';
  decision: 'allow' | 'confirm' | 'block';
  hitRules: RuleHit[];
  reason?: string;
  scoreBreakdown: {
    sRule: number;
    sCls: number;
    sCtx: number;
    sRes: number;
  };
}

/** 工具调用审计单步记录（用于报告中的“工程实时反映”） */
export interface AuditTraceStep {
  step: string;
  at: string;
  status: 'ok' | 'warn' | 'blocked' | 'error';
  detail: string;
  metadata?: Record<string, unknown>;
}

/** 上报到后端的审计追踪增量 */
export interface AppendAuditTraceRequest {
  eventId: string;
  sessionId: string;
  traceId?: string;
  step: AuditTraceStep;
}

/** 后端响应的追踪写入结果 */
export interface AppendAuditTraceResponse {
  eventId: string;
  traceId: string;
  accepted: boolean;
  latestVersion: number;
}

/** 报告任务状态（异步导出轮询） */
export interface ReportJobStatusResponse {
  jobId: string;
  status: 'pending' | 'running' | 'done' | 'failed';
  progress?: number;
  message?: string;
  downloadUrl?: string;
}

/** 总览页实时快照（统一更新多页面） */
export interface DashboardRealtimeSnapshot {
  overview: DashboardOverview;
  latestEvents: SecurityEventListItem[];
  serverTime: string;
}

/** SSE/WS 推送消息体（用于统一刷新各页面） */
export interface SecurityRealtimeEvent {
  type:
    | 'event.created'
    | 'event.updated'
    | 'dashboard.updated'
    | 'report.updated'
    | 'audit.trace.appended';
  timestamp: string;
  eventId?: string;
  jobId?: string;
  payload?: Record<string, unknown>;
}

/** ========= 资产拓扑（Dashboard 右侧关系图） ========= */
export interface TopologyNode {
  id: string;
  name: string;
  category: 'agent' | 'tool' | 'resource';
  /** 0–100，表示当前承压热度 */
  heat: number;
}

export interface TopologyEdge {
  source: string;
  target: string;
  /** 单位时间内的调用/请求次数 */
  weight: number;
  /** 阻断次数 */
  blocked?: number;
}

export interface TopologyGraph {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

/** ========= 工具调用监控台 ========= */
export interface ToolInvocationRecord {
  id: string;
  time: string;
  timestamp?: string;
  agent: string;
  toolName: string;
  tool_name?: string;
  /** 简化的参数摘要 */
  argsBrief: string;
  args_brief?: string;
  arguments: Record<string, unknown>;
  callerRole: string;
  caller_role?: string;
  requiredLevel: SensitivityLevel;
  required_level?: SensitivityLevel;
  passed: boolean;
  /** 是否越权 */
  rbacBreach: boolean;
  rbac_breach?: boolean;
  /** 关联事件 ID（若被阻断） */
  eventId?: string;
  event_id?: string;
  decision?: string;
  riskScore?: number;
  risk_score?: number;
  riskLevel?: string;
  risk_level?: string;
  rbacResult?: BackendRbacResult;
  rbac_result?: BackendRbacResult;
  outputDiff?: BackendOutputDiff;
  output_diff?: BackendOutputDiff;
  auditConclusion?: string;
  audit_conclusion?: string;
  status?: string;
  /** 调用链上下文（用于调用链图谱） */
  contextChain?: Array<{ turn: number; speaker: 'user' | 'agent'; text: string }>;
  context_chain?: Array<{ turn: number; speaker: 'user' | 'agent'; text: string }>;
}

/** ========= 注入检测规则库 ========= */
export type RuleType = 'regex' | 'keyword' | 'semantic';

export interface InjectionRule {
  id: string;
  name: string;
  type: RuleType;
  /** 命中模板（正则或关键词，semantic 留空） */
  pattern: string;
  /** 风险类别标签：注入 / 越权诱导 / 系统提示泄露 / 敏感泄露 */
  category: '提示注入' | '越权诱导' | '系统提示泄露' | '敏感诱导';
  /** 风险权重 0–1 */
  weight: number;
  enabled: boolean;
  hits7d: number;
  description?: string;
}

/** ========= 数据去标识化模板 ========= */
export type MaskStrategy = 'mask' | 'truncate' | 'hash' | 'reject';

export interface MaskTemplate {
  id: string;
  name: string;
  pattern: string;
  /** 描述识别的字段类型，如「手机号」「邮箱」 */
  category: string;
  strategy: MaskStrategy;
  /** 替换格式，如 `${prefix}****${suffix}` */
  replacement?: string;
  enabled: boolean;
  hits7d: number;
}

/** ========= 接入应用 ========= */
export interface AgentApp {
  id: string;
  name: string;
  scenario: string;
  apiKey: string;
  rps: number;
  status: 'online' | 'offline' | 'paused';
  bindRoles: string[];
  lastHeartbeat: string;
}

/** ========= 敏感资源资产 ========= */
export interface SensitiveAsset {
  id: string;
  name: string;
  type: 'api' | 'directory' | 'db_table' | 'file_pattern';
  identifier: string;
  level: SensitivityLevel;
  owner: string;
  description?: string;
}

/** ========= 告警路由 ========= */
export type AlertChannel = 'email' | 'webhook' | 'sms' | 'feishu' | 'dingtalk';

export interface AlertRoute {
  id: string;
  name: string;
  channel: AlertChannel;
  target: string;
  /** 触发条件：风险等级或类型 */
  triggerLevels: Array<'low' | 'mid' | 'high'>;
  enabled: boolean;
  lastTriggeredAt?: string;
}

/** ========= 平台操作日志 ========= */
export interface OperationLog {
  id: string;
  time: string;
  actor: string;
  action: string;
  target: string;
  ip?: string;
  outcome: 'success' | 'failure';
}
