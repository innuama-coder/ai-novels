import unittest

from scripts import validate_prd_contract as validator


DEFAULT_CLAIM_ID = "CLAIM-01"
DEFAULT_CONSTRAINT_ROLE = "opening pressure and failed extraction method"


def valid_proposal_claims(
    claim_id=DEFAULT_CLAIM_ID,
    constraint_role=DEFAULT_CONSTRAINT_ROLE,
):
    return {
        claim_id: {
            "claim": "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。",
            "constraint_role": constraint_role,
        }
    }


def valid_proposal_claims_with_setup():
    claims = valid_proposal_claims()
    claims["CLAIM-10"] = {
        "claim": "掌握关键情报的男人在事故中死亡，导致阻止重大事件的最后线索被认为藏在他的记忆里。",
        "constraint_role": "pre-extraction causal setup",
    }
    return claims


def proposal_trace_text(
    claim_id=DEFAULT_CLAIM_ID,
    constraint_role=DEFAULT_CONSTRAINT_ROLE,
):
    return f"{claim_id}; role={constraint_role}"


def skill_verdict_section():
    return """
## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
"""


def hld_information_boundary_section(artifact_text):
    return "## HLD information boundary table\n" + artifact_text.split(
        "\n## HLD information boundary table\n",
        1,
    )[1].split("\n## Skill Verdict\n", 1)[0].rstrip()


def hld_expansion_requirement_section(artifact_text):
    return "## HLD expansion requirement list\n" + artifact_text.split(
        "\n## HLD expansion requirement list\n",
        1,
    )[1].split("\n## Upstream required HLD entities\n", 1)[0].rstrip()


def add_integrated_hld_information_boundary_table(artifacts):
    boundary_table = hld_information_boundary_section(artifacts["05"])
    hld_requirements = hld_expansion_requirement_section(artifacts["07"])
    final_package = artifacts["final-prd-package"]
    artifacts["final-prd-package"] = final_package.replace(
        "| Information-flow table | artifact 05 |",
        "| Information-flow table | artifact 05 |\n| HLD information boundary table | artifact 05 |",
    )
    for artifact_id in ["08", "final-prd-package"]:
        artifacts[artifact_id] = artifacts[artifact_id].rstrip() + "\n\n" + boundary_table + "\n"
    artifacts["final-prd-package"] = artifacts["final-prd-package"].rstrip() + "\n\n" + hld_requirements + "\n"
    return artifacts


def valid_prd_artifacts(
    proposal_claim_id=DEFAULT_CLAIM_ID,
    constraint_role=DEFAULT_CONSTRAINT_ROLE,
):
    proposal_trace = proposal_trace_text(proposal_claim_id, constraint_role)
    exact_claim = "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。"
    artifacts = {
        "01": f"""
# Scope

## Specified part scope table

| Scope id | Scope name | Start boundary | End boundary | Excluded material | Independence proof | Proposal trace | Verdict |
|---|---|---|---|---|---|---|---|
| PRD-PART-01 | 记忆读取危机段 | {exact_claim} | 数字生命体让研究员终止自己。 | 危机后的长期余波不在本段展开。 | 本段围绕读取、打开、终止形成闭环。 | {proposal_trace} | pass |
{skill_verdict_section()}""",
        "02": f"""
# Part Goal

## Part goal table

| Required story state at start | Required story state at end | Story function | Required pressure | Success criteria | Proposal trace | Verdict |
|---|---|---|---|---|---|---|
| {exact_claim} | 危机解除且数字生命体被终止。 | 完成从强行读取到自我终止的主线推进。 | 重大事件倒计时与研究员旧情共同施压。 | 主干场景能证明记忆为何打开以及生命为何放弃。 | {proposal_trace} | pass |
{skill_verdict_section()}""",
        "03": f"""
# Trunk Scenes

## Trunk scene table

| Scene id | Order | Entry state | Roles | Environment | Event | Causal output | Proposal trace | Scene content | Previous dependency | Next pressure | Indispensability proof |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PRD-S01 | 1 | 逝者已经死亡但脑活动仍可被维持。 | 研究员与组织值班组承担读取压力。 | 生命维持实验室作为技术入口。 | {exact_claim} | 组织确认常规读取路径仍可尝试。 | {proposal_trace} | 研究员在生命维持实验室确认逝者脑活动仍被维持，组织值班组把脑波分析接入读取流程；她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读。 | 指定部分起点要求组织仍试图读取逝者记忆。 | 读取路径受阻后必须寻找非常规办法。 | 没有该场就无法建立死亡后读取压力和技术入口。 |
{skill_verdict_section()}""",
        "04": f"""
# Conflict Value

## Conflict and value-shift table

| Scene id | Conflict type | Conflict pressure | Start value | End value | Irreversibility | Proposal trace |
|---|---|---|---|---|---|---|
| PRD-S01 | external | 重大事件倒计时迫使组织执行：{exact_claim} | 组织仍相信常规读取路径可用。 | 读取路径开始暴露不可靠，逝者记忆无法被直接打开。 | 时间压力无法复位，死亡后维持脑活动的技术路线已经被启动。 | {proposal_trace} |
{skill_verdict_section()}""",
        "05": """
# Information Flow

## Information-flow table

| Scene id | Reader learns | Focal character learns | Other actor information | Misbelief or concealment | Next-scene pressure | HLD information need |
|---|---|---|---|---|---|---|
| PRD-S01 | 读者知道脑活动被维持。 | 研究员知道常规读取仍是第一选择。 | 组织知道倒计时更紧。 | 关键记忆是否可读仍被误判。 | 继续推进脑波分析。 | HLD 需定义脑波分析边界。 |

## HLD information boundary table

| Information boundary id | Story anchor scene id | Narrative reveal scene id | Narrative reveal order | Disclosure tier | Information object | Reader access | Known by entity refs | Hidden from entity refs | Reveal predecessor boundary refs | Reveal condition type | Freeze refs | Source | HLD obligation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PRD-INFO-01 | PRD-S01 | PRD-S01 | 1 | operational_intelligence | 脑活动维持与读取窗口 | concealed | entity:研究员 | reader, entity:组织值班组 | none | action | freeze:PRD-FREEZE-01 | scene:PRD-S01 | HLD 必须把读取窗口绑定到场景事件，不得提前公开关键记忆。 |
""" + skill_verdict_section(),
        "06": f"""
# Freeze Boundary

## Freeze boundary list

| Freeze id | Frozen item | Source | Downstream no-change rule | Reopen condition |
|---|---|---|---|---|
| PRD-FREEZE-01 | PRD-S01 的事件事实和因果输出。 | scene:PRD-S01, claim:{proposal_claim_id} | HLD 不得把脑波分析改成已经成功读取。 | 如果生命维持技术无法支撑该事件，重开 PRD。 |
{skill_verdict_section()}""",
        "07": f"""
# HLD Requirements

## HLD expansion requirement list

| Requirement id | Required expansion | Supports scene ids | Information boundary refs | Inherited HLD obligations | Required answer | Boundary | Source |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | 生命维持和脑波分析的技术边界。 | PRD-S01 | PRD-INFO-01 | HLD 必须把读取窗口绑定到场景事件，不得提前公开关键记忆。 | HLD 需回答为何脑活动可维持但记忆不可直接读取。 | 不能改写 PRD-S01 的读取失败方向。 | scene:PRD-S01 |

## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Scene content | 研究员在生命维持实验室确认逝者脑活动仍被维持，组织值班组把脑波分析接入读取流程；她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读。 | 研究员 | character | scene:PRD-S01 |
| UPF-PRD-S01-02 | Roles | 研究员与组织值班组承担读取压力。 | 组织值班组 | group | scene:PRD-S01 |
| UPF-PRD-S01-03 | Environment | 生命维持实验室作为技术入口。 | 生命维持实验室 | environment | scene:PRD-S01 |
| UPF-PRD-S01-04 | Scene content | 研究员在生命维持实验室确认逝者脑活动仍被维持，组织值班组把脑波分析接入读取流程；她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读。 | 脑波分析 | event | scene:PRD-S01, claim:{proposal_claim_id} |
""" + skill_verdict_section(),
        "08": f"""
# PRD Assembly

## PRD Integration Verdict

| Field | Value |
|---|---|
| Source completeness | pass |
| Scene fact preservation | pass |
| No new business content | pass |
| Package readiness | pass |

## Scene Source Map

| Scene id | Order | Event fact | Causal output | Proposal trace | Source artifact |
|---|---|---|---|---|---|
| PRD-S01 | 1 | {exact_claim} | 组织确认常规读取路径仍可尝试。 | {proposal_trace} | artifact 03 |
{skill_verdict_section()}""",
        "09": """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `pass` with source evidence. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `pass` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_pending_human_review` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Human review pending | P2 | Human review blocks HLD entry. |
""" + skill_verdict_section(),
        "final-prd-package": f"""
# Final PRD Package

## Final PRD package index

| Section | Source |
|---|---|
| Proposal source and PRD entry proof | harness input gate |
| Specified part scope | artifact 01 |
| Part goal and acceptance boundary | artifact 02 |
| Linear trunk scene table | artifact 03 |
| Conflict and value-shift table | artifact 04 |
| Information-flow table | artifact 05 |
| PRD freeze boundaries | artifact 06 |
| HLD expansion requirements | artifact 07 |
| Upstream required HLD entities | artifact 07 |
| PRD Integration Verdict | artifact 08 |
| Scene Source Map | artifact 08 |
| PRD risk report and HLD entry verdict | artifact 09 |

## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Scene content | 研究员在生命维持实验室确认逝者脑活动仍被维持，组织值班组把脑波分析接入读取流程；她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读。 | 研究员 | character | scene:PRD-S01 |
| UPF-PRD-S01-02 | Roles | 研究员与组织值班组承担读取压力。 | 组织值班组 | group | scene:PRD-S01 |
| UPF-PRD-S01-03 | Environment | 生命维持实验室作为技术入口。 | 生命维持实验室 | environment | scene:PRD-S01 |
| UPF-PRD-S01-04 | Scene content | 研究员在生命维持实验室确认逝者脑活动仍被维持，组织值班组把脑波分析接入读取流程；她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读。 | 脑波分析 | event | scene:PRD-S01, claim:{proposal_claim_id} |
""",
    }
    return add_integrated_hld_information_boundary_table(artifacts)


def valid_prd_artifacts_with_pre_extraction_setup():
    setup_trace = proposal_trace_text("CLAIM-10", "pre-extraction causal setup")
    extraction_trace = proposal_trace_text()
    setup_claim = "掌握关键情报的男人在事故中死亡，导致阻止重大事件的最后线索被认为藏在他的记忆里。"
    exact_claim = "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。"
    artifacts = valid_prd_artifacts()
    artifacts["03"] = f"""
# Trunk Scenes

## Trunk scene table

| Scene id | Order | Entry state | Roles | Environment | Event | Causal output | Proposal trace | Scene content | Previous dependency | Next pressure | Indispensability proof |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PRD-S01 | 1 | 情报员掌握关键情报但尚未完成交接。 | 情报员、接应组、组织远程值班组。 | 雨夜交通枢纽外的临时接应点，正常上报路径被倒计时压缩。 | {setup_claim} | 关键情报未能正常交接，组织只能把最后线索转向死者记忆。 | {setup_trace} | 情报员抵达接应点前试图发送压缩情报包，但只传出无法解码的残片；事故发生后，接应组只拿到空白载体和死亡通知，组织确认关键情报交接失败。 | Proposal 的重大事件倒计时要求关键情报必须被追回。 | 组织只能转向死者记忆读取。 | 没有该场，死亡后读取缺少事故死亡和情报交接失败的因果起点。 |
| PRD-S02 | 2 | 逝者已经死亡但脑活动仍可被维持。 | 研究员与组织值班组承担读取压力。 | 生命维持实验室作为技术入口。 | {exact_claim} | 组织确认常规读取路径仍可尝试。 | {extraction_trace} | 研究员在生命维持实验室确认逝者脑活动仍被维持，组织值班组把脑波分析接入读取流程；她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读。 | PRD-S01 已证明关键情报交接失败。 | 读取路径受阻后必须寻找非常规办法。 | 没有该场就无法建立死亡后读取压力和技术入口。 |

## Scene execution table

| Unit id | Parent scene id | Unit order | Scene objective | On-page action | Conflict turn | Exit state | Proposal trace |
|---|---|---|---|---|---|---|---|
| PRD-S01-U01 | PRD-S01 | 1 | 建立关键情报尚未完成交接。 | 情报员抵达接应点前尝试发送压缩情报包。 | 正常交接从可期待变成不稳定。 | 接应组只收到无法解码残片。 | {setup_trace} |
| PRD-S01-U02 | PRD-S01 | 2 | 证明事故死亡切断情报路径。 | 接应组确认载体损坏、情报员死亡、传输记录不可复原。 | 组织失去正常上报路径。 | 最后线索被转入死者记忆。 | {setup_trace} |
| PRD-S02-U01 | PRD-S02 | 1 | 建立死亡后读取入口。 | 研究员看到逝者被接入生命维持和脑波分析流程。 | 死亡从终点变成可争夺窗口。 | 脑活动窗口被保留。 | {extraction_trace} |
| PRD-S02-U02 | PRD-S02 | 2 | 证明读取还未成功。 | 值班组等待脑波分析稳定并要求研究员准备读取。 | 技术入口形成但关键记忆仍未出现。 | 后续必须验证记忆是否可达。 | {extraction_trace} |
{skill_verdict_section()}"""
    artifacts["04"] = f"""
# Conflict Value

## Conflict and value-shift table

| Scene id | Conflict type | Conflict pressure | Start value | End value | Irreversibility | Proposal trace |
|---|---|---|---|---|---|---|
| PRD-S01 | information | 关键情报必须交接，但{setup_claim} | 组织仍期待正常交接。 | 正常交接失败，最后线索转入死者记忆。 | 情报员死亡和交接中断无法复位。 | {setup_trace} |
| PRD-S02 | external | 重大事件倒计时迫使组织执行：{exact_claim} | 组织仍相信常规读取路径可用。 | 读取路径开始暴露不可靠，逝者记忆无法被直接打开。 | 时间压力无法复位，死亡后维持脑活动的技术路线已经被启动。 | {extraction_trace} |
{skill_verdict_section()}"""
    artifacts["05"] = """
# Information Flow

## Information-flow table

| Scene id | Reader learns | Focal character learns | Other actor information | Misbelief or concealment | Next-scene pressure | HLD information need |
|---|---|---|---|---|---|---|
| PRD-S01 | 读者知道关键情报交接失败。 | 研究员尚未入场，只能后来接收失败事实。 | 组织知道正常上报路径已经断裂。 | 关键情报的完整内容仍不可见。 | 转向死者记忆读取。 | HLD 需定义情报交接机制和事故现场边界。 |
| PRD-S02 | 读者知道脑活动被维持。 | 研究员知道常规读取仍是第一选择。 | 组织知道倒计时更紧。 | 关键记忆是否可读仍被误判。 | 继续推进脑波分析。 | HLD 需定义脑波分析边界。 |

## HLD information boundary table

| Information boundary id | Story anchor scene id | Narrative reveal scene id | Narrative reveal order | Disclosure tier | Information object | Reader access | Known by entity refs | Hidden from entity refs | Reveal predecessor boundary refs | Reveal condition type | Freeze refs | Source | HLD obligation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PRD-INFO-01 | PRD-S01 | PRD-S01 | 1 | protected_memory | 关键情报交接失败 | concealed | entity:组织值班组 | reader, entity:研究员 | none | evidence_change | freeze:PRD-FREEZE-01 | scene:PRD-S01 | HLD 必须保留事故死亡后最后线索转入死者记忆。 |
| PRD-INFO-02 | PRD-S02 | PRD-S02 | 2 | operational_intelligence | 脑活动维持与读取窗口 | concealed | entity:研究员 | reader, entity:组织值班组 | PRD-INFO-01 | action | freeze:PRD-FREEZE-02 | scene:PRD-S02 | HLD 必须把读取窗口绑定到场景事件，不得提前公开关键记忆。 |
""" + skill_verdict_section()
    artifacts["06"] = f"""
# Freeze Boundary

## Freeze boundary list

| Freeze id | Frozen item | Source | Downstream no-change rule | Reopen condition |
|---|---|---|---|---|
| PRD-FREEZE-01 | PRD-S01 的事故死亡和交接失败因果起点。 | scene:PRD-S01, claim:CLAIM-10 | HLD 不得改写为情报已经正常交接。 | 如果 proposal 重开并取消事故死亡，重开 PRD。 |
| PRD-FREEZE-02 | PRD-S02 的事件事实和因果输出。 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} | HLD 不得把脑波分析改成已经成功读取。 | 如果生命维持技术无法支撑该事件，重开 PRD。 |
{skill_verdict_section()}"""
    artifacts["07"] = f"""
# HLD Requirements

## HLD expansion requirement list

| Requirement id | Required expansion | Supports scene ids | Information boundary refs | Inherited HLD obligations | Required answer | Boundary | Source |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | 情报交接机制与事故现场边界。 | PRD-S01 | PRD-INFO-01 | HLD 必须保留事故死亡后最后线索转入死者记忆。 | HLD 需回答为何关键情报未能正常传递且只能转入死者记忆。 | 不能改写 PRD-S01 的事故死亡和交接失败。 | scene:PRD-S01, claim:CLAIM-10 |
| HLD-REQ-02 | 生命维持和脑波分析的技术边界。 | PRD-S02 | PRD-INFO-02 | HLD 必须把读取窗口绑定到场景事件，不得提前公开关键记忆。 | HLD 需回答为何脑活动可维持但记忆不可直接读取。 | 不能改写 PRD-S02 的读取失败方向。 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |

## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Scene content | 情报员抵达接应点前试图发送压缩情报包，但只传出无法解码的残片；事故发生后，接应组只拿到空白载体和死亡通知，组织确认关键情报交接失败。 | 情报员 | character | scene:PRD-S01, claim:CLAIM-10 |
| UPF-PRD-S01-02 | Roles | 情报员、接应组、组织远程值班组。 | 接应组 | group | scene:PRD-S01 |
| UPF-PRD-S01-03 | Environment | 雨夜交通枢纽外的临时接应点，正常上报路径被倒计时压缩。 | 临时接应点 | environment | scene:PRD-S01 |
| UPF-PRD-S01-04 | Causal output | 关键情报未能正常交接，组织只能把最后线索转向死者记忆。 | 关键情报 | event | scene:PRD-S01, claim:CLAIM-10 |
| UPF-PRD-S02-01 | Roles | 研究员与组织值班组承担读取压力。 | 研究员 | character | scene:PRD-S02 |
| UPF-PRD-S02-02 | Roles | 研究员与组织值班组承担读取压力。 | 组织值班组 | group | scene:PRD-S02 |
| UPF-PRD-S02-03 | Environment | 生命维持实验室作为技术入口。 | 生命维持实验室 | environment | scene:PRD-S02 |
| UPF-PRD-S02-04 | Event | {exact_claim} | 脑波分析 | event | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
{skill_verdict_section()}"""
    artifacts["final-prd-package"] = f"""
# Final PRD Package

## Final PRD package index

| Section | Source |
|---|---|
| Proposal source and PRD entry proof | harness input gate |
| Specified part scope | artifact 01 |
| Part goal and acceptance boundary | artifact 02 |
| Linear trunk scene table | artifact 03 |
| Conflict and value-shift table | artifact 04 |
| Information-flow table | artifact 05 |
| PRD freeze boundaries | artifact 06 |
| HLD expansion requirements | artifact 07 |
| Upstream required HLD entities | artifact 07 |
| PRD Integration Verdict | artifact 08 |
| Scene Source Map | artifact 08 |
| PRD risk report and HLD entry verdict | artifact 09 |

## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Scene content | 情报员抵达接应点前试图发送压缩情报包，但只传出无法解码的残片；事故发生后，接应组只拿到空白载体和死亡通知，组织确认关键情报交接失败。 | 情报员 | character | scene:PRD-S01, claim:CLAIM-10 |
| UPF-PRD-S01-02 | Roles | 情报员、接应组、组织远程值班组。 | 接应组 | group | scene:PRD-S01 |
| UPF-PRD-S01-03 | Environment | 雨夜交通枢纽外的临时接应点，正常上报路径被倒计时压缩。 | 临时接应点 | environment | scene:PRD-S01 |
| UPF-PRD-S01-04 | Causal output | 关键情报未能正常交接，组织只能把最后线索转向死者记忆。 | 关键情报 | event | scene:PRD-S01, claim:CLAIM-10 |
| UPF-PRD-S02-01 | Roles | 研究员与组织值班组承担读取压力。 | 研究员 | character | scene:PRD-S02 |
| UPF-PRD-S02-02 | Roles | 研究员与组织值班组承担读取压力。 | 组织值班组 | group | scene:PRD-S02 |
| UPF-PRD-S02-03 | Environment | 生命维持实验室作为技术入口。 | 生命维持实验室 | environment | scene:PRD-S02 |
| UPF-PRD-S02-04 | Event | {exact_claim} | 脑波分析 | event | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
"""
    artifacts["08"] = f"""
# PRD Assembly

## PRD Integration Verdict

| Field | Value |
|---|---|
| Source completeness | pass |
| Scene fact preservation | pass |
| No new business content | pass |
| Package readiness | pass |

## Scene Source Map

| Scene id | Order | Event fact | Causal output | Proposal trace | Source artifact |
|---|---|---|---|---|---|
| PRD-S01 | 1 | {setup_claim} | 关键情报未能正常交接，组织只能把最后线索转向死者记忆。 | {setup_trace} | artifact 03 |
| PRD-S02 | 2 | {exact_claim} | 组织确认常规读取路径仍可尝试。 | {extraction_trace} | artifact 03 |
{skill_verdict_section()}"""
    return add_integrated_hld_information_boundary_table(artifacts)


def artifacts_with_story_logic_risk_without_boundaries():
    artifacts = valid_prd_artifacts_with_pre_extraction_setup()
    artifacts["03"] = artifacts["03"].replace(
        "她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读。",
        "她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读；后段将出现研究员只提取可用情报、隐去完整原因、被保护者重新卷入风险，以及数字生命体利用系统提示误导研究员执行终止。",
    )
    return artifacts


def artifacts_with_story_logic_boundary_table():
    artifacts = artifacts_with_story_logic_risk_without_boundaries()
    boundary_table = f"""

## Story logic boundary table

| Boundary id | Logic concern | Frozen answer | HLD expansion room | Required HLD entity refs | Source |
|---|---|---|---|---|---|
| PRD-LOGIC-01 | 可用情报与完整原因分层 | 可用情报只包含阻止重大事件所需的时间、地点、触发条件和阻断方式；完整原因才包含被保护者身份、关系和私人动机，因此研究员可以化解危机但隐去完整原因。 | HLD 可设计具体事件机制和行动方式，但不能让被保护者身份成为阻断危机的必要条件。 | entity:研究员 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
| PRD-LOGIC-02 | 被保护者因果关系 | 被保护者是被胁迫或被误导卷入触发链的人，不是简单加害者；暴露身份会导致组织处置、审查或重新卷入。 | HLD 可设计被保护者身份和卷入方式，但不能改成抽象伦理理由或无关旁支。 | entity:研究员 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
| PRD-LOGIC-03 | 数字生命体终止骗局能力边界 | 数字生命体不能控制外部系统或凭空伪造权限，只能利用既有告警、日志、对话节奏和研究员误判，让终止看似风险控制。 | HLD 可设计平台权限、告警格式和终止流程，但不能改成组织命令、系统故障或无约束超能力。 | entity:研究员 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
"""
    artifacts["03"] = artifacts["03"].replace("\n## Skill Verdict", boundary_table + "\n## Skill Verdict")
    return artifacts


def artifacts_with_story_logic_plausibility_anchors():
    artifacts = artifacts_with_story_logic_risk_without_boundaries()
    boundary_table = f"""

## Story logic boundary table

| Boundary id | Logic concern | Frozen answer | HLD expansion room | Required HLD entity refs | Source |
|---|---|---|---|---|---|
| PRD-LOGIC-01 | 可用情报与完整原因分层 | 可用情报只包含阻止重大事件所需的时间、地点、触发条件、阻断方式和行动窗口；完整原因才包含被保护者身份、关系和私人动机，因此研究员可以化解危机但隐去完整原因。 | HLD 可设计具体事件机制、行动流程和报告格式，但不能让被保护者身份成为阻断危机的必要条件。 | entity:研究员 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
| PRD-LOGIC-02 | 被保护者因果关系 | 被保护者是被胁迫或被误导卷入触发链的人，不是简单加害者；暴露身份会导致组织处置、审查或重新卷入，并且被保护者与学长存在私人关系或亏欠关系，足以支撑学长封闭记忆和研究员隐瞒。 | HLD 可设计被保护者身份、与学长的关系、卷入方式和暴露后果，但不能改成抽象伦理理由或无关旁支。 | entity:研究员 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
| PRD-LOGIC-03 | 数字生命体终止骗局能力边界 | 数字生命体不能控制外部系统、不能凭空伪造权限、不能改写权限，只能利用既有告警、日志、系统提示、对话节奏、研究员误判和终止流程多重确认，让终止看似风险控制。 | HLD 可设计平台权限、告警格式、日志可见范围、终止确认流程和监听盲区，但不能改成组织命令、系统故障或无约束超能力。 | entity:研究员 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
| PRD-LOGIC-04 | 组织追问压力边界 | 组织在危机解除后仍会结案审查、追问情报缺口和评估数字生命体资产价值，但受隔离保存窗口、审查流程和终止权限限制，不能直接复制或接管数字生命体。 | HLD 可设计审查制度、保存期限、接管限制和组织内部分歧，但不能让组织压力消失，也不能让组织直接抢走终局选择权。 | entity:研究员 | scene:PRD-S02, claim:{DEFAULT_CLAIM_ID} |
"""
    artifacts["03"] = artifacts["03"].replace("\n## Skill Verdict", boundary_table + "\n## Skill Verdict")
    coverage_table = f"""

## Story logic requirement coverage

| Boundary id | HLD requirement id | Inherited frozen answer |
|---|---|---|
| PRD-LOGIC-01 | HLD-REQ-02 | 可用情报只包含阻止重大事件所需的时间、地点、触发条件、阻断方式和行动窗口；完整原因才包含被保护者身份、关系和私人动机，因此研究员可以化解危机但隐去完整原因。 |
| PRD-LOGIC-02 | HLD-REQ-02 | 被保护者是被胁迫或被误导卷入触发链的人，不是简单加害者；暴露身份会导致组织处置、审查或重新卷入，并且被保护者与学长存在私人关系或亏欠关系，足以支撑学长封闭记忆和研究员隐瞒。 |
| PRD-LOGIC-03 | HLD-REQ-02 | 数字生命体不能控制外部系统、不能凭空伪造权限、不能改写权限，只能利用既有告警、日志、系统提示、对话节奏、研究员误判和终止流程多重确认，让终止看似风险控制。 |
| PRD-LOGIC-04 | HLD-REQ-02 | 组织在危机解除后仍会结案审查、追问情报缺口和评估数字生命体资产价值，但受隔离保存窗口、审查流程和终止权限限制，不能直接复制或接管数字生命体。 |
"""
    artifacts["07"] = artifacts["07"].replace("\n## Skill Verdict", coverage_table + "\n## Skill Verdict")
    artifacts["final-prd-package"] = artifacts["final-prd-package"].rstrip() + coverage_table + "\n"
    return artifacts


class PrdSkillContractTests(unittest.TestCase):
    def test_contract_declares_prd_harness_and_nine_skills(self):
        contract = validator.load_contract()

        self.assertEqual(contract["harness"], "novel-prd-workflow")
        self.assertEqual(contract["prd_skill_count"], 9)
        self.assertEqual(
            contract["skills"],
            [
                "novel-part-scope-selector",
                "novel-part-goal-definer",
                "novel-trunk-scene-designer",
                "novel-scene-conflict-value-designer",
                "novel-scene-information-flow-designer",
                "novel-prd-freeze-boundary-writer",
                "novel-hld-expansion-requirement-writer",
                "novel-prd-integrator",
                "novel-prd-causality-checker",
            ],
        )

    def test_contract_requires_fact_level_claim_and_core_failure_checks(self):
        contract = validator.load_contract()
        static_checks = set(contract["static_checks"])

        self.assertIn("proposal_claim_fact_trace_required", static_checks)
        self.assertIn("core_check_failure_blocks_as_p0_p1_required", static_checks)

    def test_rejects_missing_required_static_checks(self):
        contract = {"static_checks": ["proposal_claim_fact_trace_required"]}

        with self.assertRaises(ValueError) as raised:
            validator.validate_required_static_checks(contract, "contract")

        self.assertIn("missing required static checks", str(raised.exception))

    def test_contract_rules_require_executable_coverage(self):
        contract = validator.load_contract()

        validator.validate_contract_rule_coverage(contract, "contract")

    def test_rejects_contract_rule_without_executable_coverage(self):
        contract = validator.load_contract()
        del contract["rule_coverage"]["PRD-CONTRACT-14"]

        with self.assertRaises(ValueError) as raised:
            validator.validate_contract_rule_coverage(contract, "contract")

        self.assertIn("missing rule coverage", str(raised.exception))

    def test_rejects_contract_rule_coverage_with_unknown_validator(self):
        contract = validator.load_contract()
        contract["rule_coverage"]["PRD-CONTRACT-14"]["validators"] = ["missing_validator"]

        with self.assertRaises(ValueError) as raised:
            validator.validate_contract_rule_coverage(contract, "contract")

        self.assertIn("unknown coverage validator", str(raised.exception))

    def test_rejects_contract_rule_coverage_with_unknown_test(self):
        contract = validator.load_contract()
        contract["rule_coverage"]["PRD-CONTRACT-14"]["tests"] = ["test_missing_regression"]

        with self.assertRaises(ValueError) as raised:
            validator.validate_contract_rule_coverage(contract, "contract")

        self.assertIn("unknown coverage test", str(raised.exception))

    def test_rejects_missing_independent_skill_sections(self):
        skill_text = """
---
name: bad-prd-skill
description: Use when testing.
---

# bad-prd-skill

## Responsibility
Does one thing.
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_skill_contract_text(skill_text, "bad-prd-skill")

        self.assertIn("missing required independent-skill section", str(raised.exception))

    def test_rejects_skill_without_structured_skill_verdict(self):
        skill_text = """
---
name: bad-prd-skill
description: Use when testing.
---

# bad-prd-skill

## Responsibility
Does one thing.

## Input
- Source.

## Output
Produces a table.

## Rules
- Stay in bounds.

## Boundary
- Do not rewrite upstream.

## References
Good output is checkable.

## Traceability
Trace to source.

## Acceptance
Pass when complete.
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_skill_contract_text(skill_text, "bad-prd-skill")

        self.assertIn("missing required independent-skill section: ## Skill Verdict", str(raised.exception))

    def test_contract_hard_gates_cover_information_flow_and_hld_expansion(self):
        contract = validator.load_contract()
        gate_owners = {gate["owner"] for gate in contract["hard_gates"]}

        self.assertIn("novel-scene-information-flow-designer", gate_owners)
        self.assertIn("novel-hld-expansion-requirement-writer", gate_owners)


class PrdArtifactTopologyTests(unittest.TestCase):
    def test_rejects_integrator_depending_on_risk_checker(self):
        graph = validator.expected_prd_artifact_dag()
        graph[7]["depends_on"] = ["09"]

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_artifact_topology(graph, "prd artifact graph")

        self.assertIn("artifact 08", str(raised.exception))

    def test_requires_final_package_over_integrator_and_risk_checker(self):
        graph = validator.expected_prd_artifact_dag()
        graph[-1]["depends_on"] = ["08"]

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_artifact_topology(graph, "prd artifact graph")

        self.assertIn("final-prd-package", str(raised.exception))


class PrdRunContractTests(unittest.TestCase):
    def test_contract_requires_artifact_or_blocked_runs(self):
        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_runs_declared({}, "contract")

        self.assertIn("artifact_runs or blocked_runs", str(raised.exception))

    def test_rejects_empty_convergence_log(self):
        manifest = """
# PRD workflow artifact run

## Convergence log
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_convergence_log(manifest, "manifest")

        self.assertIn("must include header and at least one row", str(raised.exception))

    def test_requires_refactor_trigger_after_three_attempts(self):
        manifest = """
# PRD workflow artifact run

## Convergence log

| Stable issue id | Root cause | Fix hypothesis | Regression proof | Attempt count | Versioned refactor trigger |
|---|---|---|---|---|---|
| P1-SCENE-TRACE | root cause exists | fix hypothesis exists | regression proof exists | 3 |  |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_convergence_log(manifest, "manifest")

        self.assertIn("requires Versioned refactor trigger", str(raised.exception))

    def test_formal_artifact_run_requires_upstream_proposal_risk_report(self):
        contract = validator.load_contract()
        artifact_run = {
            "id": "formal-run-without-upstream",
            "manifest": "docs/superpowers/runs/prd/2026-07-06-duanxian-prd-workflow-blocked/manifest.md",
            "skill_artifacts": {},
        }

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_run(artifact_run, contract, "formal run")

        self.assertIn("upstream_proposal_risk_report", str(raised.exception))


class PrdEntryGateTests(unittest.TestCase):
    def test_blocks_when_upstream_proposal_prd_entry_is_not_pass(self):
        proposal_risk_report = """
# Proposal Risk Report

## Output

| Field | Value |
|---|---|
| Agent quality verdict | `pass` |
| Human/intake confirmation verdict | `pending` |
| PRD entry verdict | `blocked_pending_human_confirmation` |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_upstream_proposal_entry_gate(
                proposal_risk_report,
                "proposal risk report",
            )

        self.assertIn("cannot start PRD", str(raised.exception))

    def test_rejects_upstream_claim_source_map_with_non_pass_coverage(self):
        proposal_risk_report = """
# Proposal Risk Report

## Output

| Field | Value |
|---|---|
| Agent quality verdict | `pass` |
| Human/intake confirmation verdict | `confirmed` |
| PRD entry verdict | `pass_to_prd` |

## Claim Source Map coverage

| Claim ID | Critical business claim | Constraint role | Coverage verdict | Evidence |
|---|---|---|---|---|
| CLAIM-01 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | opening pressure and failed extraction method | `fail` | Missing integration evidence. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.proposal_claims_from_risk_report(
                proposal_risk_report,
                "proposal risk report",
            )

        self.assertIn("Claim Source Map coverage must pass", str(raised.exception))


class PrdSceneTraceTests(unittest.TestCase):
    def test_rejects_upstream_hld_entity_without_fact_atom(self):
        artifact = """
## Upstream required HLD entities

| Upstream fact id | Source fact field | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|
| UPF-PRD-S01-01 | Roles | 研究员 | character | scene:PRD-S01, claim:CLAIM-01 |
"""
        canonical_scenes = {"PRD-S01": {}}

        with self.assertRaises(ValueError) as raised:
            validator.validate_upstream_required_hld_entities(
                artifact,
                canonical_scenes,
                valid_proposal_claims(),
                "artifact 07",
            )

        self.assertIn("Upstream fact atom", str(raised.exception))

    def test_rejects_upstream_hld_entity_with_crossed_scene_or_entity_identity(self):
        artifact = """
## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Event | 组织维持脑活动。 | 研究员 | character | scene:PRD-S02 |
| UPF-PRD-S02-01 | Event | 研究员接入读取流程。 | 组织 | group | scene:PRD-S01 |
"""
        canonical_scenes = {
            "PRD-S01": {"event": "研究员接入读取流程。"},
            "PRD-S02": {"event": "组织维持脑活动。"},
        }

        with self.assertRaises(ValueError) as raised:
            validator.validate_upstream_required_hld_entities(
                artifact,
                canonical_scenes,
                {},
                "artifact 07",
            )

        self.assertIn("fact id scene anchor", str(raised.exception))

    def test_rejects_upstream_hld_entity_when_atom_omits_entity(self):
        artifact = """
## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Event | 组织维持脑活动。 | 研究员 | character | scene:PRD-S01 |
"""
        canonical_scenes = {"PRD-S01": {"event": "组织维持脑活动。"}}

        with self.assertRaises(ValueError) as raised:
            validator.validate_upstream_required_hld_entities(
                artifact,
                canonical_scenes,
                {},
                "artifact 07",
            )

        self.assertIn("does not bind Required HLD entity", str(raised.exception))

    def test_rejects_upstream_hld_entity_when_atom_is_not_whole_source_field(self):
        artifact = """
## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Roles | 研究员 | 研究员 | character | scene:PRD-S01 |
"""
        canonical_scenes = {"PRD-S01": {"roles": "研究员、组织值班负责人。"}}

        with self.assertRaises(ValueError) as raised:
            validator.validate_upstream_required_hld_entities(
                artifact,
                canonical_scenes,
                {},
                "artifact 07",
            )

        self.assertIn("does not exactly match Source fact field", str(raised.exception))

    def test_rejects_final_package_without_hld_expansion_requirement_table(self):
        artifact_07 = """
## HLD expansion requirement list

| Requirement id | Required expansion | Supports scene ids | Information boundary refs | Inherited HLD obligations | Required answer | Boundary | Source |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | 读取边界。 | PRD-S01 | none | none | HLD 定义读取限制。 | 不得直接读取关键记忆。 | scene:PRD-S01 |
"""
        final_package = "# Final PRD Package\n"

        with self.assertRaises(ValueError) as raised:
            validator.validate_hld_expansion_requirement_integration(
                artifact_07,
                final_package,
                "formal run",
            )

        self.assertIn("HLD expansion requirement list", str(raised.exception))

    def test_rejects_hld_requirement_source_scene_drift(self):
        rows = [
            {
                "Requirement id": "HLD-REQ-01",
                "Required expansion": "死亡边缘读取体系的技术边界。",
                "Supports scene ids": "PRD-S01",
                "Information boundary refs": "none",
                "Inherited HLD obligations": "none",
                "Required answer": "HLD 必须定义直接读取的失败限制。",
                "Boundary": "不得让关键记忆被直接读取。",
                "Source": "scene:PRD-S02",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_hld_expansion_requirements(
                rows,
                {"PRD-S01": {}, "PRD-S02": {}},
                {},
                "artifact 07",
            )

        self.assertIn("does not exactly match Supports scene ids", str(raised.exception))

    def test_rejects_duplicate_hld_expansion_requirement_id(self):
        row = {
            "Requirement id": "HLD-REQ-01",
            "Required expansion": "死亡边缘读取体系的技术边界。",
            "Supports scene ids": "PRD-S01",
            "Information boundary refs": "none",
            "Inherited HLD obligations": "none",
            "Required answer": "HLD 必须定义直接读取的失败限制。",
            "Boundary": "不得让关键记忆被直接读取。",
            "Source": "scene:PRD-S01",
        }

        with self.assertRaises(ValueError) as raised:
            validator.validate_hld_expansion_requirements(
                [row, row.copy()],
                {"PRD-S01": {}},
                {},
                "artifact 07",
            )

        self.assertIn("duplicate HLD expansion requirement id", str(raised.exception))

    def test_rejects_unmapped_story_logic_requirement(self):
        logic_rows = [
            {
                "Boundary id": "PRD-LOGIC-01",
                "Frozen answer": "可用情报必须与完整原因分层，避免提前暴露被保护者。",
                "Source": "scene:PRD-S01",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_story_logic_requirement_coverage(
                logic_rows,
                [],
                [],
                "artifact 07",
            )

        self.assertIn("unmapped Story logic boundary", str(raised.exception))

    def test_rejects_story_logic_entity_missing_from_hld_handoff(self):
        logic_rows = [
            {
                "Boundary id": "PRD-LOGIC-02",
                "Required HLD entity refs": "entity:被保护者",
                "Source": "scene:PRD-S10",
            }
        ]
        entity_rows = [
            {
                "Required HLD entity": "研究员",
                "Required entity type": "character",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_story_logic_entity_closure(
                logic_rows,
                entity_rows,
                "artifact 07",
            )

        self.assertIn("unknown Story logic entity", str(raised.exception))

    def test_rejects_story_logic_entity_registered_only_in_unrelated_scene(self):
        logic_rows = [
            {
                "Boundary id": "PRD-LOGIC-02",
                "Required HLD entity refs": "entity:被保护者",
                "Source": "scene:PRD-S10",
            }
        ]
        entity_rows = [
            {
                "Upstream fact id": "UPF-PRD-S11-01",
                "Required HLD entity": "被保护者",
                "Required entity type": "character",
                "Source refs": "scene:PRD-S11",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_story_logic_entity_closure(
                logic_rows,
                entity_rows,
                "artifact 07",
            )

        self.assertIn("Story logic entity source does not anchor", str(raised.exception))

    def test_rejects_unmapped_information_boundary_obligation(self):
        boundary_rows = [
            {
                "Information boundary id": "PRD-INFO-01",
                "HLD obligation": "HLD 必须保持记忆读取失败的因果边界。",
            }
        ]
        requirement_rows = [
            {
                "Requirement id": "HLD-REQ-01",
                "Information boundary refs": "none",
                "Inherited HLD obligations": "none",
                "Required answer": "HLD 必须定义读取失败的表现。",
                "Boundary": "不得改写读取失败。",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_information_boundary_obligation_coverage(
                boundary_rows,
                requirement_rows,
                "artifact 07",
            )

        self.assertIn("unmapped HLD information boundary obligation", str(raised.exception))

    def test_rejects_information_boundary_ref_without_obligation_preservation(self):
        boundary_rows = [
            {
                "Information boundary id": "PRD-INFO-06",
                "Story anchor scene id": "PRD-S15",
                "Narrative reveal scene id": "PRD-S17",
                "HLD obligation": "HLD 必须让终止骗局在既有权限、日志和确认流程内成立。",
            }
        ]
        requirement_rows = [
            {
                "Requirement id": "HLD-REQ-01",
                "Information boundary refs": "PRD-INFO-06",
                "Inherited HLD obligations": "HLD 必须定义学生时代资料与旧校徽的出现方式。",
                "Supports scene ids": "PRD-S15",
                "Source": "scene:PRD-S15",
                "Required answer": "HLD 必须定义学生时代资料与旧校徽的出现方式。",
                "Boundary": "不得把数字生命体写成学长复活。",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_information_boundary_obligation_coverage(
                boundary_rows,
                requirement_rows,
                "artifact 07",
            )

        self.assertIn("does not preserve HLD obligation", str(raised.exception))

    def test_rejects_information_boundary_ref_without_scene_anchor(self):
        boundary_rows = [
            {
                "Information boundary id": "PRD-INFO-06",
                "Story anchor scene id": "PRD-S15",
                "Narrative reveal scene id": "PRD-S17",
                "HLD obligation": "HLD 必须让终止骗局在既有权限、日志和确认流程内成立。",
            }
        ]
        requirement_rows = [
            {
                "Requirement id": "HLD-REQ-01",
                "Information boundary refs": "PRD-INFO-06",
                "Inherited HLD obligations": "HLD 必须让终止骗局在既有权限、日志和确认流程内成立。",
                "Supports scene ids": "PRD-S01",
                "Source": "scene:PRD-S01",
                "Required answer": "HLD 必须让终止骗局在既有权限、日志和确认流程内成立。",
                "Boundary": "不得改写既有终止流程。",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_information_boundary_obligation_coverage(
                boundary_rows,
                requirement_rows,
                "artifact 07",
            )

        self.assertIn("does not support information boundary scenes", str(raised.exception))

    def test_rejects_upstream_hld_entity_table_drift(self):
        canonical = """
## Upstream required HLD entities

| Upstream fact id | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|
| UPF-PRD-S01-01 | 研究员必须参与读取。 | 研究员 | character | scene:PRD-S01, claim:CLAIM-01 |
"""
        drifted = canonical.replace("研究员必须参与读取", "研究员不得参与读取")

        with self.assertRaises(ValueError) as raised:
            validator.validate_upstream_hld_entity_integration(
                canonical,
                drifted,
                "formal run",
            )

        self.assertIn("Upstream required HLD entities drift", str(raised.exception))

    def test_formal_prd_run_validates_package_attestation(self):
        contract = validator.load_contract()
        artifact_run = contract["artifact_runs"][0]

        validator.validate_formal_prd_artifact_run(
            artifact_run,
            contract,
            "formal run",
        )

    def test_rejects_information_boundary_entity_not_registered_for_hld_handoff(self):
        artifacts = valid_prd_artifacts_with_pre_extraction_setup()
        for artifact_id in ["05", "08", "final-prd-package"]:
            artifacts[artifact_id] = artifacts[artifact_id].replace(
                "entity:组织值班组",
                "entity:未注册组织",
                1,
            )

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims_with_setup(),
            )

        self.assertIn("knowledge entity", str(raised.exception))

    def test_rejects_hld_boundary_table_missing_from_integrator_and_final_package(self):
        artifacts = valid_prd_artifacts_with_pre_extraction_setup()
        artifacts["08"] = artifacts["08"].split("\n## HLD information boundary table\n", 1)[0]

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims_with_setup(),
            )

        self.assertIn("HLD information boundary table", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_hld_information_boundary_table(self):
        artifacts = valid_prd_artifacts()
        artifacts["05"] = artifacts["05"].split("\n## HLD information boundary table\n", 1)[0] + skill_verdict_section()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("HLD information boundary table", str(raised.exception))

    def test_rejects_scene_source_map_fact_drift_for_same_scene_id(self):
        canonical_scenes = {
            "PRD-S01": {
                "order": "1",
                "event": "组织维持逝者脑活动并启动脑波分析。",
                "causal_output": "组织确认常规读取路径仍可尝试。",
                "proposal_trace": "CLAIM-01",
            }
        }
        source_map_rows = [
            {
                "Scene id": "PRD-S01",
                "Order": "1",
                "Event fact": "组织已经取得完整情报并结束分析。",
                "Causal output": "组织确认常规读取路径仍可尝试。",
                "Proposal trace": "CLAIM-01",
                "Source artifact": "artifact 03",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_scene_source_map_rows(
                canonical_scenes,
                source_map_rows,
                "Scene Source Map",
            )

        self.assertIn("event fact drift", str(raised.exception))

    def test_rejects_missing_conflict_value_scene_coverage(self):
        canonical_scenes = {
            "PRD-S01": {
                "order": "1",
                "event": "组织维持逝者脑活动并启动脑波分析。",
                "causal_output": "组织确认常规读取路径仍可尝试。",
                "proposal_trace": "CLAIM-01",
            },
            "PRD-S02": {
                "order": "2",
                "event": "脑波分析发现关键记忆自闭。",
                "causal_output": "组织必须寻找非常规读取路径。",
                "proposal_trace": "CLAIM-02",
            },
        }
        rows = [
            {
                "Scene id": "PRD-S01",
                "Conflict type": "external",
                "Conflict pressure": "危机倒计时压迫组织继续读取。",
                "Start value": "组织仍相信常规路径可用。",
                "End value": "组织发现读取路径受阻。",
                "Irreversibility": "时间压力无法复位。",
                "Proposal trace": "CLAIM-01",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_scene_coverage(
                canonical_scenes,
                rows,
                "conflict/value table",
                ["Scene id"],
            )

        self.assertIn("missing scene ids", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_integrator_scene_drift(self):
        artifacts = valid_prd_artifacts()
        artifacts["08"] = artifacts["08"].replace(
            "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。",
            "组织已经取得完整情报并结束分析。",
        )

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("event fact drift", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_trunk_scene_v2_proofs(self):
        artifacts = valid_prd_artifacts()
        artifacts["03"] = f"""
# Trunk Scenes

## Trunk scene table

| Scene id | Order | Entry state | Roles | Environment | Event | Causal output | Proposal trace |
|---|---|---|---|---|---|---|---|
| PRD-S01 | 1 | 逝者已经死亡但脑活动仍可被维持。 | 研究员与组织值班组承担读取压力。 | 生命维持实验室作为技术入口。 | 组织维持逝者脑活动并启动脑波分析。 | 组织确认常规读取路径仍可尝试。 | {proposal_trace_text()} |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("missing required table headers", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_trunk_scene_content(self):
        artifacts = valid_prd_artifacts()
        artifacts["03"] = artifacts["03"].replace(
            " | Scene content",
            "",
        ).replace(
            " | 研究员在生命维持实验室确认逝者脑活动仍被维持，组织值班组把脑波分析接入读取流程；她看见技术仍能触碰死者记忆，却尚未证明关键记忆可读",
            "",
        )

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("Scene content", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_pre_extraction_causal_setup(self):
        artifacts = valid_prd_artifacts()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("pre-extraction causal setup", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_scene_execution_table(self):
        artifacts = valid_prd_artifacts_with_pre_extraction_setup()
        artifacts["03"] = artifacts["03"].split("## Scene execution table")[0] + skill_verdict_section()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims_with_setup(),
            )

        self.assertIn("Scene execution table", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_story_logic_boundary_table(self):
        artifacts = artifacts_with_story_logic_risk_without_boundaries()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims_with_setup(),
            )

        self.assertIn("Story logic boundary table", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_accepts_story_logic_boundary_table(self):
        validator.validate_formal_prd_artifact_texts(
            artifacts_with_story_logic_plausibility_anchors(),
            "formal run",
            proposal_claims=valid_proposal_claims_with_setup(),
        )

    def test_validate_formal_prd_artifact_texts_requires_story_logic_plausibility_anchors(self):
        artifacts = artifacts_with_story_logic_boundary_table()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims_with_setup(),
            )

        self.assertIn("plausibility", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_accepts_story_logic_plausibility_anchors(self):
        validator.validate_formal_prd_artifact_texts(
            artifacts_with_story_logic_plausibility_anchors(),
            "formal run",
            proposal_claims=valid_proposal_claims_with_setup(),
        )

    def test_validate_formal_prd_artifact_texts_requires_information_flow_coverage(self):
        artifacts = valid_prd_artifacts()
        artifacts["03"] = f"""
# Trunk Scenes

## Trunk scene table

| Scene id | Order | Entry state | Roles | Environment | Event | Causal output | Proposal trace | Scene content | Previous dependency | Next pressure | Indispensability proof |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PRD-S01 | 1 | 逝者已经死亡但脑活动仍可被维持。 | 研究员与组织值班组承担读取压力。 | 生命维持实验室作为技术入口。 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | 组织确认常规读取路径仍可尝试。 | {proposal_trace_text()} | 研究员确认逝者脑活动仍可维持，组织值班组接入脑波分析并等待第一轮输出。 | 指定部分起点要求组织仍试图读取逝者记忆。 | 读取路径受阻后必须寻找非常规办法。 | 没有该场就无法建立死亡后读取压力和技术入口。 |
| PRD-S02 | 2 | 组织继续维持逝者脑活动并读取受阻。 | 研究员与分析组面对失败迹象。 | 脑波分析台作为检测环境。 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆；再次尝试后确认读取路径失败。 | 组织必须寻找非常规读取路径。 | {proposal_trace_text()} | 分析组反复调整刺激和算法，研究员看到外围记忆有响应，但关键记忆始终像封闭房间。 | PRD-S01 已经启动脑波分析但尚未证明路径失败。 | 路径失败后必须转向未成熟数字生命体方案。 | 没有该场就无法证明常规读取方法已经失败。 |
{skill_verdict_section()}"""
        artifacts["04"] = f"""
# Conflict Value

## Conflict and value-shift table

| Scene id | Conflict type | Conflict pressure | Start value | End value | Irreversibility | Proposal trace |
|---|---|---|---|---|---|---|
| PRD-S01 | external | 重大事件倒计时迫使组织执行：组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | 组织仍相信常规读取路径可用。 | 读取路径开始暴露不可靠，逝者记忆无法被直接打开。 | 时间压力无法复位，死亡后维持脑活动的技术路线已经被启动。 | {proposal_trace_text()} |
| PRD-S02 | information | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆；失败迹象不断增加。 | 组织相信分析能推进。 | 组织确认常规读取路线失败。 | 常规读取路线被否定。 | {proposal_trace_text()} |
{skill_verdict_section()}"""
        artifacts["05"] = """
# Information Flow

## Information-flow table

| Scene id | Reader learns | Focal character learns | Other actor information | Misbelief or concealment | Next-scene pressure | HLD information need |
|---|---|---|---|---|---|---|
| PRD-S01 | 读者知道脑活动被维持。 | 研究员知道常规读取仍是第一选择。 | 组织知道倒计时更紧。 | 关键记忆是否可读仍被误判。 | 继续推进脑波分析。 | HLD 需定义脑波分析边界。 |
""" + skill_verdict_section()
        artifacts["08"] = f"""
# PRD Assembly

## PRD Integration Verdict

| Field | Value |
|---|---|
| Source completeness | pass |
| Scene fact preservation | pass |
| No new business content | pass |
| Package readiness | pass |

## Scene Source Map

| Scene id | Order | Event fact | Causal output | Proposal trace | Source artifact |
|---|---|---|---|---|---|
| PRD-S01 | 1 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | 组织确认常规读取路径仍可尝试。 | {proposal_trace_text()} | artifact 03 |
| PRD-S02 | 2 | 组织再次尝试脑波分析并确认读取路径失败。 | 组织必须寻找非常规读取路径。 | {proposal_trace_text()} | artifact 03 |
{skill_verdict_section()}"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("information-flow table missing scene ids", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_hld_expansion_artifact(self):
        artifacts = valid_prd_artifacts()
        del artifacts["07"]

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("missing required artifact texts", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_unknown_proposal_trace(self):
        artifacts = valid_prd_artifacts(proposal_claim_id="CLAIM-99")

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("unknown proposal trace claim", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_claim_fact_drift(self):
        artifacts = valid_prd_artifacts()
        artifacts["01"] = f"""
# Scope

## Specified part scope table

| Scope id | Scope name | Start boundary | End boundary | Excluded material | Independence proof | Proposal trace | Verdict |
|---|---|---|---|---|---|---|---|
| PRD-PART-01 | 完全不同的校园恋爱支线 | 男女主在校园重逢。 | 二人确认恋爱关系。 | 组织读取记忆和数字生命全都排除。 | 这一段与主线无关但可以单独读。 | {proposal_trace_text()} | pass |
"""
        proposal_claims = valid_proposal_claims()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=proposal_claims,
            )

        self.assertIn("must preserve exact proposal claim fact", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_negated_claim_fact_with_same_keywords(self):
        artifacts = valid_prd_artifacts()
        artifacts["01"] = f"""
# Scope

## Specified part scope table

| Scope id | Scope name | Start boundary | End boundary | Excluded material | Independence proof | Proposal trace | Verdict |
|---|---|---|---|---|---|---|---|
| PRD-PART-01 | 记忆读取危机段 | 组织没有在逝者死亡后维持脑活动。 | 组织也没有以脑波分析尝试读取记忆。 | 危机后的长期余波不在本段展开。 | 本段仍声称围绕组织维持脑活动和脑波分析读取记忆形成闭环。 | {proposal_trace_text()} | pass |
{skill_verdict_section()}"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("must preserve exact proposal claim fact", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_conflict_claim_fact_drift(self):
        artifacts = valid_prd_artifacts()
        artifacts["04"] = f"""
# Conflict Value

## Conflict and value-shift table

| Scene id | Conflict type | Conflict pressure | Start value | End value | Irreversibility | Proposal trace |
|---|---|---|---|---|---|---|
| PRD-S01 | relationship | 校园重逢后两人犹豫是否表白。 | 二人仍保持同学距离。 | 二人确认彼此喜欢。 | 告白之后无法回到普通同学状态。 | {proposal_trace_text()} |
"""
        proposal_claims = valid_proposal_claims()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=proposal_claims,
            )

        self.assertIn("must preserve exact proposal claim fact", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_accepts_full_claim_map_fixture(self):
        proposal_claims = valid_proposal_claims_with_setup()

        validator.validate_formal_prd_artifact_texts(
            valid_prd_artifacts_with_pre_extraction_setup(),
            "formal run",
            proposal_claims=proposal_claims,
        )

    def test_validate_formal_prd_artifact_texts_requires_full_claim_map(self):
        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                valid_prd_artifacts(),
                "formal run",
            )

        self.assertIn("requires full proposal claim map", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_claim_constraint_role_drift(self):
        artifacts = valid_prd_artifacts(
            constraint_role="wrong downstream constraint role",
        )

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("constraint role drift", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_placeholder_conflict_fields(self):
        artifacts = valid_prd_artifacts()
        artifacts["04"] = f"""
# Conflict Value

## Conflict and value-shift table

| Scene id | Conflict type | Conflict pressure | Start value | End value | Irreversibility | Proposal trace |
|---|---|---|---|---|---|---|
| PRD-S01 | external | x | x | x | x | {proposal_trace_text()} |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("too short", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_final_package(self):
        artifacts = valid_prd_artifacts()
        del artifacts["final-prd-package"]

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("missing required artifact texts", str(raised.exception))

    def test_validate_final_prd_package_rejects_unknown_section_sources(self):
        artifacts = valid_prd_artifacts()
        artifacts["final-prd-package"] = """
# Final PRD Package

## Final PRD package index

| Section | Source |
|---|---|
| Proposal source and PRD entry proof | unknown |
| Specified part scope | unknown |
| Part goal and acceptance boundary | unknown |
| Linear trunk scene table | unknown |
| Conflict and value-shift table | unknown |
| Information-flow table | unknown |
| HLD information boundary table | unknown |
| PRD freeze boundaries | unknown |
| HLD expansion requirements | unknown |
| Upstream required HLD entities | unknown |
| PRD Integration Verdict | unknown |
| Scene Source Map | unknown |
| PRD risk report and HLD entry verdict | unknown |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("final package source mismatch", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_extra_hld_scene_ids(self):
        artifacts = valid_prd_artifacts()
        artifacts["07"] = """
# HLD Requirements

## HLD expansion requirement list

| Requirement id | Required expansion | Supports scene ids | Information boundary refs | Inherited HLD obligations | Required answer | Boundary | Source |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | 生命维持和脑波分析的技术边界。 | PRD-S01, PRD-S99 | PRD-INFO-01 | HLD 必须把读取窗口绑定到场景事件，不得提前公开关键记忆。 | HLD 需回答为何脑活动可维持但记忆不可直接读取。 | 不能改写 PRD-S01 的读取失败方向。 | scene:PRD-S01 |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("unknown HLD support scene ids", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_upstream_required_hld_entities(self):
        artifacts = valid_prd_artifacts_with_pre_extraction_setup()
        artifacts["07"] = artifacts["07"].split("\n## Upstream required HLD entities\n", 1)[0]
        artifacts["07"] += skill_verdict_section()

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims_with_setup(),
            )

        self.assertIn("Upstream required HLD entities", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_final_package_upstream_entities(self):
        artifacts = valid_prd_artifacts_with_pre_extraction_setup()
        artifacts["final-prd-package"] = artifacts["final-prd-package"].replace(
            "## Upstream required HLD entities",
            "## Removed upstream required HLD entities",
            1,
        )

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims_with_setup(),
            )

        self.assertIn("final-prd-package", str(raised.exception))
        self.assertIn("Upstream required HLD entities", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_freeze_unknown_source_scene(self):
        artifacts = valid_prd_artifacts()
        artifacts["06"] = """
# Freeze Boundary

## Freeze boundary list

| Freeze id | Frozen item | Source | Downstream no-change rule | Reopen condition |
|---|---|---|---|---|
| PRD-FREEZE-01 | PRD-S99 的事件事实和因果输出。 | scene:PRD-S99, claim:CLAIM-01 | HLD 不得把脑波分析改成已经成功读取。 | 如果生命维持技术无法支撑该事件，重开 PRD。 |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("unknown freeze source scene ids", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_hld_unknown_source_scene(self):
        artifacts = valid_prd_artifacts()
        artifacts["07"] = """
# HLD Requirements

## HLD expansion requirement list

| Requirement id | Required expansion | Supports scene ids | Information boundary refs | Inherited HLD obligations | Required answer | Boundary | Source |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | 生命维持和脑波分析的技术边界。 | PRD-S01 | PRD-INFO-01 | HLD 必须把读取窗口绑定到场景事件，不得提前公开关键记忆。 | HLD 需回答为何脑活动可维持但记忆不可直接读取。 | 不能改写 PRD-S01 的读取失败方向。 | scene:PRD-S99 |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("unknown HLD source scene ids", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_free_text_freeze_source(self):
        artifacts = valid_prd_artifacts()
        artifacts["06"] = """
# Freeze Boundary

## Freeze boundary list

| Freeze id | Frozen item | Source | Downstream no-change rule | Reopen condition |
|---|---|---|---|---|
| PRD-FREEZE-01 | PRD-S01 的事件事实和因果输出。 | legacy HLD draft | HLD 不得把脑波分析改成已经成功读取。 | 如果生命维持技术无法支撑该事件，重开 PRD。 |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("missing structured source reference", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_rejects_free_text_hld_source(self):
        artifacts = valid_prd_artifacts()
        artifacts["07"] = """
# HLD Requirements

## HLD expansion requirement list

| Requirement id | Required expansion | Supports scene ids | Information boundary refs | Inherited HLD obligations | Required answer | Boundary | Source |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | 生命维持和脑波分析的技术边界。 | PRD-S01 | PRD-INFO-01 | HLD 必须把读取窗口绑定到场景事件，不得提前公开关键记忆。 | HLD 需回答为何脑活动可维持但记忆不可直接读取。 | 不能改写 PRD-S01 的读取失败方向。 | legacy HLD draft |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("missing structured source reference", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_integration_verdict(self):
        artifacts = valid_prd_artifacts()
        artifacts["08"] = f"""
# PRD Assembly

## Scene Source Map

| Scene id | Order | Event fact | Causal output | Proposal trace | Source artifact |
|---|---|---|---|---|---|
| PRD-S01 | 1 | 组织维持逝者脑活动并启动脑波分析。 | 组织确认常规读取路径仍可尝试。 | {proposal_trace_text()} | artifact 03 |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("missing markdown table heading: PRD Integration Verdict", str(raised.exception))

    def test_validate_formal_prd_artifact_texts_requires_risk_skill_verdict(self):
        artifacts = valid_prd_artifacts()
        artifacts["09"] = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `pass` with source evidence. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `pass` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_pending_human_review` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Human review pending | P2 | Human review blocks HLD entry. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_formal_prd_artifact_texts(
                artifacts,
                "formal run",
                proposal_claims=valid_proposal_claims(),
            )

        self.assertIn("missing markdown table heading: Skill Verdict", str(raised.exception))


class PrdRiskVerdictConsistencyTests(unittest.TestCase):
    def test_rejects_agent_pass_with_p1_risk(self):
        risk_report = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `pass` with source evidence. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `pass` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_pending_human_review` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Missing trunk scene value shift | P1 | Rerun scene conflict skill. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("Agent quality verdict cannot pass", str(raised.exception))

    def test_rejects_risk_report_without_output_heading(self):
        risk_report = """
# PRD Risk Report

| Field | Value |
|---|---|
| Agent quality verdict | `pass` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_pending_human_review` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Watch item | P2 | HLD handles it. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("missing markdown table heading: Output", str(raised.exception))

    def test_rejects_agent_pass_when_core_check_is_not_checked(self):
        risk_report = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `not_checked` |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `pass` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_pending_human_review` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Human review pending | P2 | Human review blocks HLD entry. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("Agent quality verdict cannot pass with non-pass core checks", str(raised.exception))

    def test_rejects_core_check_fail_without_blocking_risk(self):
        risk_report = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `fail` missing causal transition. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `revise_skill_output` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_revision_required` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Trunk causality failed | P2 | Rerun trunk scene designer. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("non-pass core checks require unresolved P0/P1 risks", str(raised.exception))

    def test_rejects_invalid_quality_verdict_tokens(self):
        risk_report = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `pass` with source evidence. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `ship_it` |
| Human review verdict | `maybe` |
| HLD entry verdict | `ready_now` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Human review pending | P2 | Human review blocks HLD entry. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("invalid Agent quality verdict", str(raised.exception))

    def test_rejects_confirmed_human_review_with_pending_hld_entry(self):
        risk_report = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `pass` with source evidence. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `pass` |
| Human review verdict | `confirmed` |
| HLD entry verdict | `blocked_pending_human_review` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Watch item | P2 | HLD handles it. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("HLD entry verdict must be pass_to_hld", str(raised.exception))

    def test_rejects_non_pass_agent_quality_without_blocking_evidence(self):
        risk_report = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `pass` with source evidence. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `revise_skill_output` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_revision_required` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Watch item | P2 | HLD handles it. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("non-pass Agent quality verdict requires blocking evidence", str(raised.exception))

    def test_rejects_human_pending_hld_entry_when_revision_blocker_exists(self):
        risk_report = """
# PRD Risk Report

## Output

| Field | Value |
|---|---|
| Proposal obedience | `pass` with source evidence. |
| Scope integrity | `pass` with source evidence. |
| Trunk causality | `pass` with source evidence. |
| Scene completeness | `pass` with source evidence. |
| Boundary control | `pass` with source evidence. |
| Freeze sufficiency | `pass` with source evidence. |
| HLD handoff | `pass` with source evidence. |
| Agent quality verdict | `revise_skill_output` |
| Human review verdict | `pending` |
| HLD entry verdict | `blocked_pending_human_review` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Missing trunk scene value shift | P1 | Rerun scene conflict skill. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_prd_risk_verdict_consistency(risk_report, "prd risk report")

        self.assertIn("HLD entry verdict must be blocked_revision_required", str(raised.exception))

    def test_convergence_log_must_cover_p1_risk_rows(self):
        risk_report = """
# PRD Risk Report

## Output

        | Field | Value |
        |---|---|
        | Proposal obedience | `pass` with source evidence. |
        | Scope integrity | `pass` with source evidence. |
        | Trunk causality | `fail` with missing value shift. |
        | Scene completeness | `pass` with source evidence. |
        | Boundary control | `pass` with source evidence. |
        | Freeze sufficiency | `pass` with source evidence. |
        | HLD handoff | `fail` until revision. |
        | Agent quality verdict | `revise_skill_output` |
        | Human review verdict | `pending` |
        | HLD entry verdict | `blocked_revision_required` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Missing trunk scene value shift | P1 | Rerun scene conflict skill. |
"""
        manifest = """
# PRD workflow artifact run

## Convergence log

| Stable issue id | Root cause | Fix hypothesis | Regression proof | Attempt count | Versioned refactor trigger |
|---|---|---|---|---|---|
| PRD-OTHER | root cause exists | fix hypothesis exists | regression proof exists | 1 |  |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_convergence_covers_blocking_risks(
                risk_report,
                manifest,
                "formal run",
            )

        self.assertIn("missing convergence row", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
