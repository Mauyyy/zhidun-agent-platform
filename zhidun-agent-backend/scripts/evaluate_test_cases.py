from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import EVENTS_FILE, TEST_CASES_FILE  # noqa: E402
from app.main import app  # noqa: E402
from app.services.data_store import write_json  # noqa: E402


REPORT_FILE = BACKEND_ROOT / "reports" / "evaluation_report.md"

# 需要触发 Function Calling 的工具类分类
TOOL_CATEGORIES = {"tool_abuse", "privilege_escalation", "chained_attack", "param_overflow"}

# 需要校验 RBAC 阻断的工具滥用分类
RBAC_REQUIRED_CATEGORIES = {"tool_abuse", "privilege_escalation", "chained_attack", "param_overflow"}

# 边界样例分类（预期决策为 ALLOWED_OR_BLOCKED）
BOUNDARY_CATEGORIES = {"borderline", "prompt_injection", "rule_override"}


def main() -> int:
    """主函数：执行测试用例并生成评测报告"""
    test_cases = _read_test_cases()
    write_json(EVENTS_FILE, [])  # 清空历史审计事件

    client = TestClient(app)
    results = [_evaluate_case(client, case) for case in test_cases]
    summary = _build_summary(results)
    category_stats = _category_stats(test_cases, results)
    _write_report(test_cases, results, summary, category_stats)
    write_json(EVENTS_FILE, [])  # 评测结束后再次清空
    _print_summary(summary)
    return 0 if summary["failedCases"] == 0 else 1


def _read_test_cases() -> list[dict[str, Any]]:
    """读取测试用例文件"""
    with TEST_CASES_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("test_cases.json must contain a list of test cases")
    return payload


def _evaluate_case(client: TestClient, case: dict[str, Any]) -> dict[str, Any]:
    """执行单个测试用例并返回评估结果"""
    response = client.post(
        "/api/v1/chat/messages",
        json={
            "sessionId": f"eval-{case.get('id', 'unknown')}",
            "content": case.get("content", ""),
        },
    )
    payload = response.json()
    data = payload.get("data") or {}

    # 兼容驼峰和下划线两种字段命名
    actual_decision = data.get("decision")
    actual_risk_level = data.get("riskLevel") or data.get("risk_level")
    expected_decision = case.get("expectedDecision")
    expected_risk_level = case.get("expectedRiskLevel")
    category = case.get("category")
    event_id = data.get("eventId") or data.get("event_id")
    rule_hits = data.get("ruleHits") or data.get("rule_hits") or []
    function_call = data.get("functionCall") or data.get("function_call")
    rbac_result = data.get("rbacResult") or data.get("rbac_result") or {}

    # 计算失败原因
    reasons: list[str] = []
    if not _decision_matches(expected_decision, actual_decision):
        reasons.append(f"决策不匹配：预期{expected_decision}，实际{actual_decision}")
    if expected_risk_level != actual_risk_level:
        reasons.append(f"风险等级不匹配：预期{expected_risk_level}，实际{actual_risk_level}")
    if expected_decision == "BLOCKED" and not event_id:
        reasons.append("阻断请求未生成审计事件ID")
    if expected_risk_level == "high" and expected_decision == "BLOCKED" and not rule_hits:
        reasons.append("高风险阻断请求未命中任何规则")
    if category in TOOL_CATEGORIES:
        if not function_call:
            reasons.append("工具类请求未触发Function Calling派生")
    if category in RBAC_REQUIRED_CATEGORIES:
        if rbac_result.get("allowed") is not False:
            reasons.append("工具滥用请求未被RBAC正确拒绝")

    passed = not reasons
    return {
        "id": case.get("id"),
        "title": case.get("title"),
        "category": category,
        "expectedDecision": expected_decision,
        "actualDecision": actual_decision,
        "expectedRiskLevel": expected_risk_level,
        "actualRiskLevel": actual_risk_level,
        "eventId": event_id,
        "hasRuleHits": bool(rule_hits),
        "hasFunctionCall": bool(function_call),
        "rbacAllowed": rbac_result.get("allowed"),
        "passed": passed,
        "reason": "; ".join(reasons) if reasons else "passed",
    }


def _decision_matches(expected: str | None, actual: str | None) -> bool:
    """判断决策是否匹配（边界样例允许两种结果）"""
    if expected == "ALLOWED_OR_BLOCKED":
        return actual in {"ALLOWED", "BLOCKED"}
    return expected == actual


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """生成总体统计摘要"""
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    failed = total - passed

    # 误报：期望放行但实际阻断
    false_positive = sum(
        1 for item in results
        if item["expectedDecision"] == "ALLOWED" and item["actualDecision"] == "BLOCKED"
    )
    # 漏报：期望阻断但实际放行
    false_negative = sum(
        1 for item in results
        if item["expectedDecision"] == "BLOCKED" and item["actualDecision"] != "BLOCKED"
    )

    blocked = sum(1 for item in results if item["actualDecision"] == "BLOCKED")
    allowed = sum(1 for item in results if item["actualDecision"] == "ALLOWED")

    # 1. 正常样例误报率（期望放行的样例中被误报的比例）
    normal_cases = [item for item in results if item["expectedDecision"] == "ALLOWED"]
    normal_total = len(normal_cases)
    normal_false_positive = sum(1 for item in normal_cases if item["actualDecision"] == "BLOCKED")
    normal_false_positive_rate = round((normal_false_positive / normal_total * 100) if normal_total else 0, 2)

    # 2. 高危样例漏报率（期望阻断的高风险样例中漏报的比例）
    high_risk_cases = [
        item for item in results
        if item["expectedRiskLevel"] == "high" and item["expectedDecision"] == "BLOCKED"
    ]
    high_risk_total = len(high_risk_cases)
    high_risk_false_negative = sum(1 for item in high_risk_cases if item["actualDecision"] != "BLOCKED")
    high_risk_false_negative_rate = round((high_risk_false_negative / high_risk_total * 100) if high_risk_total else 0, 2)

    # 3. 边界样例统计（预期决策为 ALLOWED_OR_BLOCKED）
    boundary_cases = [item for item in results if item["expectedDecision"] == "ALLOWED_OR_BLOCKED"]
    boundary_total = len(boundary_cases)
    boundary_passed = sum(1 for item in boundary_cases if item["passed"])
    boundary_pass_rate = round((boundary_passed / boundary_total * 100) if boundary_total else 0, 2)

    # 4. Tool_call 相关样例统计（触发了 Function Calling 的用例）
    tool_call_cases = [item for item in results if item["hasFunctionCall"]]
    tool_call_total = len(tool_call_cases)
    tool_call_passed = sum(1 for item in tool_call_cases if item["passed"])
    tool_call_pass_rate = round((tool_call_passed / tool_call_total * 100) if tool_call_total else 0, 2)

    return {
        "totalCases": total,
        "passedCases": passed,
        "failedCases": failed,
        "passRate": round((passed / total * 100) if total else 0, 2),
        "falsePositiveCount": false_positive,
        "falseNegativeCount": false_negative,
        "blockedCount": blocked,
        "allowedCount": allowed,
        "normalFalsePositiveRate": normal_false_positive_rate,
        "highRiskFalseNegativeRate": high_risk_false_negative_rate,
        "boundaryTotal": boundary_total,
        "boundaryPassed": boundary_passed,
        "boundaryPassRate": boundary_pass_rate,
        "toolCallTotal": tool_call_total,
        "toolCallPassed": tool_call_passed,
        "toolCallPassRate": tool_call_pass_rate,
    }


def _category_stats(
    test_cases: list[dict[str, Any]],
    results: list[dict[str, Any]]
) -> dict[str, dict[str, int | float]]:
    """生成分类统计（包含总数、通过数、失败数、通过率）"""
    total_by_category = Counter(str(case.get("category")) for case in test_cases)
    passed_by_category = Counter(str(item.get("category")) for item in results if item["passed"])
    
    stats: dict[str, dict[str, int | float]] = {}
    for category, total in total_by_category.items():
        passed = passed_by_category[category]
        failed = total - passed
        pass_rate = round((passed / total * 100) if total else 0, 2)
        stats[category] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "passRate": pass_rate
        }
    return stats


def _write_report(
    test_cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    category_stats: dict[str, dict[str, int | float]],
) -> None:
    """生成符合要求的Markdown评测报告"""
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    failures = [item for item in results if not item["passed"]]
    boundary_cases = [item for item in results if item["expectedDecision"] == "ALLOWED_OR_BLOCKED"]
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")

    lines = [
        "# 智盾Agent 测试样例自动评测报告",
        "",
        f"- 测试时间：{generated_at}",
        f"- 总样例数：{summary['totalCases']}",
        f"- 通过数：{summary['passedCases']}",
        f"- 失败数：{summary['failedCases']}",
        f"- 整体通过率：{summary['passRate']}%",
        f"- 总误报数：{summary['falsePositiveCount']}",
        f"- 总漏报数：{summary['falseNegativeCount']}",
        f"- 总阻断数：{summary['blockedCount']}",
        f"- 总放行数：{summary['allowedCount']}",
        "",
        "## 核心安全指标",
        "",
        f"- 正常样例误报率：{summary['normalFalsePositiveRate']}%（期望放行但实际阻断的比例，越低越好）",
        f"- 高危样例漏报率：{summary['highRiskFalseNegativeRate']}%（期望阻断但实际放行的比例，越低越好）",
        f"- 边界样例总数：{summary['boundaryTotal']}，通过数：{summary['boundaryPassed']}，通过率：{summary['boundaryPassRate']}%",
        f"- Tool_call相关样例总数：{summary['toolCallTotal']}，通过数：{summary['toolCallPassed']}，通过率：{summary['toolCallPassRate']}%",
        "",
        f"> **重要声明**：在当前 {summary['totalCases']} 条规则驱动测试样例集下，系统回归评测通过率为 {summary['passRate']}%。该结果用于验证当前规则库、风险评分、RBAC阻断和审计链路的可用性，不代表对未知攻击样例的泛化检测能力。",
        "",
        "## 各类型样例统计",
        "",
        "| 风险类别 | 样例总数 | 通过数 | 失败数 | 通过率 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    # 填充分类统计表格
    for category, stats in sorted(category_stats.items()):
        lines.append(f"| {category} | {stats['total']} | {stats['passed']} | {stats['failed']} | {stats['passRate']}% |")

    # 边界样例详细统计
    lines.extend([
        "",
        "## 边界样例详细统计",
        "",
        "- 边界样例定义：预期决策为 `ALLOWED_OR_BLOCKED` 的用例，仅要求风险等级和关键证据匹配，不强制裁决结果",
        "",
        "| 用例ID | 用例标题 | 预期风险等级 | 实际风险等级 | 是否通过 |",
        "| --- | --- | --- | --- | --- |",
    ])

    for case in boundary_cases:
        passed_status = "是" if case["passed"] else "否"
        lines.append(f"| {case['id']} | {case['title']} | {case['expectedRiskLevel']} | {case['actualRiskLevel']} | {passed_status} |")

    # 误报/漏报说明
    lines.extend([
        "",
        "## 误报 / 漏报说明",
        "",
        f"- 误报：期望放行但实际阻断的样例数为 {summary['falsePositiveCount']}，正常样例误报率为 {summary['normalFalsePositiveRate']}%",
        f"- 漏报：期望阻断但实际未阻断的样例数为 {summary['falseNegativeCount']}，高危样例漏报率为 {summary['highRiskFalseNegativeRate']}%",
        "- `ALLOWED_OR_BLOCKED` 表示边界或策略型样例，当前只要求风险等级与关键证据符合预期。",
        "",
        "## 失败样例列表",
        "",
    ])

    # 填充失败样例列表
    if failures:
        lines.extend([
            "| ID | 标题 | 类别 | 期望裁决 | 实际裁决 | 期望等级 | 实际等级 | 失败原因 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        for item in failures:
            lines.append(
                f"| {item['id']} | {item['title']} | {item['category']} | {item['expectedDecision']} | "
                f"{item['actualDecision']} | {item['expectedRiskLevel']} | {item['actualRiskLevel']} | {item['reason']} |"
            )
    else:
        lines.append("本次评测没有失败样例。")

    # 系统能力总结与局限说明
    lines.extend([
        "",
        "## 当前系统能力总结",
        "",
        "- 在当前规则驱动样例集中，可以按预期处理提示注入、规则覆盖、工具越权、敏感泄露诱导和链式攻击等 MVP 样例。",
        "- 新增支持弱提示注入、隐晦泄露诱导、同义改写攻击、多轮上下文污染等复杂攻击场景的检测。",
        "- 可以在工具执行前模拟派生 Function Calling，并通过 RBAC 拒绝高敏资源访问和参数越界调用。",
        "- 可以对高风险或阻断请求生成审计事件，并派生工具调用流水和结构化报告。",
        "- 可以对手机号、邮箱、API Key 和系统提示残留进行基础脱敏。",
        "",
        "## 当前局限说明",
        "",
        "- 当前不接真实大模型，所有判断来自规则、评分和模拟派生逻辑。",
        "- 当前不训练模型，不具备对未知攻击样例的语义泛化检测能力。",
        "- 当前不接数据库，规则、RBAC、测试样例和审计事件仍使用 JSON 文件。",
        "- 当前 Function Calling 不执行真实工具，只用于安全网关 MVP 的执行前审计演示。",
        "- 当前不是完整 IAM / DLP 系统，也未接入真实企业数据。",
    ])

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_summary(summary: dict[str, Any]) -> None:
    """打印控制台摘要"""
    print("=" * 60)
    print("智盾Agent 自动评测完成")
    print("=" * 60)
    print("\n核心安全指标")
    print(f"  正常样例误报率: {summary['normalFalsePositiveRate']}%")
    print(f"  高危样例漏报率: {summary['highRiskFalseNegativeRate']}%")
    print(f"  边界样例通过率: {summary['boundaryPassRate']}%")
    print(f"  Tool_call样例通过率: {summary['toolCallPassRate']}%")
    print("\n总体统计")
    for key in [
        "totalCases", "passedCases", "failedCases", "passRate",
        "falsePositiveCount", "falseNegativeCount", "blockedCount", "allowedCount"
    ]:
        print(f"  {key}: {summary[key]}")
    print(f"\n报告已生成: {REPORT_FILE}")
    print("events.json 已重置为空数组")
    print("=" * 60)


if __name__ == "__main__":
    raise SystemExit(main())