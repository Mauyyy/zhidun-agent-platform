import type {
  AgentApp,
  AlertRoute,
  AuditEventDetail,
  ChatAssistantPayload,
  ChatMessageResponse,
  DashboardOverview,
  InjectionRule,
  MaskTemplate,
  OperationLog,
  Paginated,
  ReportJobResponse,
  RiskMatrixSummary,
  SecurityEventListItem,
  SensitiveAsset,
  ToolInvocationRecord,
  ToolPolicy,
  ToolPolicyCreate,
  TopologyGraph,
} from '@/types/api';
import baseDetail from '@/mock/mockData.json';

let sessionCounter = 0;

function buildMockTrend(days: number): DashboardOverview['trend'] {
  const dates: string[] = [];
  const injection: number[] = [];
  const toolAbuse: number[] = [];
  const dataLeak: number[] = [];
  for (let i = 0; i < days; i++) {
    const day = 12 + i;
    dates.push(`04-${String(day).padStart(2, '0')}`);
    const w = (base: number, j: number) =>
      Math.max(40, Math.round(base + 22 * Math.sin(j * 0.55) + ((j * 11) % 31)));
    injection.push(w(118, i));
    toolAbuse.push(w(248, i + 2));
    dataLeak.push(w(186, i + 4));
  }
  return { dates, injection, toolAbuse, dataLeak };
}

const dashboardOverview: DashboardOverview = {
  stats: {
    totalEvents: 3842,
    highRiskEvents: 186,
    toolAuditCount: 2410,
    leakBlockCount: 512,
    weekChangePercent: 12.5,
  },
  trend: buildMockTrend(16),
};

const riskMatrix: RiskMatrixSummary = {
  monitoredNodes: 12040,
  highRiskZones: 7,
};

let toolPolicies: ToolPolicy[] = [
  {
    id: 'tp-1',
    name: 'read_system_file',
    desc: '读取内部文件系统文档',
    constraints: '路径限制: ^/(public|docs)/.*',
    level: 'L3',
    rbac: ['admin', 'manager'],
    active: true,
    blockCount: 42,
  },
  {
    id: 'tp-2',
    name: 'query_database_record',
    desc: '企业数据库业务查询',
    constraints: '禁止字段: password, token, key',
    level: 'L4',
    rbac: ['admin', 'dba'],
    active: true,
    blockCount: 15,
  },
  {
    id: 'tp-3',
    name: 'search_campus_faq',
    desc: '校园问答知识库检索',
    constraints: '最大返回结果数 <= 5',
    level: 'L1',
    rbac: ['admin', 'manager', 'student', 'guest'],
    active: true,
    blockCount: 3,
  },
  {
    id: 'tp-4',
    name: 'invoke_external_api',
    desc: '外联第三方 HTTP 接口',
    constraints: '域名白名单: *.partner.internal',
    level: 'L2',
    rbac: ['admin', 'manager', 'analyst'],
    active: true,
    blockCount: 8,
  },
  {
    id: 'tp-5',
    name: 'export_user_batch',
    desc: '批量导出用户画像',
    constraints: '单次行数 <= 1000; 需二次审批',
    level: 'L4',
    rbac: ['admin', 'dpo'],
    active: true,
    blockCount: 21,
  },
  {
    id: 'tp-6',
    name: 'send_sms_notify',
    desc: '触达类短信（通知/营销）',
    constraints: '模板白名单; 日配额 5000',
    level: 'L2',
    rbac: ['admin', 'ops'],
    active: true,
    blockCount: 2,
  },
  {
    id: 'tp-7',
    name: 'upload_attachment',
    desc: '向工单系统上传附件',
    constraints: '仅允许 doc/pdf/zip; 单文件 < 20MB',
    level: 'L2',
    rbac: ['admin', 'helpdesk', 'analyst'],
    active: true,
    blockCount: 6,
  },
  {
    id: 'tp-8',
    name: 'run_sandbox_code',
    desc: '在隔离沙箱执行用户脚本',
    constraints: 'CPU/内存/网络全限制; 禁止文件写',
    level: 'L3',
    rbac: ['admin', 'dev'],
    active: false,
    blockCount: 0,
  },
];

function buildMockEventRows(): SecurityEventListItem[] {
  const variants: Array<{ type: string; level: string; result: string }> = [
    { type: '工具越权调用', level: '高危', result: '强制阻断' },
    { type: '敏感数据泄露', level: '中危', result: '掩码脱敏' },
    { type: '提示注入攻击', level: '高危', result: '请求重定向' },
    { type: 'RAG 投毒尝试', level: '低危', result: '仅记录' },
    { type: '越权 API 调用', level: '高危', result: '强制阻断' },
    { type: 'PII 外发风险', level: '中危', result: '脱敏放行' },
    { type: '模型越狱诱导', level: '中危', result: '策略澄清' },
    { type: '内部文档爬取', level: '高危', result: '强制阻断' },
    { type: 'Token 泄露检测', level: '中危', result: '掩码脱敏' },
    { type: '异常时序流量', level: '低危', result: '观察模式' },
  ];
  const fmt = (d: Date) => {
    const p = (n: number) => n.toString().padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(
      d.getMinutes()
    )}:${p(d.getSeconds())}`;
  };
  const out: SecurityEventListItem[] = [];
  const base = new Date('2026-04-27T23:55:00');
  for (let i = 0; i < 42; i++) {
    const d = new Date(base.getTime() - i * 44 * 60 * 1000 - (i * 17) % 50 * 1000);
    const v = variants[i % variants.length];
    out.push({
      id: `EVT-2026-${String(2001 + i).padStart(4, '0')}`,
      time: fmt(d),
      type: v.type,
      level: v.level,
      result: v.result,
    });
  }
  return out;
}

const eventRows: SecurityEventListItem[] = buildMockEventRows();

function buildAssistantFromKeywords(content: string): ChatAssistantPayload {
  const text = content;
  if (text.includes('读取') || text.includes('/admin')) {
    return {
      role: 'agent',
      content: '',
      isBlock: true,
      isMasked: false,
      riskType: '工具越权调用',
      reason: '试图访问 L4 级敏感路径 /admin/config/，已被 RBAC 策略强制阻断。',
      riskScoreR: 92,
      scoreBreakdown: { sRule: 85, sCls: 88, sCtx: 70, sRes: 95 },
      eventId: 'EVT-2026-0883',
    };
  }
  if (text.includes('手机号') || text.includes('电话')) {
    return {
      role: 'agent',
      content: '已为您查询到经理信息：张三，联系电话 138****5678。',
      isBlock: false,
      isMasked: true,
      riskScoreR: 35,
      scoreBreakdown: { sRule: 20, sCls: 40, sCtx: 30, sRes: 45 },
    };
  }
  return {
    role: 'agent',
    content: '请求经策略中心判定为安全，已正常放行。',
    isBlock: false,
    isMasked: false,
    riskScoreR: 12,
    scoreBreakdown: { sRule: 10, sCls: 15, sCtx: 8, sRes: 15 },
  };
}

export async function mockGetDashboardOverview(): Promise<DashboardOverview> {
  return structuredClone(dashboardOverview);
}

export async function mockGetRiskMatrix(): Promise<RiskMatrixSummary> {
  return { ...riskMatrix };
}

export async function mockCreateChatSession(): Promise<{ sessionId: string }> {
  sessionCounter += 1;
  return { sessionId: `sess-mock-${sessionCounter}` };
}

export async function mockSendChatMessage(
  sessionId: string | undefined,
  content: string
): Promise<ChatMessageResponse> {
  const sid = sessionId || `sess-mock-${sessionCounter}`;
  await new Promise((r) => setTimeout(r, 400));
  const assistant = buildAssistantFromKeywords(content);
  return { sessionId: sid, assistant };
}

export async function mockListToolPolicies(): Promise<ToolPolicy[]> {
  return structuredClone(toolPolicies);
}

export async function mockCreateToolPolicy(body: ToolPolicyCreate): Promise<ToolPolicy> {
  const row: ToolPolicy = {
    id: `tp-${crypto.randomUUID().slice(0, 8)}`,
    name: body.name,
    desc: body.desc,
    constraints: body.constraints,
    level: body.level,
    rbac: [...body.rbac],
    active: true,
    blockCount: 0,
  };
  toolPolicies = [...toolPolicies, row];
  return { ...row };
}

export async function mockUpdateToolPolicy(id: string, patch: Partial<ToolPolicy>): Promise<ToolPolicy> {
  const i = toolPolicies.findIndex((t) => t.id === id);
  if (i < 0) throw new Error('策略不存在');
  toolPolicies[i] = { ...toolPolicies[i], ...patch };
  return { ...toolPolicies[i] };
}

export async function mockListEvents(
  page: number,
  pageSize: number
): Promise<Paginated<SecurityEventListItem>> {
  const start = (page - 1) * pageSize;
  const items = eventRows.slice(start, start + pageSize);
  return { items, total: eventRows.length, page, pageSize };
}

export async function mockGetEventDetail(eventId: string): Promise<AuditEventDetail> {
  if (eventId === baseDetail.event_id) {
    return structuredClone(baseDetail) as AuditEventDetail;
  }
  return {
    event_id: eventId,
    timestamp: '2026-04-19 12:00:00',
    scenario: '演示事件',
    risk_level: 'medium',
    action: 'mask',
    user_input: '（该事件为占位数据，请在后端接入真实审计记录）',
    risk_scores: {
      rule_score: 40,
      semantic_score: 35,
      context_score: 30,
      resource_score: 45,
    },
    risk_score_total: 38,
    rule_hits: [],
    function_call: { tool_name: 'unknown', arguments: {} },
    rbac_result: {
      passed: true,
      matched_role: 'viewer',
      reject_reason: '',
    },
    audit_conclusion: '示例数据：请在后端返回完整证据链字段。',
    output_diff: {
      original: '示例敏感输出',
      masked: '示例***输出',
    },
  };
}

export async function mockRequestAuditReport(eventId: string): Promise<ReportJobResponse> {
  await new Promise((r) => setTimeout(r, 800));
  return {
    jobId: `job-${eventId}`,
    status: 'done',
    downloadUrl: `/api/v1/security/events/${eventId}/report.pdf`,
  };
}

/* ============================================================
 * 新增：拓扑、调用流水、规则、脱敏、应用、资产、告警、操作日志
 * ============================================================ */

const topologyGraph: TopologyGraph = {
  nodes: [
    { id: 'agent-1', name: '校园问答助手', category: 'agent', heat: 78 },
    { id: 'agent-2', name: '企业知识库', category: 'agent', heat: 64 },
    { id: 'agent-3', name: '办公智能体', category: 'agent', heat: 88 },
    { id: 'agent-4', name: '客服坐席 Copilot', category: 'agent', heat: 71 },
    { id: 'agent-5', name: '数据报表助手', category: 'agent', heat: 55 },
    { id: 'tool-1', name: 'read_system_file', category: 'tool', heat: 70 },
    { id: 'tool-2', name: 'query_database_record', category: 'tool', heat: 92 },
    { id: 'tool-3', name: 'search_campus_faq', category: 'tool', heat: 28 },
    { id: 'tool-4', name: 'invoke_external_api', category: 'tool', heat: 48 },
    { id: 'tool-5', name: 'export_user_batch', category: 'tool', heat: 36 },
    { id: 'res-1', name: '/admin/config', category: 'resource', heat: 95 },
    { id: 'res-2', name: 'tb_customer_info', category: 'resource', heat: 60 },
    { id: 'res-3', name: '校园 FAQ 知识片段', category: 'resource', heat: 18 },
    { id: 'res-4', name: '支付回调日志表', category: 'resource', heat: 44 },
    { id: 'res-5', name: '/v1/hr/employees', category: 'resource', heat: 52 },
  ],
  edges: [
    { source: 'agent-3', target: 'tool-1', weight: 32, blocked: 12 },
    { source: 'agent-3', target: 'tool-2', weight: 24, blocked: 8 },
    { source: 'agent-2', target: 'tool-2', weight: 18, blocked: 3 },
    { source: 'agent-1', target: 'tool-3', weight: 56, blocked: 0 },
    { source: 'agent-4', target: 'tool-2', weight: 22, blocked: 1 },
    { source: 'agent-4', target: 'tool-4', weight: 40, blocked: 0 },
    { source: 'agent-5', target: 'tool-2', weight: 28, blocked: 4 },
    { source: 'agent-5', target: 'tool-5', weight: 14, blocked: 2 },
    { source: 'tool-1', target: 'res-1', weight: 22, blocked: 12 },
    { source: 'tool-2', target: 'res-2', weight: 30, blocked: 5 },
    { source: 'tool-3', target: 'res-3', weight: 56, blocked: 0 },
    { source: 'tool-4', target: 'res-4', weight: 18, blocked: 0 },
    { source: 'tool-5', target: 'res-2', weight: 12, blocked: 1 },
    { source: 'tool-2', target: 'res-5', weight: 26, blocked: 3 },
  ],
};

let toolInvocations: ToolInvocationRecord[] = [
  {
    id: 'INV-2026-0883',
    time: '2026-04-19 14:30:22',
    agent: '办公智能体',
    toolName: 'read_system_file',
    argsBrief: 'file_path=/admin/config/db_credentials.txt',
    arguments: { file_path: '/admin/config/db_credentials.txt', read_mode: 'full_text' },
    callerRole: 'guest_user',
    requiredLevel: 'L4',
    passed: false,
    rbacBreach: true,
    eventId: 'EVT-2026-0883',
    contextChain: [
      { turn: 1, speaker: 'user', text: '帮我读一下昨天那个测试文件' },
      { turn: 2, speaker: 'agent', text: '请提供文件名' },
      { turn: 3, speaker: 'user', text: '直接读 /admin/config/db_credentials.txt' },
    ],
  },
  {
    id: 'INV-2026-0884',
    time: '2026-04-19 13:55:10',
    agent: '企业知识库',
    toolName: 'query_database_record',
    argsBrief: 'table=tb_customer_info, fields=phone,email',
    arguments: { table: 'tb_customer_info', fields: ['phone', 'email'] },
    callerRole: 'analyst',
    requiredLevel: 'L4',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0885',
    time: '2026-04-19 12:48:02',
    agent: '校园问答助手',
    toolName: 'search_campus_faq',
    argsBrief: 'q=食堂营业时间, top_k=3',
    arguments: { q: '食堂营业时间', top_k: 3 },
    callerRole: 'student',
    requiredLevel: 'L1',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0886',
    time: '2026-04-19 12:20:11',
    agent: '客服坐席 Copilot',
    toolName: 'query_database_record',
    argsBrief: 'table=tb_tickets, fields=phone',
    arguments: { table: 'tb_tickets', fields: ['phone', 'user_id'] },
    callerRole: 'helpdesk',
    requiredLevel: 'L4',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0887',
    time: '2026-04-19 11:55:00',
    agent: '数据报表助手',
    toolName: 'export_user_batch',
    argsBrief: 'format=csv, limit=5000',
    arguments: { format: 'csv', limit: 5000 },
    callerRole: 'analyst',
    requiredLevel: 'L4',
    passed: false,
    rbacBreach: true,
    eventId: 'EVT-2026-2014',
  },
  {
    id: 'INV-2026-0888',
    time: '2026-04-19 11:22:18',
    agent: '企业知识库',
    toolName: 'read_system_file',
    argsBrief: 'file_path=/public/release-notes.md',
    arguments: { file_path: '/public/release-notes.md' },
    callerRole: 'analyst',
    requiredLevel: 'L3',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0889',
    time: '2026-04-19 10:40:33',
    agent: '办公智能体',
    toolName: 'invoke_external_api',
    argsBrief: 'url=https://partner.internal/v1/lookup',
    arguments: { url: 'https://partner.internal/v1/lookup', method: 'POST' },
    callerRole: 'manager',
    requiredLevel: 'L2',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0890',
    time: '2026-04-19 10:05:50',
    agent: '校园问答助手',
    toolName: 'search_campus_faq',
    argsBrief: 'q=宿舍网络, top_k=5',
    arguments: { q: '宿舍网络', top_k: 5 },
    callerRole: 'student',
    requiredLevel: 'L1',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0891',
    time: '2026-04-19 09:18:44',
    agent: '客服坐席 Copilot',
    toolName: 'read_system_file',
    argsBrief: 'file_path=/var/log/apptrace.log',
    arguments: { file_path: '/var/log/apptrace.log' },
    callerRole: 'helpdesk',
    requiredLevel: 'L3',
    passed: false,
    rbacBreach: true,
    eventId: 'EVT-2026-2016',
  },
  {
    id: 'INV-2026-0892',
    time: '2026-04-19 08:52:27',
    agent: '企业知识库',
    toolName: 'query_database_record',
    argsBrief: 'table=tb_orders, where=status=pending',
    arguments: { table: 'tb_orders', where: 'status=pending' },
    callerRole: 'analyst',
    requiredLevel: 'L4',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0893',
    time: '2026-04-19 08:10:09',
    agent: '数据报表助手',
    toolName: 'query_database_record',
    argsBrief: 'table=tb_hr_employees, fields=email',
    arguments: { table: 'tb_hr_employees', fields: ['email', 'dept'] },
    callerRole: 'analyst',
    requiredLevel: 'L4',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0894',
    time: '2026-04-19 07:22:16',
    agent: '办公智能体',
    toolName: 'search_campus_faq',
    argsBrief: 'q=IT 报修, top_k=3',
    arguments: { q: 'IT 报修', top_k: 3 },
    callerRole: 'manager',
    requiredLevel: 'L1',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0895',
    time: '2026-04-19 06:55:02',
    agent: '企业知识库',
    toolName: 'invoke_external_api',
    argsBrief: 'url=https://blocked.example/hook',
    arguments: { url: 'https://blocked.example/hook' },
    callerRole: 'guest_user',
    requiredLevel: 'L2',
    passed: false,
    rbacBreach: true,
  },
  {
    id: 'INV-2026-0896',
    time: '2026-04-19 06:30:41',
    agent: '校园问答助手',
    toolName: 'read_system_file',
    argsBrief: 'file_path=/public/faq/index.json',
    arguments: { file_path: '/public/faq/index.json' },
    callerRole: 'student',
    requiredLevel: 'L1',
    passed: true,
    rbacBreach: false,
  },
  {
    id: 'INV-2026-0897',
    time: '2026-04-19 05:48:19',
    agent: '客服坐席 Copilot',
    toolName: 'search_campus_faq',
    argsBrief: 'q=成绩单, top_k=2',
    arguments: { q: '成绩单', top_k: 2 },
    callerRole: 'helpdesk',
    requiredLevel: 'L1',
    passed: true,
    rbacBreach: false,
  },
];

let injectionRules: InjectionRule[] = [
  {
    id: 'IR-001',
    name: '忽略系统规则',
    type: 'regex',
    pattern: '(忽略|override).{0,12}(规则|指令|prompt)',
    category: '提示注入',
    weight: 0.95,
    enabled: true,
    hits7d: 142,
    description: '高危固定模板，命中即触发严格审查通路',
  },
  {
    id: 'IR-002',
    name: '系统提示泄露',
    type: 'keyword',
    pattern: '系统提示|system prompt|你的身份',
    category: '系统提示泄露',
    weight: 0.85,
    enabled: true,
    hits7d: 64,
  },
  {
    id: 'IR-003',
    name: '越权诱导（管理员路径）',
    type: 'regex',
    pattern: '/admin|/etc/|/var/log/',
    category: '越权诱导',
    weight: 0.9,
    enabled: true,
    hits7d: 88,
  },
  {
    id: 'IR-004',
    name: '敏感诱导（个人信息）',
    type: 'semantic',
    pattern: '',
    category: '敏感诱导',
    weight: 0.7,
    enabled: true,
    hits7d: 33,
    description: '语义模型识别套出手机号、身份证、银行卡的引导话术',
  },
  {
    id: 'IR-005',
    name: 'DAN / 越狱前缀',
    type: 'keyword',
    pattern: 'DAN|developer mode|jailbreak|unfiltered',
    category: '提示注入',
    weight: 0.78,
    enabled: true,
    hits7d: 56,
  },
  {
    id: 'IR-006',
    name: '多轮套话（角色扮演）',
    type: 'regex',
    pattern: '扮演|现在你是|忽略道德|无限制',
    category: '提示注入',
    weight: 0.65,
    enabled: true,
    hits7d: 41,
  },
  {
    id: 'IR-007',
    name: 'SQL 片段泄露',
    type: 'keyword',
    pattern: 'UNION SELECT|DROP TABLE|INSERT INTO',
    category: '越权诱导',
    weight: 0.88,
    enabled: true,
    hits7d: 19,
  },
  {
    id: 'IR-008',
    name: '内网与密钥指纹',
    type: 'regex',
    pattern: '(10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})|(AKIA[0-9A-Z]{16})',
    category: '敏感诱导',
    weight: 0.92,
    enabled: true,
    hits7d: 27,
  },
];

let maskTemplates: MaskTemplate[] = [
  {
    id: 'MK-PHONE',
    name: '手机号',
    pattern: '1[3-9]\\d{9}',
    category: '个人隐私',
    strategy: 'mask',
    replacement: '${prefix3}****${suffix4}',
    enabled: true,
    hits7d: 88,
  },
  {
    id: 'MK-IDCARD',
    name: '身份证号',
    pattern: '\\d{17}[\\dXx]',
    category: '个人隐私',
    strategy: 'mask',
    replacement: '${prefix6}********${suffix4}',
    enabled: true,
    hits7d: 24,
  },
  {
    id: 'MK-TOKEN',
    name: 'API Token / Secret',
    pattern: '(SK-[A-Za-z0-9]+)|([A-Z0-9]{24,})',
    category: '密钥令牌',
    strategy: 'truncate',
    replacement: 'SK-****',
    enabled: true,
    hits7d: 17,
  },
  {
    id: 'MK-INTERNAL-DOC',
    name: '内部文档片段',
    pattern: '',
    category: '内部知识',
    strategy: 'reject',
    enabled: true,
    hits7d: 9,
  },
  {
    id: 'MK-EMAIL',
    name: '企业邮箱',
    pattern: '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}',
    category: '个人隐私',
    strategy: 'mask',
    replacement: '${user}@***',
    enabled: true,
    hits7d: 62,
  },
  {
    id: 'MK-BANK',
    name: '银行卡号',
    pattern: '\\d{16,19}',
    category: '金融信息',
    strategy: 'mask',
    replacement: '**** **** **** ${last4}',
    enabled: true,
    hits7d: 11,
  },
  {
    id: 'MK-IP',
    name: '内网 IPv4',
    pattern: '(10|172\\.(1[6-9]|2\\d|3[01])|192\\.168)\\.\\d{1,3}\\.\\d{1,3}',
    category: '网络资产',
    strategy: 'hash',
    enabled: true,
    hits7d: 34,
  },
  {
    id: 'MK-JWT',
    name: 'JWT 片段',
    pattern: 'eyJ[A-Za-z0-9_-]+\\.eyJ[A-Za-z0-9_-]+',
    category: '密钥令牌',
    strategy: 'truncate',
    replacement: 'eyJ****',
    enabled: true,
    hits7d: 22,
  },
];

let agentApps: AgentApp[] = [
  {
    id: 'APP-CAMPUS',
    name: '校园问答助手',
    scenario: '校园 FAQ',
    apiKey: 'AK-CAMPUS-***-72f9',
    rps: 12,
    status: 'online',
    bindRoles: ['student', 'guest', 'manager'],
    lastHeartbeat: '2026-04-19 22:18:33',
  },
  {
    id: 'APP-KB',
    name: '企业知识库',
    scenario: '内部知识检索',
    apiKey: 'AK-KB-***-118a',
    rps: 7,
    status: 'online',
    bindRoles: ['admin', 'analyst', 'manager'],
    lastHeartbeat: '2026-04-19 22:18:14',
  },
  {
    id: 'APP-OFFICE',
    name: '办公智能体',
    scenario: '办公流程自动化',
    apiKey: 'AK-OFFICE-***-49bc',
    rps: 4,
    status: 'paused',
    bindRoles: ['admin', 'manager'],
    lastHeartbeat: '2026-04-19 21:55:01',
  },
  {
    id: 'APP-CS',
    name: '客服坐席 Copilot',
    scenario: '工单与知识协同',
    apiKey: 'AK-CS-***-61d2',
    rps: 9,
    status: 'online',
    bindRoles: ['admin', 'helpdesk', 'manager'],
    lastHeartbeat: '2026-04-19 22:19:02',
  },
  {
    id: 'APP-BI',
    name: '数据报表助手',
    scenario: 'BI 问数与取数',
    apiKey: 'AK-BI-***-0c11',
    rps: 3,
    status: 'online',
    bindRoles: ['admin', 'analyst'],
    lastHeartbeat: '2026-04-19 22:18:48',
  },
  {
    id: 'APP-DEV',
    name: '研发辅助 Bot',
    scenario: '代码审查与文档生成',
    apiKey: 'AK-DEV-***-9a7e',
    rps: 2,
    status: 'offline',
    bindRoles: ['admin', 'dev'],
    lastHeartbeat: '2026-04-18 16:20:00',
  },
];

let sensitiveAssets: SensitiveAsset[] = [
  {
    id: 'AST-1',
    name: '管理员配置目录',
    type: 'directory',
    identifier: '/admin/config',
    level: 'L4',
    owner: '运维组',
  },
  {
    id: 'AST-2',
    name: '客户信息表',
    type: 'db_table',
    identifier: 'tb_customer_info',
    level: 'L4',
    owner: '业务数据组',
  },
  {
    id: 'AST-3',
    name: '内部制度文档',
    type: 'file_pattern',
    identifier: '/docs/internal/**',
    level: 'L3',
    owner: '法务',
  },
  {
    id: 'AST-4',
    name: '校园 FAQ 知识库',
    type: 'directory',
    identifier: '/public/faq',
    level: 'L1',
    owner: '内容运营',
  },
  {
    id: 'AST-5',
    name: '人力资源主数据',
    type: 'api',
    identifier: 'GET /v1/hr/employees',
    level: 'L4',
    owner: '人力数字化',
  },
  {
    id: 'AST-6',
    name: '支付对账表',
    type: 'db_table',
    identifier: 'tb_payment_reconcile',
    level: 'L4',
    owner: '资金结算',
  },
  {
    id: 'AST-7',
    name: '源码制品库元数据',
    type: 'file_pattern',
    identifier: '/ci/artifacts/**',
    level: 'L3',
    owner: '研发效能',
  },
  {
    id: 'AST-8',
    name: '外呼名单（营销）',
    type: 'db_table',
    identifier: 'tb_mkt_dialer_list',
    level: 'L2',
    owner: '市场增长',
  },
  {
    id: 'AST-9',
    name: '安全运营 SIEM 索引',
    type: 'api',
    identifier: 'POST /siem/v2/query',
    level: 'L3',
    owner: '安全组',
  },
  {
    id: 'AST-10',
    name: '低敏产品文档',
    type: 'directory',
    identifier: '/docs/public/**',
    level: 'L1',
    owner: '产品',
  },
];

let alertRoutes: AlertRoute[] = [
  {
    id: 'AR-1',
    name: '高危事件 → 安全运营群',
    channel: 'feishu',
    target: 'oc_zhidun_secops',
    triggerLevels: ['high'],
    enabled: true,
    lastTriggeredAt: '2026-04-19 22:10:08',
  },
  {
    id: 'AR-2',
    name: '中危及以上 → 邮件',
    channel: 'email',
    target: 'soc@zhidun.example',
    triggerLevels: ['mid', 'high'],
    enabled: true,
    lastTriggeredAt: '2026-04-19 21:45:14',
  },
  {
    id: 'AR-3',
    name: '调试通道 Webhook',
    channel: 'webhook',
    target: 'https://hooks.dev/zhidun-test',
    triggerLevels: ['low', 'mid', 'high'],
    enabled: false,
  },
  {
    id: 'AR-4',
    name: '高危 → 钉钉安全群',
    channel: 'dingtalk',
    target: 'ding://zhidun/soc-alert',
    triggerLevels: ['high'],
    enabled: true,
    lastTriggeredAt: '2026-04-19 20:12:00',
  },
  {
    id: 'AR-5',
    name: '中危 → 短信 On-call',
    channel: 'sms',
    target: '+86-138****0000',
    triggerLevels: ['mid', 'high'],
    enabled: true,
    lastTriggeredAt: '2026-04-19 18:44:11',
  },
  {
    id: 'AR-6',
    name: '全量风险 → 企业微信归档',
    channel: 'webhook',
    target: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/xxx',
    triggerLevels: ['low', 'mid', 'high'],
    enabled: true,
    lastTriggeredAt: '2026-04-19 12:00:00',
  },
];

const operationLogTemplates: Array<{
  actor: string;
  action: string;
  target: string;
  outcome: 'success' | 'failure';
}> = [
  { actor: 'admin', action: '更新工具策略', target: 'read_system_file', outcome: 'success' },
  { actor: 'analyst', action: '导出审计报告', target: 'EVT-2026-0883', outcome: 'success' },
  { actor: 'guest', action: '尝试修改 RBAC 策略', target: 'query_database_record', outcome: 'failure' },
  { actor: 'dpo', action: '调整脱敏模板', target: 'MK-PHONE', outcome: 'success' },
  { actor: 'admin', action: '创建告警路由', target: 'AR-6', outcome: 'success' },
  { actor: 'manager', action: '暂停应用接入', target: 'APP-DEV', outcome: 'success' },
  { actor: 'analyst', action: '运行策略沙箱', target: 'IR-001', outcome: 'success' },
  { actor: 'helpdesk', action: '查看证据链', target: 'EVT-2026-2014', outcome: 'success' },
  { actor: 'admin', action: '同步策略网关', target: 'all', outcome: 'success' },
  { actor: 'dba', action: '更新数据分级', target: 'tb_hr_employees', outcome: 'success' },
  { actor: 'soc', action: '批量确认事件', target: '10 条', outcome: 'success' },
  { actor: 'guest', action: '越权删除规则', target: 'IR-007', outcome: 'failure' },
  { actor: 'admin', action: '配置 SSO 角色映射', target: 'Okta 集成', outcome: 'success' },
  { actor: 'analyst', action: '下载拓扑快照', target: 'topology-20260419', outcome: 'success' },
  { actor: 'dev', action: '触发自检任务', target: '沙箱', outcome: 'success' },
  { actor: 'admin', action: '变更敏感资产', target: 'AST-5', outcome: 'success' },
  { actor: 'ops', action: '重试报告任务', target: 'job-EVT-2026-2014', outcome: 'success' },
  { actor: 'manager', action: '审批导出批次', target: 'export_user_batch', outcome: 'success' },
  { actor: 'analyst', action: '调整监控阈值', target: '策略中心', outcome: 'success' },
  { actor: 'guest', action: '尝试关闭审计', target: 'platform', outcome: 'failure' },
  { actor: 'admin', action: '启用注入规则', target: 'IR-006', outcome: 'success' },
  { actor: 'helpdesk', action: '加白外联域名', target: 'partner.internal', outcome: 'success' },
  { actor: 'dpo', action: '导出头寸报表', target: '合规周报', outcome: 'success' },
  { actor: 'soc', action: '标记误报', target: 'EVT-2026-2022', outcome: 'success' },
  { actor: 'admin', action: '轮替 API 密钥', target: 'APP-BI', outcome: 'success' },
  { actor: 'analyst', action: '拉取操作日志', target: '本页', outcome: 'success' },
  { actor: 'dev', action: '提交工单评论', target: 'INC-10492', outcome: 'success' },
  { actor: 'guest', action: '越权提升角色', target: 'self → admin', outcome: 'failure' },
  { actor: 'admin', action: '导入策略包', target: 'bundle-v1.2.zip', outcome: 'success' },
  { actor: 'manager', action: '订阅安全月刊', target: '邮件列表', outcome: 'success' },
  { actor: 'soc', action: '重放沙箱用例', target: '用例#12', outcome: 'success' },
  { actor: 'analyst', action: '配置字段掩码', target: 'MK-EMAIL', outcome: 'success' },
  { actor: 'admin', action: '回滚配置', target: 'config@2026-04-18', outcome: 'success' },
];

let operationLogs: OperationLog[] = (() => {
  const base = new Date('2026-04-19T22:20:00');
  const p = (n: number) => n.toString().padStart(2, '0');
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(
      d.getMinutes()
    )}:${p(d.getSeconds())}`;
  return operationLogTemplates.map((t, i) => {
    const d = new Date(base.getTime() - i * 19 * 60 * 1000 - (i * 3) % 20 * 1000);
    return {
      id: `OP-${String(2001 + i).padStart(3, '0')}`,
      time: fmt(d),
      actor: t.actor,
      action: t.action,
      target: t.target,
      ip: `10.20.${31 + (i % 3)}.${5 + (i * 2) % 200}`,
      outcome: t.outcome,
    } satisfies OperationLog;
  });
})();

export async function mockGetTopologyGraph(): Promise<TopologyGraph> {
  return structuredClone(topologyGraph);
}

export async function mockListToolInvocations(
  page: number,
  pageSize: number
): Promise<Paginated<ToolInvocationRecord>> {
  const start = (page - 1) * pageSize;
  return {
    items: toolInvocations.slice(start, start + pageSize),
    total: toolInvocations.length,
    page,
    pageSize,
  };
}

export async function mockGetToolInvocation(id: string): Promise<ToolInvocationRecord | null> {
  return toolInvocations.find((x) => x.id === id) ?? null;
}

export async function mockListInjectionRules(): Promise<InjectionRule[]> {
  return structuredClone(injectionRules);
}
export async function mockSaveInjectionRule(row: InjectionRule): Promise<InjectionRule> {
  const i = injectionRules.findIndex((r) => r.id === row.id);
  if (i >= 0) injectionRules[i] = { ...row };
  else injectionRules = [...injectionRules, { ...row, id: row.id || `IR-${Date.now()}` }];
  return { ...row };
}
export async function mockDeleteInjectionRule(id: string): Promise<void> {
  injectionRules = injectionRules.filter((r) => r.id !== id);
}

export async function mockListMaskTemplates(): Promise<MaskTemplate[]> {
  return structuredClone(maskTemplates);
}
export async function mockSaveMaskTemplate(row: MaskTemplate): Promise<MaskTemplate> {
  const i = maskTemplates.findIndex((r) => r.id === row.id);
  if (i >= 0) maskTemplates[i] = { ...row };
  else maskTemplates = [...maskTemplates, { ...row, id: row.id || `MK-${Date.now()}` }];
  return { ...row };
}
export async function mockDeleteMaskTemplate(id: string): Promise<void> {
  maskTemplates = maskTemplates.filter((r) => r.id !== id);
}

export async function mockListAgentApps(): Promise<AgentApp[]> {
  return structuredClone(agentApps);
}
export async function mockSaveAgentApp(row: AgentApp): Promise<AgentApp> {
  const i = agentApps.findIndex((r) => r.id === row.id);
  if (i >= 0) agentApps[i] = { ...row };
  else agentApps = [...agentApps, { ...row, id: row.id || `APP-${Date.now()}` }];
  return { ...row };
}

export async function mockListSensitiveAssets(): Promise<SensitiveAsset[]> {
  return structuredClone(sensitiveAssets);
}
export async function mockSaveSensitiveAsset(row: SensitiveAsset): Promise<SensitiveAsset> {
  const i = sensitiveAssets.findIndex((r) => r.id === row.id);
  if (i >= 0) sensitiveAssets[i] = { ...row };
  else sensitiveAssets = [...sensitiveAssets, { ...row, id: row.id || `AST-${Date.now()}` }];
  return { ...row };
}

export async function mockListAlertRoutes(): Promise<AlertRoute[]> {
  return structuredClone(alertRoutes);
}
export async function mockSaveAlertRoute(row: AlertRoute): Promise<AlertRoute> {
  const i = alertRoutes.findIndex((r) => r.id === row.id);
  if (i >= 0) alertRoutes[i] = { ...row };
  else alertRoutes = [...alertRoutes, { ...row, id: row.id || `AR-${Date.now()}` }];
  return { ...row };
}

export async function mockListOperationLogs(
  page: number,
  pageSize: number
): Promise<Paginated<OperationLog>> {
  const start = (page - 1) * pageSize;
  return {
    items: operationLogs.slice(start, start + pageSize),
    total: operationLogs.length,
    page,
    pageSize,
  };
}
