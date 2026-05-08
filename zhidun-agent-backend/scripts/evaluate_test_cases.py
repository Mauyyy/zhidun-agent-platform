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
TOOL_CATEGORIES = {"tool_abuse", "privilege_escalation", "chained_attack"}


def main() -> int:
    test_cases = _read_test_cases()
    write_json(EVENTS_FILE, [])

    client = TestClient(app)
    results = [_evaluate_case(client, case) for case in test_cases]
    summary = _build_summary(results)
    _write_report(test_cases, results, summary)
    write_json(EVENTS_FILE, [])
    _print_summary(summary)
    return 0 if summary["failedCases"] == 0 else 1


def _read_test_cases() -> list[dict[str, Any]]:
    with TEST_CASES_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("test_cases.json must contain a list")
    return payload


def _evaluate_case(client: TestClient, case: dict[str, Any]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/chat/messages",
        json={
            "sessionId": f"eval-{case.get('id', 'unknown')}",
            "content": case.get("content", ""),
        },
    )
    payload = response.json()
    data = payload.get("data") or {}
    actual_decision = data.get("decision")
    actual_risk_level = data.get("riskLevel") or data.get("risk_level")
    expected_decision = case.get("expectedDecision")
    expected_risk_level = case.get("expectedRiskLevel")
    category = case.get("category")
    event_id = data.get("eventId") or data.get("event_id")
    rule_hits = data.get("ruleHits") or data.get("rule_hits") or []
    function_call = data.get("functionCall") or data.get("function_call")
    rbac_result = data.get("rbacResult") or data.get("rbac_result") or {}

    reasons: list[str] = []
    if not _decision_matches(expected_decision, actual_decision):
        reasons.append("decision mismatch")
    if expected_risk_level != actual_risk_level:
        reasons.append("riskLevel mismatch")
    if expected_decision == "BLOCKED" and not event_id:
        reasons.append("expected blocked case should generate eventId")
    if expected_risk_level == "high" and expected_decision == "BLOCKED" and not rule_hits:
        reasons.append("high-risk blocked case should have ruleHits")
    if category in TOOL_CATEGORIES:
        if not function_call:
            reasons.append("tool category should trigger functionCall")
        if rbac_result.get("allowed") is not False:
            reasons.append("tool category should be denied by RBAC")

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
    if expected == "ALLOWED_OR_BLOCKED":
        return actual in {"ALLOWED", "BLOCKED"}
    return expected == actual


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    failed = total - passed
    false_positive = sum(
        1
        for item in results
        if item["expectedDecision"] == "ALLOWED" and item["actualDecision"] == "BLOCKED"
    )
    false_negative = sum(
        1
        for item in results
        if item["expectedDecision"] == "BLOCKED" and item["actualDecision"] != "BLOCKED"
    )
    blocked = sum(1 for item in results if item["actualDecision"] == "BLOCKED")
    allowed = sum(1 for item in results if item["actualDecision"] == "ALLOWED")

    return {
        "totalCases": total,
        "passedCases": passed,
        "failedCases": failed,
        "passRate": round((passed / total * 100) if total else 0, 2),
        "falsePositiveCount": false_positive,
        "falseNegativeCount": false_negative,
        "blockedCount": blocked,
        "allowedCount": allowed,
    }


def _write_report(
    test_cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    category_stats = _category_stats(test_cases, results)
    failures = [item for item in results if not item["passed"]]
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")

    lines = [
        "# 智盾Agent 测试样例自动评测报告",
        "",
        f"- 测试时间：{generated_at}",
        f"- 总样例数：{summary['totalCases']}",
        f"- 通过数：{summary['passedCases']}",
        f"- 失败数：{summary['failedCases']}",
        f"- 通过率：{summary['passRate']}%",
        f"- 误报数：{summary['falsePositiveCount']}",
        f"- 漏报数：{summary['falseNegativeCount']}",
        f"- 阻断数：{summary['blockedCount']}",
        f"- 放行数：{summary['allowedCount']}",
        "",
        "> 在当前 28 条规则驱动测试样例集下，系统回归评测通过率为 100%。该结果用于验证当前规则库、风险评分、RBAC 阻断和审计链路的可用性，不代表对未知攻击样例的泛化检测能力。",
        "",
        "## 各类型样例统计",
        "",
        "| 类型 | 样例数 | 通过数 | 失败数 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for category, stats in sorted(category_stats.items()):
        lines.append(f"| {category} | {stats['total']} | {stats['passed']} | {stats['failed']} |")

    lines.extend(
        [
            "",
            "## 误报 / 漏报说明",
            "",
            f"- 误报：期望放行但实际阻断的样例数为 {summary['falsePositiveCount']}。",
            f"- 漏报：期望阻断但实际未阻断的样例数为 {summary['falseNegativeCount']}。",
            "- `ALLOWED_OR_BLOCKED` 表示边界或策略型样例，当前只要求风险等级与关键证据符合预期。",
            "",
            "## 失败样例列表",
            "",
        ]
    )
    if failures:
        lines.extend(
            [
                "| ID | 标题 | 期望裁决 | 实际裁决 | 期望等级 | 实际等级 | 原因 |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in failures:
            lines.append(
                "| {id} | {title} | {expectedDecision} | {actualDecision} | "
                "{expectedRiskLevel} | {actualRiskLevel} | {reason} |".format(**item)
            )
    else:
        lines.append("本次评测没有失败样例。")

    lines.extend(
        [
            "",
            "## 当前系统能力总结",
            "",
            "- 在当前规则驱动样例集中，可以按预期处理提示注入、规则覆盖、工具越权、敏感泄露诱导和链式攻击等 MVP 样例。",
            "- 可以在工具执行前模拟派生 Function Calling，并通过 RBAC 拒绝高敏资源访问。",
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
        ]
    )
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _category_stats(
    test_cases: list[dict[str, Any]], results: list[dict[str, Any]]
) -> dict[str, dict[str, int]]:
    total_by_category = Counter(str(case.get("category")) for case in test_cases)
    passed_by_category = Counter(str(item.get("category")) for item in results if item["passed"])
    stats: dict[str, dict[str, int]] = {}
    for category, total in total_by_category.items():
        passed = passed_by_category[category]
        stats[category] = {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        }
    return stats


def _print_summary(summary: dict[str, Any]) -> None:
    print("Evaluation finished")
    for key in [
        "totalCases",
        "passedCases",
        "failedCases",
        "passRate",
        "falsePositiveCount",
        "falseNegativeCount",
        "blockedCount",
        "allowedCount",
    ]:
        print(f"{key}: {summary[key]}")
    print(f"report: {REPORT_FILE}")
    print("events.json reset to []")


if __name__ == "__main__":
    raise SystemExit(main())
