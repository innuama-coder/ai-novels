import hashlib
import re

import pytest

from scripts import validate_hld_contract as validator
from scripts import validate_prd_contract as prd_validator


def _field_value_table(title, values):
    rows = "\n".join(f"| {field} | {value} |" for field, value in values.items())
    return f"## {title}\n\n| Field | Value |\n|---|---|\n{rows}\n"


def test_contract_requires_release_preflight_rule_coverage():
    contract = validator.load_hld_contract()
    rules = {rule["id"]: rule["rule"] for rule in contract["contract_rules"]}

    assert "HLD-CONTRACT-18" in rules
    assert "release preflight" in rules["HLD-CONTRACT-18"].lower()
    assert "HLD-CONTRACT-18" in contract["rule_coverage"]
    validator.validate_release_preflight_contract(contract)


def _skill_verdict_table(verdict="pass"):
    return _field_value_table("Skill Verdict", {
        "Skill quality verdict": verdict,
        "Source closure": "closed",
        "Inventory coverage": "closed",
        "Boundary obedience": "pass",
        "Downstream readiness": "ready",
        "Blocking issue": "none",
        "Rerun target": "none",
    })


def _minimal_upstream_text():
    return """
PRD-S01 is the minimal upstream source for this test package.

## HLD information boundary table

| Information boundary id | Story anchor scene id | Narrative reveal scene id | Narrative reveal order | Disclosure tier | Information object | Reader access | Known by entity refs | Hidden from entity refs | Reveal predecessor boundary refs | Reveal condition type | Freeze refs | Source | HLD obligation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PRD-INFO-01 | PRD-S01 | PRD-S01 | 1 | operational_intelligence | usable intelligence | concealed | entity:researcher | reader | none | action | freeze:PRD-FREEZE-01 | scene:PRD-S01 | HLD must bind the usable intelligence reveal to the PRD scene. |

## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Roles | upstream fact | researcher | character | scene:PRD-S01 |
| UPF-PRD-S01-02 | Environment | PRD-S01 requires lab. | lab | environment | scene:PRD-S01 |
"""


def _validate_hld_artifact_package(
    contract,
    artifacts,
    previous_reconciliation_text=None,
    normalize_integrator=True,
):
    artifacts = dict(artifacts)
    if normalize_integrator and "11" in artifacts and "## LLD handoff index" not in artifacts["11"]:
        artifacts["11"] = _minimal_integrator_artifact(contract, artifacts)
    upstream_text = _minimal_upstream_text()
    return validator.validate_hld_artifact_package(
        contract,
        artifacts,
        upstream_text=upstream_text,
        prd_boundary_sources={
            "artifact_05": upstream_text,
            "artifact_08": upstream_text,
            "final_prd_package": upstream_text,
        },
        previous_reconciliation_text=previous_reconciliation_text,
    )


def _metadata_table(artifact):
    return _field_value_table("Artifact Metadata", {
        "Artifact id": artifact["id"],
        "Owner skill": artifact["skill"],
        "Run id": "hld-test-run",
        "Upstream package": "test-prd-package",
        "Input artifacts": "test-inputs",
        "Output path": f"artifact-{artifact['id']}.md",
        "Version": "v1",
    })


def _markdown_table(title, columns, row):
    header = "| " + " | ".join(columns) + " |"
    sep = "|" + "|".join("---" for _ in columns) + "|"
    body = "| " + " | ".join(row[column] for column in columns) + " |"
    return f"## {title}\n\n{header}\n{sep}\n{body}\n"


def _markdown_rows_table(title, columns, rows):
    header = "| " + " | ".join(columns) + " |"
    sep = "|" + "|".join("---" for _ in columns) + "|"
    body = "\n".join("| " + " | ".join(row[column] for column in columns) + " |" for row in rows)
    return f"## {title}\n\n{header}\n{sep}\n{body}\n"


def _core_thread_rows_for_contract_tests():
    definitions = [
        ("HLD-08-01", "main", "advance_crisis_resolution", "event:HLD-06-01"),
        ("HLD-08-02", "hidden", "withhold_then_reframe_cause", "information:HLD-07-01"),
        ("HLD-08-03", "emotional", "convert_private_relation_to_cost", "character:HLD-04-01"),
        ("HLD-08-04", "theme", "test_value_through_choice", "event:HLD-06-01"),
        ("HLD-08-05", "institutional", "apply_systemic_pressure", "rule:HLD-03-01"),
        ("HLD-08-06", "identity", "separate_digital_life_from_human_memory", "character:HLD-04-01; information:HLD-07-01"),
    ]
    rows = []
    support_by_id = {}
    for index, (thread_id, thread_type, thread_function, anchor_refs) in enumerate(definitions, start=1):
        support_id = f"HLD-02-{index:02d}"
        source_ref = f"scene:PRD-S{index:02d}"
        support_by_id[support_id] = {"Source": source_ref}
        next_thread_id = definitions[index % len(definitions)][0]
        rows.append({
            "Thread id": thread_id,
            "Thread type": thread_type,
            "Thread function": thread_function,
            "Thread anchor refs": anchor_refs,
            "Required pressure refs": source_ref,
            "Core question": f"Can the {thread_type} line change the final decision?",
            "Node distribution": "HLD-06-01, HLD-07-01",
            "Thread progression": (
                "HLD-06-01: the question becomes operationally urgent "
                "-> HLD-07-01: the question changes the final decision"
            ),
            "Crossover": f"thread:{next_thread_id}; effect=This crossover changes the cost of the final decision.",
            "Closure state": "closed",
            "Closure outcome": "The thread reaches a consequential and traceable final state.",
            "Supports": support_id,
        })
    return rows, support_by_id


def _minimal_artifact_text(artifact, include_core_threads=True):
    heading = artifact["section"]
    columns = artifact["columns"]
    row_id = "HLD-F-01" if artifact["id"] == "11" else f"HLD-{artifact['id']}-01"
    valid_values = {
        "01": {
            "Inventory id": "HLD-01-01",
            "Entity type": "character",
            "Entity name": "researcher",
            "Required HLD owner": "artifact 04",
            "Secondary HLD owners": "none",
            "Upstream evidence": "PRD requires researcher as primary actor.",
            "Source": "scene:PRD-S01",
            "Initial status": "active",
        },
        "02": {
            "Support id": "HLD-02-01",
            "Supports": "scene:PRD-S01",
            "Support type": "explain",
            "Required HLD owner": "artifact 03",
            "Inventory obligations": "none",
            "Required answer": "Explain why direct memory reading fails.",
            "Boundary": "Cannot make brainwave extraction succeed directly.",
            "Source": "scene:PRD-S01",
            "Support status": "ready",
        },
        "03": {
            "Rule id": "HLD-03-01",
            "Rule type": "technology",
            "Design fact": "Closed memory cannot be opened by direct brainwave analysis.",
            "Supports": "HLD-02-01",
            "Boundary": "Direct extraction remains impossible.",
            "Source": "scene:PRD-S01",
            "LLD handoff": "LLD-RULE-01",
            "Amendment request": "none",
        },
        "04": {
            "Character id": "HLD-04-01",
            "Inventory id": "HLD-01-01",
            "Entity type": "character",
            "Entity name": "researcher",
            "Role type": "researcher",
            "Function": "Investigates the closed memory through digital-life interaction.",
            "Relationship/motivation": "Fear of institutional misuse pressures duty.",
            "Relationship targets": "none",
            "Concrete motive evidence": "fear of institutional misuse pressures duty",
            "Information permission": "Can access dialogue outputs but not omniscient truth.",
            "Identity boundary": "human researcher identity remains distinct from senior and digital life",
            "Supports": "HLD-02-02",
            "Source": "scene:PRD-S01",
            "LLD handoff": "LLD-CHAR-01",
            "Amendment request": "none",
        },
        "05": {
            "Environment id": "HLD-05-01",
            "Inventory id": "HLD-01-90",
            "Entity type": "environment",
            "Entity name": "lab",
            "Environment type": "lab",
            "Function": "Enables monitored digital-life interaction.",
            "Spatial relation": "Connects life-support site and digital enclosure.",
            "State change id": "ENV-STATE-05-01",
            "State change dimension": "access",
            "State before": "ACCESS_STANDARD",
            "State after": "ACCESS_EMERGENCY_ONLY",
            "State change": "Access tightens as crisis pressure rises.",
            "Supports": "HLD-02-03",
            "Source": "scene:PRD-S01",
            "LLD handoff": "LLD-ENV-01",
            "Amendment request": "none",
        },
        "06": {
            "Event id": "HLD-06-01",
            "Inventory id": "HLD-01-91",
            "Entity type": "event",
            "Entity name": "memory-lock disclosure",
            "Event type": "trigger",
            "Causal role": "Forces the memory-lock investigation forward.",
            "Visibility": "visible",
            "Cause refs": "scene:PRD-S01",
            "Event action": "Digital-life disclosure reveals the memory lock during monitored dialogue.",
            "Participants": "HLD-04-01",
            "Environment refs": "HLD-05-01",
            "Environment state change refs": "ENV-STATE-05-01",
            "Environment state transitions": "ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY",
            "Environment state realizations": "ENV-STATE-05-01 [access]: emergency authorization narrows laboratory entry.",
            "Consequences": "Researcher obtains usable intelligence without complete cause.",
            "Supports": "HLD-02-04",
            "Source": "scene:PRD-S01",
            "LLD handoff": "LLD-EVENT-01",
            "Amendment request": "none",
        },
        "07": {
            "Info id": "HLD-07-01",
            "Inventory id": "HLD-01-92",
            "Entity type": "information object",
            "Entity name": "usable intelligence",
            "PRD information boundary id": "PRD-INFO-01",
            "Freeze refs": "freeze:PRD-FREEZE-01",
            "Story anchor event ref": "HLD-06-01",
            "Time layer": "digital_interaction",
            "Narrative reveal phase": "REVEAL-01",
            "Disclosure tier": "operational_intelligence",
            "Information object": "usable intelligence",
            "Known by": "HLD-04-01",
            "Hidden from": "reader",
            "Reveal predecessor refs": "none",
            "Reveal event ref": "HLD-06-01",
            "Reveal action": "Digital-life disclosure reveals the memory lock during monitored dialogue.",
            "Reveal condition type": "action",
            "Reveal condition refs": "HLD-06-01",
            "Reveal condition": "Digital-life disclosure reveals the memory lock during monitored dialogue.",
            "Supports": "HLD-02-05",
            "Source": "scene:PRD-S01",
            "LLD handoff": "LLD-INFO-01",
            "Amendment request": "none",
        },
        "08": {
            "Thread id": "HLD-08-01",
            "Thread type": "main",
            "Thread function": "advance_crisis_resolution",
            "Thread anchor refs": "event:HLD-06-01",
            "Required pressure refs": "scene:PRD-S01",
            "Core question": "Can the crisis be resolved without destroying the protected human cause?",
            "Node distribution": "HLD-06-01, HLD-07-01",
            "Thread progression": "HLD-06-01: the crisis becomes operationally urgent -> HLD-07-01: usable intelligence changes the final decision",
            "Crossover": "thread:HLD-08-02; effect=The hidden cause turns the public crisis into a private choice.",
            "Closure state": "closed",
            "Closure outcome": "The crisis is resolved while the complete cause remains protected.",
            "Supports": "HLD-02-06",
            "Source": "scene:PRD-S01",
            "LLD handoff": "LLD-THREAD-01",
            "Amendment request": "none",
        },
        "09": {
            "Style/POV id": "HLD-09-01",
            "Rule type": "POV",
            "Access policy": "limited_focalization",
            "Information refs": "info:HLD-07-01",
            "Thread refs": "thread:HLD-08-01",
            "Reader disclosure mode": "external_inference",
            "Language profile": "none",
            "Design fact": "rule=Filter digital-life agency through observation; scope=Researcher-facing narration; effect=Readers infer interiority from visible signs.",
            "POV permission": "focalizer=Researcher observer; permitted=Report observed dialogue and behavior; evidence=Monitored exchanges and visible actions.",
            "Prohibited expression": "forbidden=State unrestricted digital-life thoughts; target=Digital-life interiority; trigger=When evidence is only dialogue or behavior.",
            "Supports": "HLD-02-07",
            "Source": "scene:PRD-S01",
            "LLD handoff": "LLD-STYLE-01",
            "Amendment request": "none",
        },
        "10": {
            "Initial inventory id": "HLD-01-01",
            "Request id": "HLD-10-01",
            "Entity name": "researcher",
            "Entity type": "character",
            "Required HLD owner": "artifact 04",
            "Requested by artifact": "artifact 04",
            "Decision": "accept",
            "Canonical subject id": "none",
            "Final inventory id": "inventory:INV-01",
            "Reason": "Researcher is required by PRD scene support.",
            "Source": "scene:PRD-S01",
            "Support status": "closed",
        },
        "11": {
            "HLD fact id": "HLD-F-01",
            "Upstream fact id": "UPF-PRD-S01-01",
            "Fact type": "character",
            "Upstream fact atom": "upstream fact",
            "HLD fact atom": "Researcher remains the constrained focal actor.",
            "Source refs": "scene:PRD-S01",
            "Owner artifact": "artifact 04",
            "Final inventory id": "inventory:INV-01",
            "Expansion mode": "explain",
            "Support mechanism": "Explains the technical boundary.",
            "LLD handoff target": "LLD-RULE-01",
            "Preservation status": "bounded_expansion",
        },
    }
    fact_values = {
        column: valid_values.get(artifact["id"], {}).get(column, f"{artifact['id']} {column} fact")
        for column in validator.FACT_ATOM_COLUMNS_BY_HEADING.get(heading, [])
    }
    hld_atom = " ".join(fact_values.values()) or f"{artifact['id']} hld fact"
    row = {}
    for column in columns:
        if column == columns[0]:
            row[column] = valid_values.get(artifact["id"], {}).get(column, row_id)
        elif column in fact_values:
            row[column] = fact_values[column]
        elif column in valid_values.get(artifact["id"], {}):
            row[column] = valid_values[artifact["id"]][column]
        elif column in {"Source", "Source refs"}:
            row[column] = "scene:PRD-S01"
        elif column == "Expansion mode":
            row[column] = "explain"
        elif column == "Preservation status":
            row[column] = "preserved"
        elif column == "Final inventory id":
            row[column] = "inventory:INV-01"
        elif column == "Canonical subject id":
            row[column] = "none"
        elif column == "Owner artifact":
            row[column] = "artifact 03"
        elif column == "HLD fact atom":
            row[column] = hld_atom
        elif column == "Upstream fact atom":
            row[column] = "upstream fact"
        else:
            row[column] = f"{artifact['id']} {column}"
    trace_id = row[columns[0]]
    trace = _markdown_table("HLD Fact Trace", [
        "Fact trace id",
        "Upstream fact id",
        "Upstream fact atom",
        "HLD fact atom",
        "Source refs",
        "Expansion mode",
        "Support mechanism",
        "Preservation status",
    ], {
        "Fact trace id": trace_id,
        "Upstream fact id": {
            "05": "UPF-PRD-S01-02",
            "06": "UPF-PRD-S01-03",
            "07": "UPF-PRD-S01-04",
        }.get(artifact["id"], "UPF-PRD-S01-01"),
        "Upstream fact atom": {
            "05": "PRD-S01 requires lab.",
            "06": "upstream fact",
            "07": "upstream fact",
        }.get(artifact["id"], "upstream fact"),
        "HLD fact atom": row.get("HLD fact atom", hld_atom),
        "Source refs": "scene:PRD-S01",
        "Expansion mode": "explain",
        "Support mechanism": "supports test package",
        "Preservation status": "preserved",
    })
    text = "\n".join([
        _metadata_table(artifact),
        _markdown_table(heading, columns, row),
        trace,
        _skill_verdict_table(),
    ])
    if artifact["id"] == "02":
        support_rows = [
            ("HLD-02-02", "artifact 04", "scene:PRD-S01"),
            ("HLD-02-03", "artifact 05", "scene:PRD-S01"),
            ("HLD-02-04", "artifact 06", "scene:PRD-S01"),
            ("HLD-02-05", "artifact 07", "scene:PRD-S01"),
            ("HLD-02-06", "artifact 08", "scene:PRD-S01"),
            ("HLD-02-07", "artifact 09", "scene:PRD-S01"),
        ]
        if include_core_threads:
            support_rows.extend([
            ("HLD-02-80", "artifact 08", "scene:PRD-S02"),
            ("HLD-02-81", "artifact 08", "scene:PRD-S03"),
            ("HLD-02-82", "artifact 08", "scene:PRD-S04"),
            ("HLD-02-83", "artifact 08", "scene:PRD-S05"),
            ("HLD-02-84", "artifact 08", "scene:PRD-S06"),
            ])
        for support_id, owner, source in support_rows:
            text = _add_support_row(text, support_id, owner=owner, source=source)
    if artifact["id"] == "01":
        text = _add_inventory_row(
            text,
            "HLD-01-90",
            "lab",
            owner="artifact 05",
            entity_type="environment",
            upstream_fact_id="UPF-PRD-S01-02",
        )
        text = _add_inventory_row(
            text,
            "HLD-01-91",
            "memory-lock disclosure",
            owner="artifact 06",
            entity_type="event",
            upstream_fact_id="UPF-PRD-S01-03",
            upstream_fact_atom="upstream fact",
        )
        text = _add_inventory_row(
            text,
            "HLD-01-92",
            "usable intelligence",
            owner="artifact 07",
            entity_type="information object",
            upstream_fact_id="UPF-PRD-S01-04",
            upstream_fact_atom="upstream fact",
        )
    if artifact["id"] == "10":
        text = _add_inventory_reconciliation(
            text,
            "HLD-01-90",
            "lab",
            owner="artifact 05",
            entity_type="environment",
            final_inventory_id="inventory:INV-90",
        )
        text = _add_inventory_reconciliation(
            text,
            "HLD-01-91",
            "memory-lock disclosure",
            owner="artifact 06",
            entity_type="event",
            final_inventory_id="inventory:INV-91",
        )
        text = _add_inventory_reconciliation(
            text,
            "HLD-01-92",
            "usable intelligence",
            owner="artifact 07",
            entity_type="information object",
            final_inventory_id="inventory:INV-92",
        )
    if artifact["id"] == "11":
        text = _add_environment_source_map_row(text)
        text = _add_event_source_map_row(text)
        text = _add_information_source_map_row(text)
    if artifact["id"] == "08" and include_core_threads:
        text = _add_required_thread_rows(text)
    if artifact["id"] == "09":
        text = _add_required_style_rows(text)
    return _bind_style_execution_text(text)


def _minimal_artifact_12_text(artifact):
    verdict_matrix = """## Verdict consistency matrix

| Verdict | Required condition | Actual evidence | Resolved value | Consistency |
|---|---|---|---|---|
| Agent quality verdict | all required checks pass and no unresolved P0/P1 | all required checks pass and no unresolved P0/P1 | pass | pass |
| HLD human review state | confirmed or not_required | not_required | not_required | pass |
| LLD entry verdict | Agent quality pass plus human review confirmed or not_required | pass_to_lld conditions satisfied | pass_to_lld | pass |
"""
    rubric_coverage = """## Artifact rubric coverage

| Artifact | Good delivery evidence | Blocking failure check | Coverage verdict |
|---|---|---|---|
| Artifact 01 | Inventory coverage checked | Required entities have source and owner | pass |
| Artifact 02 | Support matrix coverage checked | Support rows have answer, boundary, and owner | pass |
| Artifact 03 | World rule rubric checked | Rules constrain action without rewriting PRD | pass |
| Artifact 04 | Character system rubric checked | Actors have function, concrete motive pressure, relationship target closure, information permission, and digital-life identity boundary | pass |
| Artifact 05 | Environment system rubric checked | Environments have inventory coverage, spatial relation, state-change dimension, state transition, event state realization, and Source Map trace closure | pass |
| Artifact 06 | Event inventory coverage, causal-chain closure, concrete event action, consequence, visibility, environment integration, and Source Map trace closure checked | Missing event inventory, cause, action, consequence, visibility, environment integration, or Source Map closure blocks | pass |
| Artifact 07 | Information inventory, story anchor, time layer, narrative reveal phase, disclosure tier, knowledge state, reveal predecessor, reveal event, reveal action, condition type, condition refs, and Source Map trace closure checked | Missing information identity, temporal order, reveal action, condition reference, or Source Map closure blocks | pass |
| Artifact 08 | Main, hidden, emotional, theme, institutional, and identity threads have Thread function, Required pressure refs, Thread progression, crossover, and closure outcome checks | Missing a core thread, Thread function, Required pressure, Thread progression, crossover, or closure outcome blocks | pass |
| Artifact 09 | POV, narrative distance, information access, digital-life interiority, dialogue, image system, prohibited expression, and language style have Access policy, Information refs, Thread refs, Reader disclosure mode, Language profile directives, type-specific behavior, execution reference closure, focalizer resolution, structured Design fact, POV permission, Prohibited expression execution fields, and LLD handoff checks | Missing a required style rule, Access policy, Information refs, Thread refs, Reader disclosure mode, Language profile directives, type-specific behavior, vague expression, execution reference closure, focalizer resolution, structured execution fields, or LLD handoff blocks | pass |
| Artifact 10 | Reconciliation subject register, origin binding, canonical merge target, single final inventory id, amendment blocking, and continuity check evidence recorded | Phantom subject, source or owner drift, unresolved merge, multi-id mint, amendment mint, or final-id renumbering blocks | pass |
| Artifact 11 | Fact-level Source Map closure covers artifact 03-09 and every ready LLD handoff index row | Missing or drifted artifact 03-09 Source Map closure or LLD handoff index blocks | pass |
| Artifact 12 | Integrity checker rubric checked | Risks, verdicts, and convergence are routeable | pass |
"""
    reconciliation_closure_checks = """## Reconciliation closure checks

| Initial inventory id | Request id | Decision | Canonical subject id | Final inventory id | Origin artifact | Origin source refs | Origin fact trace id | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| HLD-01-01 | HLD-10-01 | accept | none | inventory:INV-01 | artifact 04 | scene:PRD-S01 | HLD-01-01 | origin=inventory; identity=researcher; final=inventory:INV-01 | pass |
| HLD-01-90 | HLD-10-90 | accept | none | inventory:INV-90 | artifact 05 | scene:PRD-S01 | HLD-01-90 | origin=inventory; identity=lab; final=inventory:INV-90 | pass |
| HLD-01-91 | HLD-10-91 | accept | none | inventory:INV-91 | artifact 06 | scene:PRD-S01 | HLD-01-91 | origin=inventory; identity=event; final=inventory:INV-91 | pass |
| HLD-01-92 | HLD-10-92 | accept | none | inventory:INV-92 | artifact 07 | scene:PRD-S01 | HLD-01-92 | origin=inventory; identity=information; final=inventory:INV-92 | pass |
"""
    environment_closure_checks = """## Environment closure checks

| Environment id | Inventory id | State change id | State change dimension | State before | State after | Event ids | Event state transition refs | Event state realization refs | Source Map HLD fact id | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-05-01 | HLD-01-90 | ENV-STATE-05-01 | access | ACCESS_STANDARD | ACCESS_EMERGENCY_ONLY | HLD-06-01 | HLD-06-01:ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY | HLD-06-01:ENV-STATE-05-01 | HLD-F-05 | function=monitored interaction; spatial=life-support to enclosure; transition=access restriction; before=ACCESS_STANDARD; after=ACCESS_EMERGENCY_ONLY; realization=emergency authorization narrows laboratory entry | pass |
"""
    event_closure_checks = """## Event closure checks

| Event id | Inventory id | Cause refs | Event action | Causal role | Consequences | Environment state change refs | Event fact id | Event closure evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| HLD-06-01 | HLD-01-91 | scene:PRD-S01 | Digital-life disclosure reveals the memory lock during monitored dialogue. | Forces the memory-lock investigation forward. | Researcher obtains usable intelligence without complete cause. | ENV-STATE-05-01 | HLD-F-06 | cause=PRD trigger; action=digital-life disclosure; role=forces investigation; consequence=usable intelligence; environment=access restriction realized | pass |
"""
    information_closure_checks = """## Information closure checks

| Info id | Inventory id | PRD information boundary id | Freeze refs | Story anchor event ref | Time layer | Narrative reveal phase | Disclosure tier | Known by | Hidden from | Reveal predecessor refs | Reveal event ref | Reveal action | Reveal condition type | Reveal condition refs | Reveal condition | Information fact id | Information closure evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-07-01 | HLD-01-92 | PRD-INFO-01 | freeze:PRD-FREEZE-01 | HLD-06-01 | digital_interaction | REVEAL-01 | operational_intelligence | HLD-04-01 | reader | none | HLD-06-01 | Digital-life disclosure reveals the memory lock during monitored dialogue. | action | HLD-06-01 | Digital-life disclosure reveals the memory lock during monitored dialogue. | HLD-F-07 | boundary=PRD-INFO-01; freeze=PRD-FREEZE-01; anchor=event disclosure; layer=digital interaction; phase=one; tier=operational intelligence; knowledge=researcher only; predecessor=none; reveal=event dialogue; action=memory lock disclosure; condition_type=action; condition_ref=event disclosure; condition=event action opens memory lock | pass |
"""
    thread_closure_checks = """## Thread closure checks

| Thread id | Thread type | Thread function | Thread anchor refs | Required pressure refs | Thread progression | Crossover | Closure outcome | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| HLD-08-01 | main | advance_crisis_resolution | event:HLD-06-01 | scene:PRD-S01 | HLD-06-01: the crisis becomes operationally urgent -> HLD-07-01: usable intelligence changes the final decision | thread:HLD-08-02; effect=The hidden cause turns the public crisis into a private choice. | The crisis is resolved while the complete cause remains protected. | function=crisis resolution; anchors=event; pressure=PRD-S01; progression=urgency to decision; crossover=hidden cause; closure=crisis resolution | pass |
| HLD-08-02 | hidden | withhold_then_reframe_cause | information:HLD-07-01 | scene:PRD-S02 | HLD-06-01: the lock appears as an operational barrier -> HLD-07-01: the hidden cause reframes the barrier as private protection | thread:HLD-08-03; effect=Emotional recognition makes the hidden cause costly to expose. | The protected cause remains hidden from formal institutional reporting. | function=withhold cause; anchors=information; pressure=PRD-S02; progression=barrier to protection; crossover=emotional recognition; closure=protected cause | pass |
| HLD-08-03 | emotional | convert_private_relation_to_cost | character:HLD-04-01 | scene:PRD-S03 | HLD-06-01: the researcher treats disclosure as professional duty -> HLD-07-01: recognition makes the decision personally costly | thread:HLD-08-04; effect=The theme turns private grief into an enduring moral cost. | The researcher accepts lasting grief without claiming emotional absolution. | function=relation cost; anchors=character; pressure=PRD-S03; progression=duty to grief; crossover=theme; closure=lasting grief | pass |
| HLD-08-04 | theme | test_value_through_choice | event:HLD-06-01 | scene:PRD-S04 | HLD-06-01: extraction promises a clean solution -> HLD-07-01: protection requires a consequential incomplete disclosure | thread:HLD-08-05; effect=Institutional pressure tests whether protection can resist useful truth. | The world remains safe while protection leaves an unresolved ethical burden. | function=value choice; anchors=event; pressure=PRD-S04; progression=solution to cost; crossover=institutional pressure; closure=ethical burden | pass |
| HLD-08-05 | institutional | apply_systemic_pressure | rule:HLD-03-01 | scene:PRD-S05 | HLD-06-01: institutional urgency demands usable intelligence -> HLD-07-01: the rule boundary limits what the institution may know | thread:HLD-08-06; effect=Identity boundaries prevent the institution from treating new life as a tool. | Institutional pressure persists but cannot erase the protected private cause. | function=systemic pressure; anchors=rule; pressure=PRD-S05; progression=urgency to limit; crossover=identity boundary; closure=persistent pressure | pass |
| HLD-08-06 | identity | separate_digital_life_from_human_memory | character:HLD-04-01; information:HLD-07-01 | scene:PRD-S06 | HLD-06-01: memory fragments appear to speak for the senior -> HLD-07-01: disclosure establishes a distinct digital subject | thread:HLD-08-01; effect=Its autonomous ending resolves the crisis without restoring the dead senior. | The digital life acts as a distinct subject and chooses its own ending. | function=identity separation; anchors=character and information; pressure=PRD-S06; progression=memory to subject; crossover=autonomous ending; closure=distinct subject | pass |
"""
    style_closure_checks = """## Style/POV closure checks

| Style/POV id | Rule type | Access policy | Information refs | Thread refs | Reader disclosure mode | Language profile | Design fact | POV permission | Prohibited expression | LLD handoff | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-09-01 | POV | limited_focalization | info:HLD-07-01 | thread:HLD-08-01 | external_inference | none | rule=Filter digital-life agency through observation; scope=Researcher-facing narration; effect=Readers infer interiority from visible signs. | focalizer=Researcher observer; permitted=Report observed dialogue and behavior; evidence=Monitored exchanges and visible actions. | forbidden=State unrestricted digital-life thoughts; target=Digital-life interiority; trigger=When evidence is only dialogue or behavior. | LLD-STYLE-01 | policy=limited focalization; information=HLD-07-01; thread=HLD-08-01; reader=external inference; language=none; design=observation filter; permission=observed dialogue; prohibition=no interior entry; handoff=LLD-STYLE-01 | pass |
| HLD-09-02 | narrative distance | controlled_distance | info:HLD-07-01 | thread:HLD-08-02 | external_inference | none | rule=Keep uncertainty within observable limits; scope=Researcher-facing narration; effect=Inference never becomes private certainty. | focalizer=Researcher observer; permitted=Maintain controlled observational distance; evidence=Observed reactions and verified records. | forbidden=Convert inference into narrated certainty; target=Unverified motives; trigger=When direct evidence is unavailable. | LLD-STYLE-02 | policy=controlled distance; information=HLD-07-01; thread=HLD-08-02; reader=external inference; language=none; design=bounded uncertainty; permission=controlled observation; prohibition=no narrated certainty; handoff=LLD-STYLE-02 | pass |
| HLD-09-03 | information access | reveal_gated | info:HLD-07-01 | thread:HLD-08-01 | reveal_at_information_gate | none | rule=Release facts only at approved gates; scope=Reader information access; effect=Reader knowledge follows the reveal event. | focalizer=Researcher observer; permitted=Narrate information after its reveal event; evidence=Approved reveal action and record. | forbidden=Reveal protected cause early; target=Pre-gate reader knowledge; trigger=Before the bound event completes. | LLD-STYLE-03 | policy=reveal gated; information=HLD-07-01; thread=HLD-08-01; reader=reveal at gate; language=none; design=reveal gate; permission=approved event; prohibition=no early cause; handoff=LLD-STYLE-03 | pass |
| HLD-09-04 | digital-life interiority | no_direct_interior | info:HLD-07-01 | thread:HLD-08-06 | external_inference | none | rule=Render agency through mediated signs; scope=Digital-life representation; effect=Its subjectivity remains inferred not entered. | focalizer=Researcher observer; permitted=Show dialogue behavior and system responses; evidence=Monitored signs of agency. | forbidden=Enter unrestricted digital-life thoughts; target=Digital-life interiority; trigger=Without external evidence. | LLD-STYLE-04 | policy=no direct interior; information=HLD-07-01; thread=HLD-08-06; reader=external inference; language=none; design=mediated agency; permission=visible responses; prohibition=no unrestricted thoughts; handoff=LLD-STYLE-04 | pass |
| HLD-09-05 | dialogue | mediated_dialogue | info:HLD-07-01 | thread:HLD-08-02 | external_inference | none | rule=Treat dialogue as partial evidence; scope=Digital-life exchanges; effect=Hidden motives remain unresolved. | focalizer=Researcher observer; permitted=Present monitored exchanges with interruption; evidence=Recorded dialogue and visible reactions. | forbidden=Certify concealed motives through dialogue; target=Hidden causal information; trigger=When records remain incomplete. | LLD-STYLE-05 | policy=mediated dialogue; information=HLD-07-01; thread=HLD-08-02; reader=external inference; language=none; design=partial evidence; permission=monitored exchange; prohibition=no settled hidden cause; handoff=LLD-STYLE-05 | pass |
| HLD-09-06 | image system | bounded_image_system | info:HLD-07-01 | thread:HLD-08-04 | external_inference | none | rule=Use images only as bounded evidence; scope=Recurring sensory images; effect=Images clarify active disclosure limits. | focalizer=Researcher observer; permitted=Repeat images tied to observed containment; evidence=Active disclosure boundary and scene evidence. | forbidden=Use images as omniscient explanation; target=Hidden causal information; trigger=When no observed evidence supports them. | LLD-STYLE-06 | policy=bounded image system; information=HLD-07-01; thread=HLD-08-04; reader=external inference; language=none; design=bounded imagery; permission=observed containment; prohibition=no omniscient explanation; handoff=LLD-STYLE-06 | pass |
| HLD-09-07 | prohibited expression | hard_prohibition | info:HLD-07-01 | thread:HLD-08-06 | external_inference | none | rule=Keep memory source separate from subject; scope=Digital-life identity language; effect=Identity claims remain externally evidenced. | focalizer=Researcher observer; permitted=State identity only through external evidence; evidence=Observed action and verified record. | forbidden=Call digital life the resurrected senior; target=Digital-life identity; trigger=Without independently verified evidence. | LLD-STYLE-07 | policy=hard prohibition; information=HLD-07-01; thread=HLD-08-06; reader=external inference; language=none; design=identity distinction; permission=external identity claims; prohibition=no resurrection claim; handoff=LLD-STYLE-07 | pass |
| HLD-09-08 | language style | controlled_register | info:HLD-07-01 | thread:HLD-08-04 | external_inference | register=mode:restrained formal narration, limit:avoid evaluative abstraction; syntax=sentence:balanced clauses with controlled breaks, variation:shorten under immediate pressure; diction=prefer:precise institutional and sensory terms, avoid:ungrounded technical jargon; rhythm=pace:measured sentences with pressure pauses, shift:accelerate only during verified action | rule=Keep pressure concrete and emotionally restrained; scope=Narrative language choices; effect=Style preserves observed evidence and human cost. | focalizer=Researcher observer; permitted=Use restrained wording tied to sensory evidence; evidence=Observed action and verified records. | forbidden=Use lyric omniscience or melodramatic absolutes; target=Narrative language choices; trigger=When evidence remains partial or hidden. | LLD-STYLE-08 | policy=controlled register; information=HLD-07-01; thread=HLD-08-04; reader=external inference; language=structured directives; design=restrained pressure; permission=sensory evidence; prohibition=no lyric omniscience; handoff=LLD-STYLE-08 | pass |
"""
    return _bind_style_execution_text("\n".join([
        _metadata_table(artifact),
        _markdown_table("HLD Fact Trace", [
            "Fact trace id",
            "Upstream fact id",
            "Upstream fact atom",
            "HLD fact atom",
            "Source refs",
            "Expansion mode",
            "Support mechanism",
            "Preservation status",
        ], {
            "Fact trace id": "none",
            "Upstream fact id": "none",
            "Upstream fact atom": "none",
            "HLD fact atom": "none",
            "Source refs": "scene:PRD-S01",
            "Expansion mode": "explain",
            "Support mechanism": "none",
            "Preservation status": "checked",
        }),
        _field_value_table("Output", {
            "Agent quality verdict": "pass",
            "HLD human review state": "not_required",
            "LLD entry verdict": "pass_to_lld",
        }),
        _markdown_table("Risks", [
            "Risk",
            "Severity",
            "Source refs",
            "Owner artifact",
            "Rerun target",
            "Handling",
            "Blocking verdict effect",
        ], {
            "Risk": "none",
            "Severity": "P3",
            "Source refs": "none",
            "Owner artifact": "none",
            "Rerun target": "none",
            "Handling": "none",
            "Blocking verdict effect": "none",
        }),
        verdict_matrix,
        rubric_coverage,
        reconciliation_closure_checks,
        environment_closure_checks,
        event_closure_checks,
        information_closure_checks,
        thread_closure_checks,
        style_closure_checks,
        _markdown_table("HLD Convergence Log", [
            "Stable issue id",
            "Severity",
            "Root cause",
            "Fix hypothesis",
            "Regression proof",
            "Attempt count",
            "Rerun target",
            "Status",
        ], {
            "Stable issue id": "none",
            "Severity": "P3",
            "Root cause": "none",
            "Fix hypothesis": "none",
            "Regression proof": "none",
            "Attempt count": "0",
            "Rerun target": "none",
            "Status": "closed",
        }),
        _skill_verdict_table(),
    ]))


def _minimal_hld_artifacts(contract, complete_threads=True):
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact, include_core_threads=complete_threads)
        )
    artifacts = _bind_style_execution_refs(artifacts)
    artifacts["11"] = _minimal_integrator_artifact(contract, artifacts)
    return artifacts


def _minimal_integrator_artifact(contract, artifacts):
    artifact_11 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "11")
    source_map_rows = []
    handoff_rows = []
    trace_rows = []
    fact_types = {
        "03": "rule",
        "04": "character",
        "05": "environment",
        "06": "event",
        "07": "information object",
        "08": "thread",
        "09": "style/POV",
    }
    final_inventory_ids = {
        "04": "inventory:INV-01",
        "05": "inventory:INV-90",
        "06": "inventory:INV-91",
        "07": "inventory:INV-92",
    }
    source_map_ids = {
        "03": "HLD-F-03",
        "04": "HLD-F-01",
        "05": "HLD-F-05",
        "06": "HLD-F-06",
        "07": "HLD-F-07",
    }
    for artifact_id, (heading, id_column) in validator.SOURCE_MAP_DESIGN_ARTIFACTS.items():
        business_rows = validator.parse_rows(artifacts[artifact_id], heading)
        trace_by_id = {
            row["Fact trace id"]: row
            for row in validator.parse_rows(artifacts[artifact_id], "HLD Fact Trace")
        }
        for index, business_row in enumerate(business_rows, start=1):
            trace = trace_by_id[business_row[id_column]]
            hld_fact_id = source_map_ids.get(artifact_id, f"HLD-F-{artifact_id}-{index:02d}")
            if index > 1:
                hld_fact_id = f"HLD-F-{artifact_id}-{index:02d}"
            source_map_row = {
                "HLD fact id": hld_fact_id,
                "Upstream fact id": trace["Upstream fact id"],
                "Fact type": fact_types[artifact_id],
                "Upstream fact atom": trace["Upstream fact atom"],
                "HLD fact atom": trace["HLD fact atom"],
                "Source refs": trace["Source refs"],
                "Owner artifact": f"artifact {artifact_id}",
                "Final inventory id": final_inventory_ids.get(artifact_id, "none"),
                "Expansion mode": trace["Expansion mode"],
                "Support mechanism": trace["Support mechanism"],
                "LLD handoff target": business_row["LLD handoff"],
                "Preservation status": trace["Preservation status"],
            }
            source_map_rows.append(source_map_row)
            trace_rows.append({
                "Fact trace id": hld_fact_id,
                "Upstream fact id": trace["Upstream fact id"],
                "Upstream fact atom": trace["Upstream fact atom"],
                "HLD fact atom": trace["HLD fact atom"],
                "Source refs": trace["Source refs"],
                "Expansion mode": trace["Expansion mode"],
                "Support mechanism": trace["Support mechanism"],
                "Preservation status": trace["Preservation status"],
            })
            handoff_rows.append({
                "LLD handoff target": business_row["LLD handoff"],
                "HLD fact id": hld_fact_id,
                "Owner artifact": f"artifact {artifact_id}",
                "Final inventory id": final_inventory_ids.get(artifact_id, "none"),
                "Upstream fact id": trace["Upstream fact id"],
                "Upstream fact atom": trace["Upstream fact atom"],
                "HLD fact atom": trace["HLD fact atom"],
                "Source refs": trace["Source refs"],
                "Handoff status": "ready",
            })
    return "\n".join([
        _metadata_table(artifact_11),
        _markdown_rows_table("HLD Source Map", artifact_11["columns"], source_map_rows),
        _markdown_rows_table("LLD handoff index", validator.LLD_HANDOFF_INDEX_COLUMNS, handoff_rows),
        _markdown_rows_table("HLD Fact Trace", [
            "Fact trace id",
            "Upstream fact id",
            "Upstream fact atom",
            "HLD fact atom",
            "Source refs",
            "Expansion mode",
            "Support mechanism",
            "Preservation status",
        ], trace_rows),
        _skill_verdict_table(),
    ])


def _bind_style_execution_refs(artifacts):
    return {
        artifact_id: _bind_style_execution_text(artifact_text)
        for artifact_id, artifact_text in artifacts.items()
    }


def _bind_style_execution_text(artifact_text):
    artifact_text = re.sub(r"scope=[^;|]+(?=; effect=)", "scope=info:HLD-07-01", artifact_text)
    artifact_text = re.sub(r"focalizer=[^;|]+(?=; permitted=)", "focalizer=researcher", artifact_text)
    artifact_text = re.sub(
        r"evidence=[^;|]+(?=\s+forbidden=|\s*\|)",
        "evidence=info:HLD-07-01",
        artifact_text,
    )
    artifact_text = re.sub(r"target=[^;|]+(?=; trigger=)", "target=thread:HLD-08-01", artifact_text)
    artifact_text = re.sub(
        r"trigger=[^|]+?(?=\s+LLD-[A-Z0-9-]+|\s*\|)",
        "trigger=external_inference",
        artifact_text,
    )
    artifact_text = re.sub(
        r"(\| HLD-09-03 \|[^\n]*?trigger=)external_inference",
        r"\1reveal_at_information_gate",
        artifact_text,
    )
    for style_id, thread_ref in {
        "HLD-09-02": "thread:HLD-08-02",
        "HLD-09-04": "thread:HLD-08-06",
        "HLD-09-05": "thread:HLD-08-02",
        "HLD-09-06": "thread:HLD-08-04",
        "HLD-09-07": "thread:HLD-08-06",
        "HLD-09-08": "thread:HLD-08-04",
    }.items():
        artifact_text = re.sub(
            rf"(\| {style_id} \|[^\n]*?target=)thread:HLD-08-01",
            rf"\1{thread_ref}",
            artifact_text,
        )
    return artifact_text


def _add_support_row(
    artifact_02_text,
    support_id,
    owner="artifact 04",
    inventory_obligations="none",
    source="scene:PRD-S01",
):
    support_row = (
        f"| {support_id} | {source} | explain | {owner} | {inventory_obligations} | "
        "Explain the additional required HLD answer. | Cannot leave the support unimplemented. | "
        f"{source} | ready |"
    )
    trace_row = (
        f"| {support_id} | UPF-PRD-S01-01 | PRD-S01 requires an additional support answer. | "
        f"{source} explain {owner} {inventory_obligations} "
        f"Explain the additional required HLD answer. Cannot leave the support unimplemented. ready | {source} | explain | "
        "creates required design support | preserved |"
    )
    text = artifact_02_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{support_row}\n\n## HLD Fact Trace\n",
    )
    return text.replace(
        "\n## Skill Verdict\n",
        f"\n{trace_row}\n\n## Skill Verdict\n",
    )


def _add_thread_row(
    artifact_text,
    thread_id,
    thread_type,
    thread_function,
    thread_anchor_refs,
    pressure_ref,
    core_question,
    thread_progression,
    crossover,
    closure_outcome,
    support_id,
):
    row = (
        f"| {thread_id} | {thread_type} | {thread_function} | {thread_anchor_refs} | {pressure_ref} | {core_question} | HLD-06-01, HLD-07-01 | {thread_progression} | "
        f"{crossover} | closed | {closure_outcome} | {support_id} | {pressure_ref} | "
        f"LLD-THREAD-{thread_id.removeprefix('HLD-08-')} | none |"
    )
    trace = (
        f"| {thread_id} | UPF-PRD-S01-01 | upstream fact | {thread_function} {thread_anchor_refs} {pressure_ref} {core_question} HLD-06-01, HLD-07-01 {thread_progression} "
        f"{crossover} closed {closure_outcome} | {pressure_ref} | explain | "
        "maps source-backed thread progression | preserved |"
    )
    return artifact_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{trace}\n\n## Skill Verdict\n",
    )


def _add_style_row(
    artifact_text,
    style_id,
    rule_type,
    access_policy,
    information_refs,
    thread_refs,
    reader_disclosure_mode,
    language_profile,
    design_fact,
    pov_permission,
    prohibited_expression,
):
    row = (
        f"| {style_id} | {rule_type} | {access_policy} | {information_refs} | {thread_refs} | {reader_disclosure_mode} | {language_profile} | {design_fact} | "
        f"{pov_permission} | {prohibited_expression} | HLD-02-07 | scene:PRD-S01 | "
        f"LLD-STYLE-{style_id.removeprefix('HLD-09-')} | none |"
    )
    trace = (
        f"| {style_id} | UPF-PRD-S01-01 | upstream fact | {rule_type} {access_policy} {information_refs} {thread_refs} {reader_disclosure_mode} {language_profile} "
        f"{design_fact} {pov_permission} {prohibited_expression} HLD-02-07 LLD-STYLE-{style_id.removeprefix('HLD-09-')} | "
        "scene:PRD-S01 | permission | maps information boundary to writing constraint | preserved |"
    )
    return artifact_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{trace}\n\n## Skill Verdict\n",
    )


def _add_required_style_rows(artifact_text):
    rows = [
        ("HLD-09-02", "narrative distance", "controlled_distance", "info:HLD-07-01", "thread:HLD-08-02", "external_inference", "none", "rule=Keep uncertainty within observable limits; scope=Researcher-facing narration; effect=Inference never becomes private certainty.", "focalizer=Researcher observer; permitted=Maintain controlled observational distance; evidence=Observed reactions and verified records.", "forbidden=Convert inference into narrated certainty; target=Unverified motives; trigger=When direct evidence is unavailable."),
        ("HLD-09-03", "information access", "reveal_gated", "info:HLD-07-01", "thread:HLD-08-01", "reveal_at_information_gate", "none", "rule=Release facts only at approved gates; scope=Reader information access; effect=Reader knowledge follows the reveal event.", "focalizer=Researcher observer; permitted=Narrate information after its reveal event; evidence=Approved reveal action and record.", "forbidden=Reveal protected cause early; target=Pre-gate reader knowledge; trigger=Before the bound event completes."),
        ("HLD-09-04", "digital-life interiority", "no_direct_interior", "info:HLD-07-01", "thread:HLD-08-06", "external_inference", "none", "rule=Render agency through mediated signs; scope=Digital-life representation; effect=Its subjectivity remains inferred not entered.", "focalizer=Researcher observer; permitted=Show dialogue behavior and system responses; evidence=Monitored signs of agency.", "forbidden=Enter unrestricted digital-life thoughts; target=Digital-life interiority; trigger=Without external evidence."),
        ("HLD-09-05", "dialogue", "mediated_dialogue", "info:HLD-07-01", "thread:HLD-08-02", "external_inference", "none", "rule=Treat dialogue as partial evidence; scope=Digital-life exchanges; effect=Hidden motives remain unresolved.", "focalizer=Researcher observer; permitted=Present monitored exchanges with interruption; evidence=Recorded dialogue and visible reactions.", "forbidden=Certify concealed motives through dialogue; target=Hidden causal information; trigger=When records remain incomplete."),
        ("HLD-09-06", "image system", "bounded_image_system", "info:HLD-07-01", "thread:HLD-08-04", "external_inference", "none", "rule=Use images only as bounded evidence; scope=Recurring sensory images; effect=Images clarify active disclosure limits.", "focalizer=Researcher observer; permitted=Repeat images tied to observed containment; evidence=Active disclosure boundary and scene evidence.", "forbidden=Use images as omniscient explanation; target=Hidden causal information; trigger=When no observed evidence supports them."),
        ("HLD-09-07", "prohibited expression", "hard_prohibition", "info:HLD-07-01", "thread:HLD-08-06", "external_inference", "none", "rule=Keep memory source separate from subject; scope=Digital-life identity language; effect=Identity claims remain externally evidenced.", "focalizer=Researcher observer; permitted=State identity only through external evidence; evidence=Observed action and verified record.", "forbidden=Call digital life the resurrected senior; target=Digital-life identity; trigger=Without independently verified evidence."),
        ("HLD-09-08", "language style", "controlled_register", "info:HLD-07-01", "thread:HLD-08-04", "external_inference", "register=mode:restrained formal narration, limit:avoid evaluative abstraction; syntax=sentence:balanced clauses with controlled breaks, variation:shorten under immediate pressure; diction=prefer:precise institutional and sensory terms, avoid:ungrounded technical jargon; rhythm=pace:measured sentences with pressure pauses, shift:accelerate only during verified action", "rule=Keep pressure concrete and emotionally restrained; scope=Narrative language choices; effect=Style preserves observed evidence and human cost.", "focalizer=Researcher observer; permitted=Use restrained wording tied to sensory evidence; evidence=Observed action and verified records.", "forbidden=Use lyric omniscience or melodramatic absolutes; target=Narrative language choices; trigger=When evidence remains partial or hidden."),
    ]
    for row in rows:
        artifact_text = _add_style_row(artifact_text, *row)
    return artifact_text


def _add_required_thread_rows(artifact_text):
    rows = [
        (
            "HLD-08-02",
            "hidden",
            "withhold_then_reframe_cause",
            "information:HLD-07-01",
            "scene:PRD-S02",
            "What private cause does the memory lock conceal?",
            "HLD-06-01: the lock appears as an operational barrier -> HLD-07-01: the hidden cause reframes the barrier as private protection",
            "thread:HLD-08-03; effect=Emotional recognition makes the hidden cause costly to expose.",
            "The protected cause remains hidden from formal institutional reporting.",
            "HLD-02-80",
        ),
        (
            "HLD-08-03",
            "emotional",
            "convert_private_relation_to_cost",
            "character:HLD-04-01",
            "scene:PRD-S03",
            "Can the researcher distinguish grief from responsibility?",
            "HLD-06-01: the researcher treats disclosure as professional duty -> HLD-07-01: recognition makes the decision personally costly",
            "thread:HLD-08-04; effect=The theme turns private grief into an enduring moral cost.",
            "The researcher accepts lasting grief without claiming emotional absolution.",
            "HLD-02-81",
        ),
        (
            "HLD-08-04",
            "theme",
            "test_value_through_choice",
            "event:HLD-06-01",
            "scene:PRD-S04",
            "What does protection cost when truth can be extracted?",
            "HLD-06-01: extraction promises a clean solution -> HLD-07-01: protection requires a consequential incomplete disclosure",
            "thread:HLD-08-05; effect=Institutional pressure tests whether protection can resist useful truth.",
            "The world remains safe while protection leaves an unresolved ethical burden.",
            "HLD-02-82",
        ),
        (
            "HLD-08-05",
            "institutional",
            "apply_systemic_pressure",
            "rule:HLD-03-01",
            "scene:PRD-S05",
            "Can the organization close the case without owning every truth?",
            "HLD-06-01: institutional urgency demands usable intelligence -> HLD-07-01: the rule boundary limits what the institution may know",
            "thread:HLD-08-06; effect=Identity boundaries prevent the institution from treating new life as a tool.",
            "Institutional pressure persists but cannot erase the protected private cause.",
            "HLD-02-83",
        ),
        (
            "HLD-08-06",
            "identity",
            "separate_digital_life_from_human_memory",
            "character:HLD-04-01; information:HLD-07-01",
            "scene:PRD-S06",
            "Who is the digital life when memory is not a resurrection?",
            "HLD-06-01: memory fragments appear to speak for the senior -> HLD-07-01: disclosure establishes a distinct digital subject",
            "thread:HLD-08-01; effect=Its autonomous ending resolves the crisis without restoring the dead senior.",
            "The digital life acts as a distinct subject and chooses its own ending.",
            "HLD-02-84",
        ),
    ]
    for row in rows:
        artifact_text = _add_thread_row(artifact_text, *row)
    return artifact_text


def _add_inventory_row(
    artifact_01_text,
    inventory_id,
    entity_name,
    owner="artifact 04",
    entity_type="character",
    upstream_fact_id="UPF-PRD-S01-01",
    upstream_fact_atom=None,
):
    fact_atom = upstream_fact_atom or f"PRD-S01 requires {entity_name}."
    inventory_row = (
        f"| {inventory_id} | {entity_type} | {entity_name} | {owner} | none | "
        f"PRD requires {entity_name} as a world entity. | scene:PRD-S01 | active |"
    )
    trace_row = (
        f"| {inventory_id} | {upstream_fact_id} | {fact_atom} | "
        f"{entity_type} {entity_name} {owner} none active PRD requires {entity_name} as a world entity. | "
        "scene:PRD-S01 | explain | tracks required entity | preserved |"
    )
    text = artifact_01_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{inventory_row}\n\n## HLD Fact Trace\n",
    )
    return text.replace(
        "\n## Skill Verdict\n",
        f"\n{trace_row}\n\n## Skill Verdict\n",
    )


def _add_inventory_reconciliation(
    artifact_10_text,
    inventory_id,
    entity_name,
    owner="artifact 04",
    entity_type="character",
    final_inventory_id="inventory:INV-02",
):
    upstream_facts = {
        "HLD-01-90": ("HLD-10-90", "UPF-PRD-S01-02", "PRD-S01 requires lab."),
        "HLD-01-91": ("HLD-10-91", "UPF-PRD-S01-03", "upstream fact"),
        "HLD-01-92": ("HLD-10-92", "UPF-PRD-S01-04", "upstream fact"),
    }
    request_id, upstream_fact_id, upstream_fact_atom = upstream_facts.get(
        inventory_id,
        ("HLD-10-02", "UPF-PRD-S01-01", f"PRD-S01 requires {entity_name}."),
    )
    reconciliation_row = (
        f"| {inventory_id} | {request_id} | {entity_name} | {entity_type} | {owner} | {owner} | "
        f"accept | none | {final_inventory_id} | {entity_name} is required by PRD scene support. | scene:PRD-S01 | closed |"
    )
    trace_row = (
        f"| {inventory_id} | {upstream_fact_id} | {upstream_fact_atom} | "
        f"{entity_name} accept none {final_inventory_id} {entity_name} is required by PRD scene support. | "
        f"scene:PRD-S01 | handoff | finalizes {entity_type} inventory | preserved |"
    )
    return artifact_10_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{reconciliation_row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{trace_row}\n\n## Skill Verdict\n",
    )


def _add_environment_inventory_with_reconciliation(artifacts, inventory_id="HLD-01-02", entity_name="digital enclosure"):
    artifacts["01"] = _add_inventory_row(
        artifacts["01"],
        inventory_id,
        entity_name,
        owner="artifact 05",
        entity_type="environment",
    )
    artifacts["10"] = _add_inventory_reconciliation(
        artifacts["10"],
        inventory_id,
        entity_name,
        owner="artifact 05",
        entity_type="environment",
    )


def _add_environment_design_row(artifact_05_text, inventory_id, entity_name, environment_id="HLD-05-02"):
    environment_row = (
        f"| {environment_id} | {inventory_id} | environment | {entity_name} | enclosure | "
        "Contains the injected-memory dialogue boundary. | Is accessed only through the lab. | "
        "ENV-STATE-05-02 | visibility | VISIBILITY_NORMAL | VISIBILITY_EMERGENCY_ONLY | Visibility narrows as the crisis approaches. | HLD-02-03 | scene:PRD-S01 | LLD-ENV-02 | none |"
    )
    environment_trace = (
        f"| {environment_id} | UPF-PRD-S01-01 | PRD-S01 requires {entity_name}. | "
        f"{inventory_id} environment {entity_name} enclosure Contains the injected-memory dialogue boundary. "
        "Is accessed only through the lab. ENV-STATE-05-02 visibility VISIBILITY_NORMAL VISIBILITY_EMERGENCY_ONLY Visibility narrows as the crisis approaches. HLD-02-03 LLD-ENV-02 | "
        "scene:PRD-S01 | explain | designs digital enclosure | preserved |"
    )
    return artifact_05_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{environment_row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{environment_trace}\n\n## Skill Verdict\n",
    )


def _add_environment_source_map_row(artifact_11_text):
    source_map_row = (
        "| HLD-F-05 | UPF-PRD-S01-02 | environment | PRD-S01 requires lab. | "
        "HLD-01-90 environment lab lab Enables monitored digital-life interaction. "
        "Connects life-support site and digital enclosure. ENV-STATE-05-01 access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. "
        "HLD-02-03 LLD-ENV-01 none | scene:PRD-S01 | artifact 05 | inventory:INV-90 | explain | "
        "designs monitored interaction space | LLD-ENV-01 | bounded_expansion |"
    )
    source_map_trace = (
        "| HLD-F-05 | UPF-PRD-S01-02 | PRD-S01 requires lab. | "
        "HLD-01-90 environment lab lab Enables monitored digital-life interaction. "
        "Connects life-support site and digital enclosure. ENV-STATE-05-01 access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. "
        "HLD-02-03 LLD-ENV-01 none | scene:PRD-S01 | explain | "
        "designs monitored interaction space | bounded_expansion |"
    )
    return artifact_11_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{source_map_row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{source_map_trace}\n\n## Skill Verdict\n",
    )


def _minimal_event_hld_fact_atom():
    values = {
        "Inventory id": "HLD-01-91",
        "Entity type": "event",
        "Entity name": "memory-lock disclosure",
        "Cause refs": "scene:PRD-S01",
        "Event action": "Digital-life disclosure reveals the memory lock during monitored dialogue.",
        "Causal role": "Forces the memory-lock investigation forward.",
        "Visibility": "visible",
        "Participants": "HLD-04-01",
        "Environment refs": "HLD-05-01",
        "Environment state change refs": "ENV-STATE-05-01",
        "Environment state transitions": "ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY",
        "Environment state realizations": "ENV-STATE-05-01 [access]: emergency authorization narrows laboratory entry.",
        "Consequences": "Researcher obtains usable intelligence without complete cause.",
        "Supports": "HLD-02-04",
        "LLD handoff": "LLD-EVENT-01",
        "Amendment request": "none",
    }
    return " ".join(values[column] for column in validator.FACT_ATOM_COLUMNS_BY_HEADING["Event system table"])


def _add_event_source_map_row(artifact_11_text):
    event_atom = _minimal_event_hld_fact_atom()
    source_map_row = (
        "| HLD-F-06 | UPF-PRD-S01-03 | event | upstream fact | "
        f"{event_atom} | scene:PRD-S01 | artifact 06 | inventory:INV-91 | sequence | "
        "designs source-backed event chain | LLD-EVENT-01 | bounded_expansion |"
    )
    source_map_trace = (
        "| HLD-F-06 | UPF-PRD-S01-03 | upstream fact | "
        f"{event_atom} | scene:PRD-S01 | sequence | designs source-backed event chain | bounded_expansion |"
    )
    return artifact_11_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{source_map_row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{source_map_trace}\n\n## Skill Verdict\n",
    )


def _add_information_source_map_row(artifact_11_text):
    information_atom = _minimal_information_hld_fact_atom()
    source_map_row = (
        "| HLD-F-07 | UPF-PRD-S01-04 | information object | upstream fact | "
        f"{information_atom} | scene:PRD-S01 | artifact 07 | inventory:INV-92 | sequence | "
        "designs controlled information disclosure | LLD-INFO-01 | bounded_expansion |"
    )
    source_map_trace = (
        "| HLD-F-07 | UPF-PRD-S01-04 | upstream fact | "
        f"{information_atom} | scene:PRD-S01 | sequence | designs controlled information disclosure | bounded_expansion |"
    )
    return artifact_11_text.replace(
        "\n## HLD Fact Trace\n",
        f"\n{source_map_row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{source_map_trace}\n\n## Skill Verdict\n",
    )


def _minimal_information_hld_fact_atom():
    values = {
        "Inventory id": "HLD-01-92",
        "Entity type": "information object",
        "Entity name": "usable intelligence",
        "PRD information boundary id": "PRD-INFO-01",
        "Freeze refs": "freeze:PRD-FREEZE-01",
        "Story anchor event ref": "HLD-06-01",
        "Time layer": "digital_interaction",
        "Narrative reveal phase": "REVEAL-01",
        "Disclosure tier": "operational_intelligence",
        "Information object": "usable intelligence",
        "Known by": "HLD-04-01",
        "Hidden from": "reader",
        "Reveal predecessor refs": "none",
        "Reveal event ref": "HLD-06-01",
        "Reveal action": "Digital-life disclosure reveals the memory lock during monitored dialogue.",
        "Reveal condition type": "action",
        "Reveal condition refs": "HLD-06-01",
        "Reveal condition": "Digital-life disclosure reveals the memory lock during monitored dialogue.",
        "Supports": "HLD-02-05",
        "LLD handoff": "LLD-INFO-01",
        "Amendment request": "none",
    }
    return " ".join(
        values[column]
        for column in validator.FACT_ATOM_COLUMNS_BY_HEADING["Time and information table"]
    )


def _ensure_character_relationship_targets_column(artifact_04_text, default_value="none"):
    if "Relationship targets" in artifact_04_text:
        return artifact_04_text
    lines = []
    in_character_table = False
    for line in artifact_04_text.splitlines():
        if line == "## Character system table":
            in_character_table = True
            lines.append(line)
            continue
        if in_character_table and line.startswith("## "):
            in_character_table = False
        if in_character_table and line.startswith("| Character id |"):
            line = line.replace(
                "Relationship/motivation | Concrete motive evidence",
                "Relationship/motivation | Relationship targets | Concrete motive evidence",
            )
        elif in_character_table and line.startswith("| HLD-04-"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            cells.insert(7, default_value)
            line = "| " + " | ".join(cells) + " |"
        lines.append(line)
    return "\n".join(lines)


def test_required_hld_skills_exist():
    contract = validator.load_hld_contract()
    validator.validate_required_skill_files(contract)


def test_every_artifact_has_minimum_schema():
    contract = validator.load_hld_contract()
    validator.validate_artifact_schemas(contract)
    validator.validate_skill_contract_text(contract)


def test_artifact_04_schema_requires_inventory_identity_columns():
    contract = validator.load_hld_contract()
    artifact_04 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "04")
    for column in ["Inventory id", "Entity type", "Entity name", "Relationship targets", "Concrete motive evidence", "Identity boundary"]:
        assert column in artifact_04["columns"]


def test_artifact_05_schema_requires_inventory_identity_columns():
    contract = validator.load_hld_contract()
    artifact_05 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "05")
    for column in ["Inventory id", "Entity type", "Entity name"]:
        assert column in artifact_05["columns"]


def test_artifact_06_schema_requires_environment_integration_columns():
    contract = validator.load_hld_contract()
    artifact_06 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "06")
    for column in ["Environment refs", "Environment state change refs"]:
        assert column in artifact_06["columns"]


def test_artifact_05_schema_requires_state_change_identity():
    contract = validator.load_hld_contract()
    artifact_05 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "05")
    assert "State change id" in artifact_05["columns"]
    assert "State change dimension" in artifact_05["columns"]
    assert "State before" in artifact_05["columns"]
    assert "State after" in artifact_05["columns"]


def test_artifact_06_schema_requires_environment_state_realization():
    contract = validator.load_hld_contract()
    artifact_06 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "06")
    assert "Environment state realizations" in artifact_06["columns"]
    assert "Environment state transitions" in artifact_06["columns"]


def test_artifact_06_schema_requires_inventory_and_causal_chain_fields():
    contract = validator.load_hld_contract()
    artifact_06 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "06")
    for column in ["Inventory id", "Entity type", "Entity name", "Cause refs", "Event action"]:
        assert column in artifact_06["columns"]


def test_artifact_12_schema_requires_event_closure_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    assert "Event closure checks" in artifact_12["sections"]
    for column in ["Cause refs", "Event action", "Event fact id", "Event closure evidence"]:
        assert column in artifact_12["columns"]


def test_artifact_07_schema_requires_inventory_and_reveal_fields():
    contract = validator.load_hld_contract()
    artifact_07 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "07")
    for column in [
        "Inventory id",
        "Entity type",
        "Entity name",
        "Story anchor event ref",
        "Narrative reveal phase",
        "Reveal predecessor refs",
        "Disclosure tier",
        "Reveal event ref",
        "Reveal action",
        "Reveal condition type",
        "Reveal condition refs",
    ]:
        assert column in artifact_07["columns"]


def test_artifact_12_schema_requires_information_closure_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    assert "Information closure checks" in artifact_12["sections"]
    for column in [
        "Info id",
        "Story anchor event ref",
        "Narrative reveal phase",
        "Reveal predecessor refs",
        "Reveal event ref",
        "Reveal action",
        "Reveal condition type",
        "Reveal condition refs",
        "Information fact id",
    ]:
        assert column in artifact_12["columns"]


def test_event_type_and_visibility_are_distinct_axes():
    assert not (validator.EVENT_TYPES & validator.EVENT_VISIBILITY)


def test_environment_skill_acceptance_is_locally_evaluable():
    text = validator.read(validator.ROOT / "skills/novel-environment-system-designer/SKILL.md")
    acceptance = text.split("## Acceptance", 1)[1].split("## Skill Verdict", 1)[0]
    assert "not an artifact 05 pass condition" in acceptance
    assert "Source-Map" not in acceptance


def test_integrity_skill_uses_v3_environment_rubric_terms():
    text = validator.read(validator.ROOT / "skills/novel-hld-integrity-checker/SKILL.md")
    for term in ["state-change dimension", "state transition", "event state realization"]:
        assert term in text


def test_character_skill_references_define_good_delivery_standards():
    text = validator.read(validator.ROOT / "skills/novel-character-system-designer/SKILL.md")
    references = text.split("## References", 1)[1].split("## Traceability", 1)[0]
    for term in [
        "Good delivery standards",
        "Blocking anti-patterns",
        "narrative function",
        "human pressure",
        "relationship target closure",
        "information permission",
        "identity boundary",
        "LLD handoff",
        "source-backed",
    ]:
        assert term in references


def test_environment_skill_references_define_good_delivery_standards():
    text = validator.read(validator.ROOT / "skills/novel-environment-system-designer/SKILL.md")
    references = text.split("## References", 1)[1].split("## Traceability", 1)[0]
    for term in [
        "Good delivery standards",
        "Blocking anti-patterns",
        "spatial function",
        "spatial relation",
        "state change",
        "access",
        "evidence",
        "pressure",
        "safety",
        "LLD handoff",
        "source-backed",
    ]:
        assert term in references


def test_event_skill_references_define_good_delivery_standards():
    text = validator.read(validator.ROOT / "skills/novel-event-system-designer/SKILL.md")
    references = text.split("## References", 1)[1].split("## Traceability", 1)[0].casefold()
    for term in [
        "good delivery standards",
        "blocking anti-patterns",
        "causal chain",
        "event action",
        "trigger closure",
        "consequence",
        "visibility",
        "lld handoff",
        "source-backed",
    ]:
        assert term in references


def test_time_information_skill_references_define_good_delivery_standards():
    text = validator.read(validator.ROOT / "skills/novel-time-information-system-designer/SKILL.md")
    references = text.split("## References", 1)[1].split("## Traceability", 1)[0].casefold()
    for term in [
        "good delivery standards",
        "blocking anti-patterns",
        "time layer",
        "disclosure tier",
        "reveal event",
        "knowledge state",
        "lld handoff",
        "source-backed",
    ]:
        assert term in references


def test_environment_skill_output_table_has_aligned_markdown_separator():
    text = validator.read(validator.ROOT / "skills/novel-environment-system-designer/SKILL.md")
    output_artifact = text.split("## Output Artifact", 1)[1].split("## Artifact Metadata", 1)[0]
    table_lines = [line.strip() for line in output_artifact.splitlines() if line.strip().startswith("|")]
    assert len(table_lines) >= 2
    assert len(table_lines[0].strip("|").split("|")) == len(table_lines[1].strip("|").split("|"))


def test_event_skill_output_table_has_aligned_markdown_separator():
    text = validator.read(validator.ROOT / "skills/novel-event-system-designer/SKILL.md")
    output_artifact = text.split("## Output Artifact", 1)[1].split("## Artifact Metadata", 1)[0]
    table_lines = [line.strip() for line in output_artifact.splitlines() if line.strip().startswith("|")]
    assert len(table_lines) >= 2
    assert len(table_lines[0].strip("|").split("|")) == len(table_lines[1].strip("|").split("|"))


def test_integrity_skill_event_closure_template_has_one_aligned_separator():
    text = validator.read(validator.ROOT / "skills/novel-hld-integrity-checker/SKILL.md")
    section = text.split("`## Event closure checks`", 1)[1].split("`## Information closure checks`", 1)[0]
    table_lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    assert len(table_lines) == 2
    assert len(table_lines[0].strip("|").split("|")) == len(table_lines[1].strip("|").split("|"))


def test_environment_skill_event_integration_reference_matches_v3_contract():
    text = validator.read(validator.ROOT / "skills/novel-environment-system-designer/SKILL.md")
    references = text.split("## References", 1)[1].split("## Traceability", 1)[0]
    event_integration_row = next(line for line in references.splitlines() if line.startswith("| Event integration |"))
    assert "transition" in event_integration_row
    assert "realization" in event_integration_row


def test_artifact_dag_is_closed_and_acyclic():
    contract = validator.load_hld_contract()
    validator.validate_artifact_dag(contract)


def test_harness_declares_prd_gate_and_blocked_behavior():
    contract = validator.load_hld_contract()
    validator.validate_prd_gate_terms(contract)


def test_harness_contains_no_business_authority():
    contract = validator.load_hld_contract()
    validator.validate_harness_boundary(contract)


def test_harness_rejects_open_inventory_coverage():
    text = validator.read(validator.HARNESS_SKILL)
    assert "Inventory coverage = open:<reason>" in text


def test_harness_routing_rules_include_current_contract_gates():
    contract = validator.load_hld_contract()
    validator.validate_harness_routing_rules(contract)


def test_contract_declares_source_grammar_and_expansion_modes():
    contract = validator.load_hld_contract()
    validator.validate_source_grammar_and_expansion_modes(contract)


def test_skills_require_artifact_metadata_fact_trace_and_verdict():
    contract = validator.load_hld_contract()
    validator.validate_skill_contract_text(contract)


def test_owner_design_skills_require_consuming_assigned_support_rows():
    required_phrase = "consume every ready artifact 02 support row assigned to this artifact"
    for skill in [
        "novel-world-rule-designer",
        "novel-character-system-designer",
        "novel-environment-system-designer",
        "novel-event-system-designer",
        "novel-time-information-system-designer",
        "novel-thread-system-designer",
        "novel-style-pov-system-designer",
    ]:
        text = validator.read(validator.ROOT / "skills" / skill / "SKILL.md")
        assert required_phrase in text


def test_inventory_builder_requires_secondary_scan_checklist():
    text = validator.read(validator.ROOT / "skills/novel-world-entity-inventory-builder/SKILL.md")
    for term in [
        "Secondary scan checklist",
        "Actor and group pass",
        "Place and interface pass",
        "Event and process pass",
        "Rule and authority pass",
        "Information and memory pass",
        "Time and reveal pass",
        "Thread and POV pass",
        "Amendment pass",
    ]:
        assert term in text


def test_contract_fact_trace_fields_include_upstream_fact_id():
    contract = validator.load_hld_contract()
    assert "Upstream fact id" in contract["fact_trace_fields"]


def test_skills_use_provisional_inventory_before_reconciliation():
    contract = validator.load_hld_contract()
    validator.validate_inventory_id_timing(contract)


def test_source_map_accepts_fact_level_rows():
    validator.validate_hld_source_map_rows("""
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | PRD-S01 says brain activity is maintained but memory is unreadable. | HLD defines a life-support signal boundary that explains why activity persists while closed memory remains inaccessible. | scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | explains technical boundary | LLD-RULE-01 | bounded_expansion |
""")


def test_source_map_accepts_multiple_upstream_fact_ids_from_same_source_ref():
    validator.validate_hld_source_map_rows("""
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | PRD-S01 says direct brainwave reading fails. | HLD preserves failed direct reading as a technical boundary. | scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | explains boundary | LLD-RULE-01 | bounded_expansion |
| HLD-F-02 | UPF-PRD-S01-02 | event | PRD-S01 says the organization maintains brain activity after death. | HLD preserves the life-support maintenance event. | scene:PRD-S01 | artifact 06 | inventory:INV-01 | sequence | sequences event trigger | LLD-EVENT-01 | bounded_expansion |
""")


def test_source_map_rejects_same_upstream_fact_id_rewritten_with_added_source_ref():
    with pytest.raises(ValueError, match="same upstream fact id rewrites upstream fact atom"):
        validator.validate_hld_source_map_rows("""
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | PRD-S01 says direct brainwave reading fails. | HLD preserves failed direct reading. | scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | explains boundary | LLD-RULE-01 | bounded_expansion |
| HLD-F-02 | UPF-PRD-S01-01 | rule | PRD-S01 says direct brainwave reading succeeds after tuning. | HLD rewrites direct reading. | scene:PRD-S01, claim:CLAIM-01 | artifact 03 | inventory:INV-01 | explain | rewrites boundary | LLD-RULE-02 | bounded_expansion |
""")


def test_source_map_rejects_same_source_fact_rewrite():
    with pytest.raises(ValueError, match="same upstream fact id rewrites upstream fact atom"):
        validator.validate_hld_source_map_rows("""
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | PRD-S01 says brain activity is maintained but memory is unreadable. | HLD explains unreadable memory. | scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | explains boundary | LLD-RULE-01 | bounded_expansion |
| HLD-F-02 | UPF-PRD-S01-01 | rule | PRD-S01 says brainwave analysis succeeds immediately. | HLD rewrites the extraction result. | scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | rewrites boundary | LLD-RULE-02 | bounded_expansion |
""")


def test_source_map_rejects_reordered_same_source_fact_rewrite():
    with pytest.raises(ValueError, match="same upstream fact id rewrites upstream fact atom"):
        validator.validate_hld_source_map_rows("""
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | PRD-S01 says brain activity is maintained but memory is unreadable. | HLD explains unreadable memory. | scene:PRD-S01, claim:CLAIM-01 | artifact 03 | inventory:INV-01 | explain | explains boundary | LLD-RULE-01 | bounded_expansion |
| HLD-F-02 | UPF-PRD-S01-01 | rule | PRD-S01 says brainwave analysis succeeds immediately. | HLD rewrites the extraction result. | claim:CLAIM-01, scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | rewrites boundary | LLD-RULE-02 | bounded_expansion |
""")


def test_source_map_rejects_single_source_ref_rewrite_inside_larger_source_set():
    with pytest.raises(ValueError, match="same upstream fact id rewrites upstream fact atom"):
        validator.validate_hld_source_map_rows("""
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | PRD-S01 says direct brainwave reading fails. | HLD preserves failed direct reading. | scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | explains boundary | LLD-RULE-01 | bounded_expansion |
| HLD-F-02 | UPF-PRD-S01-01 | rule | PRD-S01 says direct brainwave reading succeeds after tuning. | HLD rewrites direct reading. | scene:PRD-S01, claim:CLAIM-01 | artifact 03 | inventory:INV-01 | explain | rewrites boundary | LLD-RULE-02 | bounded_expansion |
""")


def test_source_map_rejects_free_text_source_refs():
    with pytest.raises(ValueError, match="invalid source ref"):
        validator.validate_hld_source_map_rows("""
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | PRD-S01 says brain activity is maintained but memory is unreadable. | HLD defines a life-support signal boundary. | PRD scene one | artifact 03 | inventory:INV-01 | explain | explains technical boundary | LLD-RULE-01 | bounded_expansion |
""")


def test_artifact_trace_must_cover_each_business_row():
    with pytest.raises(ValueError, match="missing fact trace coverage"):
        validator.validate_hld_artifact_trace_binding("""
## World rule design table

| Rule id | Rule type | Design fact | Supports | Boundary | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|
| HLD-RULE-01 | technology | Brain activity can be sustained but closed memory cannot be opened directly. | SUP-01 | Cannot make brainwave reading succeed. | scene:PRD-S01 | LLD-RULE-01 | none |
| HLD-RULE-02 | institution | Organization pressure can force an immature digital-life trial. | SUP-02 | Cannot remove ethical conflict. | scene:PRD-S02 | LLD-RULE-02 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-RULE-01 | UPF-PRD-S01-01 | PRD-S01 requires failed direct reading. | Brain activity can be sustained but closed memory cannot be opened directly. | scene:PRD-S01 | explain | explains technical boundary | bounded_expansion |
""", "World rule design table", "Rule id")


def test_artifact_trace_rejects_matching_id_with_different_hld_fact_atom():
    with pytest.raises(ValueError, match="HLD fact atom does not bind"):
        validator.validate_hld_artifact_trace_binding("""
## World rule design table

| Rule id | Rule type | Design fact | Supports | Boundary | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|
| HLD-RULE-01 | technology | Brain activity can be sustained but closed memory cannot be opened directly. | SUP-01 | Cannot make brainwave reading succeed. | scene:PRD-S01 | LLD-RULE-01 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-RULE-01 | UPF-PRD-S01-01 | PRD-S01 requires failed direct reading. | Organization successfully extracts memory directly. | scene:PRD-S01 | explain | explains opposite fact | bounded_expansion |
""", "World rule design table", "Rule id")


def test_artifact_02_trace_binds_dispatch_semantics():
    with pytest.raises(ValueError, match="HLD fact atom does not bind"):
        validator.validate_hld_artifact_trace_binding("""
## PRD support matrix

| Support id | Supports | Support type | Required HLD owner | Inventory obligations | Required answer | Boundary | Source | Support status |
|---|---|---|---|---|---|---|---|---|
| HLD-02-01 | scene:PRD-S01 | explain | artifact 03 | none | Explain why direct memory reading fails. | Cannot make brainwave extraction succeed directly. | scene:PRD-S01 | ready |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-02-01 | UPF-PRD-S01-01 | PRD-S01 requires failed direct reading. | scene:PRD-S01 none Explain why direct memory reading fails. Cannot make brainwave extraction succeed directly. | scene:PRD-S01 | explain | asks required support question | preserved |
""", "PRD support matrix", "Support id")


def test_artifact_03_trace_binds_rule_semantics():
    with pytest.raises(ValueError, match="HLD fact atom does not bind"):
        validator.validate_hld_artifact_trace_binding("""
## World rule design table

| Rule id | Rule type | Design fact | Supports | Boundary | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|
| HLD-03-01 | technology | Closed memory cannot be opened by direct brainwave analysis. | HLD-02-01 | Direct extraction remains impossible. | scene:PRD-S01 | LLD-RULE-01 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-03-01 | UPF-PRD-S01-01 | PRD-S01 requires failed direct reading. | Closed memory cannot be opened by direct brainwave analysis. | scene:PRD-S01 | explain | explains technical boundary | bounded_expansion |
""", "World rule design table", "Rule id")


def test_artifact_04_trace_binds_character_semantics():
    with pytest.raises(ValueError, match="HLD fact atom does not bind"):
        validator.validate_hld_artifact_trace_binding("""
## Character system table

| Character id | Inventory id | Entity type | Entity name | Role type | Function | Relationship/motivation | Relationship targets | Concrete motive evidence | Information permission | Identity boundary | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-04-01 | HLD-01-01 | character | researcher | researcher | Investigates the closed memory through digital-life interaction. | Personal attachment conflicts with institutional duty. | none | attachment to the senior conflicts with institutional duty | Can access dialogue outputs but not omniscient truth. | human researcher identity remains distinct from senior and digital life | HLD-02-01 | scene:PRD-S01 | LLD-CHAR-01 | HLD-AMEND-01 |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-04-01 | UPF-PRD-S01-01 | PRD-S01 requires researcher. | Investigates the closed memory through digital-life interaction. Personal attachment conflicts with institutional duty. Can access dialogue outputs but not omniscient truth. | scene:PRD-S01 | permission | defines character pressure | bounded_expansion |
""", "Character system table", "Character id")


def test_artifact_trace_rejects_duplicate_fact_trace_id():
    with pytest.raises(ValueError, match="duplicate fact trace id"):
        validator.validate_hld_artifact_trace_binding("""
## Initial world entity inventory

| Inventory id | Entity type | Entity name | Required HLD owner | Secondary HLD owners | Upstream evidence | Source | Initial status |
|---|---|---|---|---|---|---|---|
| HLD-01-01 | character | researcher | artifact 04 | none | PRD requires researcher as primary actor. | scene:PRD-S01 | active |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-01-01 | UPF-PRD-S01-01 | PRD-S01 requires researcher. | character researcher artifact 04 PRD requires researcher as primary actor. active | scene:PRD-S01 | support | tracks required entity | preserved |
| HLD-01-01 | UPF-PRD-S01-01 | PRD-S01 requires researcher. | character researcher artifact 04 PRD requires researcher as primary actor. active | scene:PRD-S01 | support | tracks required entity | preserved |
""", "Initial world entity inventory", "Inventory id")


def test_skill_verdict_output_rejects_invalid_values():
    with pytest.raises(ValueError, match="invalid Skill Verdict"):
        validator.validate_skill_verdict_output("""
## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | ok |
| Source closure | pass |
| Inventory coverage | closed |
| Boundary obedience | pass |
| Downstream readiness | ready |
| Blocking issue | none |
| Rerun target | none |
""")


def test_skill_verdict_rejects_pass_with_blocking_issue():
    with pytest.raises(ValueError, match="pass verdict cannot carry blocking issue"):
        validator.validate_skill_verdict_output("""
## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | closed |
| Inventory coverage | closed |
| Boundary obedience | pass |
| Downstream readiness | ready |
| Blocking issue | HLD-P1-01 |
| Rerun target | artifact 03 |
""")


def test_skill_verdict_rejects_pass_with_p2_with_blocking_state():
    with pytest.raises(ValueError, match="blocking state requires fail"):
        validator.validate_skill_verdict_output("""
## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass_with_p2 |
| Source closure | open:missing source |
| Inventory coverage | closed |
| Boundary obedience | pass |
| Downstream readiness | blocked:missing source |
| Blocking issue | HLD-P1-01 |
| Rerun target | artifact 03 |
""")


def test_integrator_skill_preservation_status_matches_contract():
    contract = validator.load_hld_contract()
    text = validator.read(validator.ROOT / "skills/novel-hld-integrator/SKILL.md")
    validator.validate_skill_preservation_status_terms(contract, "novel-hld-integrator", text)


def test_artifact_package_validation_requires_real_artifacts():
    contract = validator.load_hld_contract()
    with pytest.raises(ValueError, match="missing HLD artifact outputs"):
        validator.validate_hld_artifact_package(contract, {})


def test_artifact_package_rejects_artifact_12_missing_verdict_matrix():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    text = artifacts["12"]
    start = text.index("## Verdict consistency matrix")
    end = text.index("## HLD Convergence Log")
    artifacts["12"] = text[:start] + text[end:]

    with pytest.raises(ValueError, match="missing heading: Verdict consistency matrix"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_invalid_inventory_owner():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["01"] = artifacts["01"].replace(
        "| HLD-01-01 | character | researcher | artifact 04 |",
        "| HLD-01-01 | character | researcher | artifact 02 |",
    ).replace(
        "character researcher artifact 04 none PRD requires researcher as primary actor. active",
        "character researcher artifact 02 none PRD requires researcher as primary actor. active",
    )

    with pytest.raises(ValueError, match="invalid Required HLD owner"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_duplicate_inventory_id():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    duplicate_row = "| HLD-01-01 | character | researcher | artifact 04 | none | PRD requires researcher as primary actor. | scene:PRD-S01 | active |"
    artifacts["01"] = artifacts["01"].replace(duplicate_row, f"{duplicate_row}\n{duplicate_row}")

    with pytest.raises(ValueError, match="duplicate Initial world entity inventory id"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_inventory_owner_routing_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = artifacts["01"].replace(
        "| HLD-01-01 | character | researcher | artifact 04 |",
        "| HLD-01-01 | character | researcher | artifact 03 |",
    ).replace(
        "character researcher artifact 04 none PRD requires researcher as primary actor. active",
        "character researcher artifact 03 none PRD requires researcher as primary actor. active",
    )

    with pytest.raises(ValueError, match="invalid inventory owner routing"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_required_upstream_entity():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    upstream_text = """
PRD-S01 introduces multiple required entities.

## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S01-01 | Roles | upstream fact | researcher | character | scene:PRD-S01 |
| UPF-PRD-S01-02 | Roles | PRD-S01 requires digital life. | digital life | character | scene:PRD-S01 |
"""

    with pytest.raises(ValueError, match="artifact 01 missing required upstream entity"):
        validator.validate_hld_artifact_package(contract, artifacts, upstream_text=upstream_text)


def test_artifact_package_rejects_missing_upstream_required_entities_table():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    upstream_text = "PRD-S01 is covered, but the mandatory upstream entity table is missing."

    with pytest.raises(ValueError, match="missing mandatory Upstream required HLD entities"):
        validator.validate_hld_artifact_package(contract, artifacts, upstream_text=upstream_text)


def test_upstream_entity_table_requires_source_fact_field():
    legacy_upstream_text = """
## Upstream required HLD entities

| Upstream fact id | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|
| UPF-PRD-S01-01 | upstream fact | researcher | character | scene:PRD-S01 |
"""

    with pytest.raises(ValueError, match="Source fact field"):
        validator.extract_required_upstream_entities(legacy_upstream_text)


def test_authenticated_prd_handoff_rejects_unregistered_final_package(tmp_path):
    unregistered_final_package = tmp_path / "final-prd-package.md"
    unregistered_final_package.write_text("# forged final package\n")

    with pytest.raises(ValueError, match="not registered"):
        validator.validate_authenticated_prd_handoff(unregistered_final_package)


def test_authenticated_prd_handoff_accepts_registered_final_package():
    validator.validate_authenticated_prd_handoff(
        prd_validator.resolve_recorded_path(
            "docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md"
        )
    )


def test_artifact_package_rejects_secondary_owner_without_support_obligation():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = artifacts["01"].replace(
        "| HLD-01-01 | character | researcher | artifact 04 | none |",
        "| HLD-01-01 | character | researcher | artifact 04 | artifact 07 |",
    ).replace(
        "character researcher artifact 04 none PRD requires researcher as primary actor. active",
        "character researcher artifact 04 artifact 07 PRD requires researcher as primary actor. active",
    )

    with pytest.raises(ValueError, match="secondary owner lacks inventory-bound support obligation"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_secondary_owner_support_without_inventory_binding():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = artifacts["01"].replace(
        "| HLD-01-01 | character | researcher | artifact 04 | none |",
        "| HLD-01-01 | character | researcher | artifact 04 | artifact 07 |",
    ).replace(
        "character researcher artifact 04 none PRD requires researcher as primary actor. active",
        "character researcher artifact 04 artifact 07 PRD requires researcher as primary actor. active",
    )
    artifacts["02"] = _add_support_row(artifacts["02"], "HLD-02-08", owner="artifact 07")
    artifacts["07"] = artifacts["07"].replace(
        "| Digital-life dialogue opens the locked memory fragment. | HLD-02-05 |",
        "| Digital-life dialogue opens the locked memory fragment. | HLD-02-05, HLD-02-08 |",
    )

    with pytest.raises(ValueError, match="secondary owner lacks inventory-bound support obligation"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_secondary_owner_support_with_partial_source_binding():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = artifacts["01"].replace(
        "| HLD-01-01 | character | researcher | artifact 04 | none | PRD requires researcher as primary actor. | scene:PRD-S01 | active |",
        "| HLD-01-01 | character | researcher | artifact 04 | artifact 07 | PRD requires researcher as primary actor. | scene:PRD-S01, claim:CLAIM-01 | active |",
    ).replace(
        "character researcher artifact 04 none PRD requires researcher as primary actor. active",
        "character researcher artifact 04 artifact 07 PRD requires researcher as primary actor. active",
    ).replace(
        "| scene:PRD-S01 | explain | supports test package | preserved |",
        "| scene:PRD-S01, claim:CLAIM-01 | explain | supports test package | preserved |",
        1,
    )
    artifacts["02"] = _add_support_row(
        artifacts["02"],
        "HLD-02-08",
        owner="artifact 07",
        inventory_obligations="HLD-01-01",
    )
    artifacts["07"] = artifacts["07"].replace(
        "| Digital-life dialogue opens the locked memory fragment. | HLD-02-05 |",
        "| Digital-life dialogue opens the locked memory fragment. | HLD-02-05, HLD-02-08 |",
    )

    with pytest.raises(ValueError, match="secondary owner support source mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_invalid_inventory_initial_status():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = artifacts["01"].replace(
        "| scene:PRD-S01 | active |",
        "| scene:PRD-S01 | draft |",
        1,
    ).replace(
        "character researcher artifact 04 none PRD requires researcher as primary actor. active",
        "character researcher artifact 04 none PRD requires researcher as primary actor. draft",
    )

    with pytest.raises(ValueError, match="invalid Initial status"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_unrouteable_inventory_amendment_status():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = artifacts["01"].replace(
        "| HLD-01-01 | character | researcher | artifact 04 | none |",
        "| HLD-01-01 | unresolved amendment | researcher | artifact 04 | none |",
    ).replace(
        "| scene:PRD-S01 | active |",
        "| scene:PRD-S01 | amendment_needed:missing protected person |",
        1,
    ).replace(
        "character researcher artifact 04 none PRD requires researcher as primary actor. active",
        "unresolved amendment researcher artifact 04 none PRD requires researcher as primary actor. amendment_needed:missing protected person",
    )

    with pytest.raises(ValueError, match="unrouteable inventory amendment"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_01_trace_binds_owner_type_secondary_and_status():
    with pytest.raises(ValueError, match="HLD fact atom does not bind"):
        validator.validate_hld_artifact_trace_binding("""
## Initial world entity inventory

| Inventory id | Entity type | Entity name | Required HLD owner | Secondary HLD owners | Upstream evidence | Source | Initial status |
|---|---|---|---|---|---|---|---|
| HLD-01-01 | character | researcher | artifact 04 | artifact 07 | PRD requires researcher as primary actor. | scene:PRD-S01 | active |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-01-01 | UPF-PRD-S01-01 | PRD-S01 requires researcher. | researcher PRD requires researcher as primary actor. | scene:PRD-S01 | support | tracks required entity | preserved |
""", "Initial world entity inventory", "Inventory id")


def test_artifact_package_rejects_invalid_support_type():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["02"] = artifacts["02"].replace("| HLD-02-01 | scene:PRD-S01 | explain |", "| HLD-02-01 | scene:PRD-S01 | decorate |").replace(
        "scene:PRD-S01 explain artifact 03 none Explain why direct memory reading fails. Cannot make brainwave extraction succeed directly. ready",
        "scene:PRD-S01 decorate artifact 03 none Explain why direct memory reading fails. Cannot make brainwave extraction succeed directly. ready",
    )

    with pytest.raises(ValueError, match="invalid Support type"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_unconsumed_support_row():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["02"] = _add_support_row(artifacts["02"], "HLD-02-99", owner="artifact 04")

    with pytest.raises(ValueError, match="unconsumed support"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_support_not_consumed_by_required_owner():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["02"] = _add_support_row(artifacts["02"], "HLD-02-98", owner="artifact 04")
    artifacts["05"] = artifacts["05"].replace(
        "| HLD-02-03 | scene:PRD-S01 |",
        "| HLD-02-03, HLD-02-98 | scene:PRD-S01 |",
    ).replace(
        "access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. HLD-02-03 LLD-ENV-01",
        "access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. HLD-02-03, HLD-02-98 LLD-ENV-01",
    )

    with pytest.raises(ValueError, match="support owner did not consume"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_support_consumed_by_non_owner():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["02"] = _add_support_row(artifacts["02"], "HLD-02-97", owner="artifact 04")
    artifacts["03"] = artifacts["03"].replace(
        "| Closed memory cannot be opened by direct brainwave analysis. | HLD-02-01 | Direct extraction remains impossible. |",
        "| Closed memory cannot be opened by direct brainwave analysis. | HLD-02-01, HLD-02-97 | Direct extraction remains impossible. |",
    )
    artifacts["03"] = artifacts["03"].replace(
        "technology Closed memory cannot be opened by direct brainwave analysis. HLD-02-01 Direct extraction remains impossible. LLD-RULE-01",
        "technology Closed memory cannot be opened by direct brainwave analysis. HLD-02-01, HLD-02-97 Direct extraction remains impossible. LLD-RULE-01",
    )
    artifacts["04"] = artifacts["04"].replace(
        "| Investigates the closed memory through digital-life interaction. | Personal attachment conflicts with institutional duty. | Information permission",
        "| Investigates the closed memory through digital-life interaction. | Personal attachment conflicts with institutional duty. | Information permission",
    ).replace(
        "| HLD-02-02 | scene:PRD-S01 |",
        "| HLD-02-02, HLD-02-97 | scene:PRD-S01 |",
        ).replace(
            "HLD-01-01 character researcher researcher Investigates the closed memory through digital-life interaction. Fear of institutional misuse pressures duty. fear of institutional misuse pressures duty Can access dialogue outputs but not omniscient truth. human researcher identity remains distinct from senior and digital life HLD-02-02 LLD-CHAR-01",
            "HLD-01-01 character researcher researcher Investigates the closed memory through digital-life interaction. Fear of institutional misuse pressures duty. fear of institutional misuse pressures duty Can access dialogue outputs but not omniscient truth. human researcher identity remains distinct from senior and digital life HLD-02-02, HLD-02-97 LLD-CHAR-01",
        ).replace(
            "human researcher identity remains distinct from senior and digital life HLD-02-02 LLD-CHAR-01",
            "human researcher identity remains distinct from senior and digital life HLD-02-02, HLD-02-97 LLD-CHAR-01",
        )

    with pytest.raises(ValueError, match="support consumed by non-owner"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_character_support_consumed_by_non_owner():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["02"] = _add_support_row(artifacts["02"], "HLD-02-96", owner="artifact 05")
    artifacts["05"] = artifacts["05"].replace(
        "| HLD-02-03 | scene:PRD-S01 |",
        "| HLD-02-03, HLD-02-96 | scene:PRD-S01 |",
    ).replace(
        "access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. HLD-02-03 LLD-ENV-01",
        "access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. HLD-02-03, HLD-02-96 LLD-ENV-01",
    )
    artifacts["04"] = artifacts["04"].replace(
        "| HLD-02-02 | scene:PRD-S01 |",
        "| HLD-02-02, HLD-02-96 | scene:PRD-S01 |",
        ).replace(
            "HLD-01-01 character researcher researcher Investigates the closed memory through digital-life interaction. Fear of institutional misuse pressures duty. fear of institutional misuse pressures duty Can access dialogue outputs but not omniscient truth. human researcher identity remains distinct from senior and digital life HLD-02-02 LLD-CHAR-01",
            "HLD-01-01 character researcher researcher Investigates the closed memory through digital-life interaction. Fear of institutional misuse pressures duty. fear of institutional misuse pressures duty Can access dialogue outputs but not omniscient truth. human researcher identity remains distinct from senior and digital life HLD-02-02, HLD-02-96 LLD-CHAR-01",
        ).replace(
            "human researcher identity remains distinct from senior and digital life HLD-02-02 LLD-CHAR-01",
            "human researcher identity remains distinct from senior and digital life HLD-02-02, HLD-02-96 LLD-CHAR-01",
        )

    with pytest.raises(ValueError, match="support consumed by non-owner"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_character_inventory_design():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = _add_inventory_row(artifacts["01"], "HLD-01-02", "digital life")
    artifacts["10"] = artifacts["10"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-01-02 | HLD-10-02 | digital life | character | artifact 04 | artifact 04 | accept | none | inventory:INV-02 | Digital life is required by PRD scene support. | scene:PRD-S01 | closed |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-01-02 | UPF-PRD-S01-01 | PRD-S01 requires digital life. | digital life accept inventory:INV-02 Digital life is required by PRD scene support. | scene:PRD-S01 | handoff | finalizes character inventory | preserved |\n\n## Skill Verdict\n",
    )

    with pytest.raises(ValueError, match="missing character inventory design"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_environment_inventory_design():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    _add_environment_inventory_with_reconciliation(artifacts)

    with pytest.raises(ValueError, match="missing environment inventory design"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_environment_core_field():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["05"] = artifacts["05"].replace(
        "Enables monitored digital-life interaction.",
        "none",
    )

    with pytest.raises(ValueError, match="missing environment core field"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_invalid_environment_state_change_id():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["05"] = artifacts["05"].replace("ENV-STATE-05-01", "invalid-state")

    with pytest.raises(ValueError, match="invalid environment state change id"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_duplicate_environment_state_change_id():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    _add_environment_inventory_with_reconciliation(artifacts)
    artifacts["05"] = _add_environment_design_row(
        artifacts["05"],
        "HLD-01-02",
        "digital enclosure",
    ).replace("ENV-STATE-05-02", "ENV-STATE-05-01")

    with pytest.raises(ValueError, match="duplicate environment state change id"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_inventory_identity_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["05"] = artifacts["05"].replace("lab", "lab-alt")

    with pytest.raises(ValueError, match="environment inventory identity mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_inventory_source_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["05"] = artifacts["05"].replace("scene:PRD-S01", "claim:CLAIM-01")

    with pytest.raises(ValueError, match="environment inventory source mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_inventory_upstream_fact_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["05"] = artifacts["05"].replace("UPF-PRD-S01-02", "UPF-PRD-S01-03")

    with pytest.raises(ValueError, match="environment inventory upstream fact mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_trace_upstream_fact_atom_rewrite():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["05"] = artifacts["05"].replace("PRD-S01 requires lab.", "rewritten environment upstream fact")

    with pytest.raises(ValueError, match="environment inventory upstream fact atom mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_fact_missing_source_map_closure():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["11"] = "\n".join(
        line for line in artifacts["11"].splitlines()
        if "| HLD-F-05 |" not in line
    )

    with pytest.raises(ValueError, match="missing Source Map closure: artifact 05 HLD-05-01"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_unresolved_event_environment_ref():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace("HLD-05-01", "HLD-05-99")

    with pytest.raises(ValueError, match="unresolved event environment"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_event_environment_state_change_refs():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace(
        "ENV-STATE-05-01",
        "none",
    )

    with pytest.raises(ValueError, match="missing event environment state change refs"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_empty_event_causal_role():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace(
        "Forces the memory-lock investigation forward.",
        "none",
        1,
    )

    with pytest.raises(ValueError, match="missing event core field"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_empty_event_consequences():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace(
        "Researcher obtains usable intelligence without complete cause.",
        "none",
        1,
    )

    with pytest.raises(ValueError, match="missing event core field"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_empty_information_time_layer():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["07"] = artifacts["07"].replace("digital_interaction", "none", 1)

    with pytest.raises(ValueError, match="missing information core field"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_empty_information_reveal_condition():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["07"] = artifacts["07"].replace(
        "| action | HLD-06-01 | Digital-life disclosure reveals the memory lock during monitored dialogue. | HLD-02-05 |",
        "| action | HLD-06-01 | none | HLD-02-05 |",
    )

    with pytest.raises(ValueError, match="missing information core field"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_information_trace_upstream_fact_atom_rewrite():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["07"] = artifacts["07"].replace(
        "| HLD-07-01 | UPF-PRD-S01-04 | upstream fact |",
        "| HLD-07-01 | UPF-PRD-S01-04 | rewritten information premise |",
    )

    with pytest.raises(ValueError, match="information inventory upstream fact atom mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_information_reveal_action_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["07"] = artifacts["07"].replace(
        "Digital-life disclosure reveals the memory lock during monitored dialogue.",
        "A courier silently leaves an unrelated paper note at the station.",
    )

    with pytest.raises(ValueError, match="information reveal action mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_information_fact_trace_without_support_binding():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    before_trace, trace_and_after = artifacts["07"].split("## HLD Fact Trace", 1)
    trace, after_trace = trace_and_after.split("## Skill Verdict", 1)
    artifacts["07"] = "## HLD Fact Trace".join([
        before_trace,
        "## Skill Verdict".join([trace.replace("HLD-02-05 ", ""), after_trace]),
    ])

    with pytest.raises(ValueError, match="HLD fact atom does not bind HLD-07-01 to Time and information table.Supports"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_duplicate_information_inventory_binding():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    business_row = next(
        line for line in artifacts["07"].splitlines()
        if line.startswith("| HLD-07-01 | HLD-01-92 |")
    )
    trace_row = next(
        line for line in artifacts["07"].splitlines()
        if line.startswith("| HLD-07-01 | UPF-PRD-S01-04 |")
    )
    artifacts["07"] = artifacts["07"].replace(
        "\n## HLD Fact Trace\n",
        f"\n{business_row.replace('HLD-07-01', 'HLD-07-02', 1)}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{trace_row.replace('HLD-07-01', 'HLD-07-02', 1)}\n\n## Skill Verdict\n",
    )

    with pytest.raises(ValueError, match="duplicate information inventory binding"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_noncontiguous_information_reveal_phases():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["07"] = artifacts["07"].replace("REVEAL-01", "REVEAL-03")

    with pytest.raises(ValueError, match="information narrative reveal phases are not contiguous"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_action_condition_detached_from_reveal_action():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    old = "Digital-life disclosure reveals the memory lock during monitored dialogue."
    new = "A courier silently leaves an unrelated paper note at the station."
    artifacts["07"] = artifacts["07"].replace(
        f"| action | HLD-06-01 | {old} | HLD-02-05 |",
        f"| action | HLD-06-01 | {new} | HLD-02-05 |",
    )
    prefix, suffix = artifacts["07"].rsplit(old, 1)
    artifacts["07"] = f"{prefix}{new}{suffix}"

    with pytest.raises(ValueError, match="information action reveal condition mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_information_tier_dependencies_require_operational_predecessor_for_complete_cause():
    information = {
        "HLD-07-01": {"Disclosure tier": "operational_intelligence"},
        "HLD-07-02": {"Disclosure tier": "complete_cause"},
    }

    with pytest.raises(ValueError, match="complete cause lacks operational-intelligence predecessor"):
        validator.validate_information_tier_dependencies(
            information,
            {"HLD-07-01": set(), "HLD-07-02": set()},
        )

    validator.validate_information_tier_dependencies(
        information,
        {"HLD-07-01": set(), "HLD-07-02": {"HLD-07-01"}},
    )


def test_artifact_package_rejects_nontrigger_event_without_predecessor():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace(
        "| HLD-06-01 | HLD-01-91 | event | memory-lock disclosure | trigger |",
        "| HLD-06-01 | HLD-01-91 | event | memory-lock disclosure | revelation |",
        1,
    )

    with pytest.raises(ValueError, match="missing event predecessor"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_event_environment_state_change_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace("ENV-STATE-05-01", "ENV-STATE-05-99")

    with pytest.raises(ValueError, match="event environment state change mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_event_environment_state_realization():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace(
        "ENV-STATE-05-01 [access]: emergency authorization narrows laboratory entry.",
        "none",
    )

    with pytest.raises(ValueError, match="missing event environment state realizations"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_event_environment_state_realization_dimension_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace("[access]", "[visibility]")

    with pytest.raises(ValueError, match="event environment state realization dimension mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_reversed_event_environment_state_transition():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["06"] = artifacts["06"].replace(
        "ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY",
        "ENV-STATE-05-01:ACCESS_EMERGENCY_ONLY=>ACCESS_STANDARD",
    )

    with pytest.raises(ValueError, match="event environment state transition mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_without_event_integration():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    _add_environment_inventory_with_reconciliation(artifacts)
    artifacts["05"] = _add_environment_design_row(
        artifacts["05"],
        "HLD-01-02",
        "digital enclosure",
    )

    with pytest.raises(ValueError, match="missing environment event integration"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_support_inventory_obligation_bound_to_wrong_environment():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    _add_environment_inventory_with_reconciliation(artifacts)
    artifacts["02"] = _add_support_row(
        artifacts["02"],
        "HLD-02-98",
        owner="artifact 05",
        inventory_obligations="HLD-01-02",
    )
    environment_row = (
        "| HLD-05-02 | HLD-01-02 | environment | digital enclosure | enclosure | "
        "Contains the injected-memory dialogue boundary. | Is accessed only through the lab. | "
        "ENV-STATE-05-02 | visibility | VISIBILITY_NORMAL | VISIBILITY_EMERGENCY_ONLY | Visibility narrows as the crisis approaches. | HLD-02-03 | scene:PRD-S01 | LLD-ENV-02 | none |"
    )
    environment_trace = (
        "| HLD-05-02 | UPF-PRD-S01-01 | PRD-S01 requires digital enclosure. | "
        "HLD-01-02 environment digital enclosure enclosure Contains the injected-memory dialogue boundary. "
        "Is accessed only through the lab. ENV-STATE-05-02 visibility VISIBILITY_NORMAL VISIBILITY_EMERGENCY_ONLY Visibility narrows as the crisis approaches. HLD-02-03 LLD-ENV-02 | "
        "scene:PRD-S01 | explain | designs digital enclosure | preserved |"
    )
    artifacts["05"] = artifacts["05"].replace(
        "\n## HLD Fact Trace\n",
        f"\n{environment_row}\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        f"\n{environment_trace}\n\n## Skill Verdict\n",
    ).replace(
        "HLD-02-03 | scene:PRD-S01 | LLD-ENV-01",
        "HLD-02-03, HLD-02-98 | scene:PRD-S01 | LLD-ENV-01",
    ).replace(
        "access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. HLD-02-03 LLD-ENV-01",
        "access ACCESS_STANDARD ACCESS_EMERGENCY_ONLY Access tightens as crisis pressure rises. HLD-02-03, HLD-02-98 LLD-ENV-01",
    )

    with pytest.raises(ValueError, match="support inventory obligation not consumed by bound environment"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_abstract_character_motive_evidence():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["04"] = artifacts["04"].replace(
        "fear of institutional misuse pressures duty",
        "abstract ethics and good versus evil",
    )

    with pytest.raises(ValueError, match="invalid concrete motive evidence"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_vague_character_motive_evidence():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["04"] = artifacts["04"].replace(
        "fear of institutional misuse pressures duty",
        "fear",
    )

    with pytest.raises(ValueError, match="invalid concrete motive evidence"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_character_core_field():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["04"] = artifacts["04"].replace(
        "Can access dialogue outputs but not omniscient truth.",
        "none",
    )

    with pytest.raises(ValueError, match="missing character core field"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_unresolved_character_relationship_target():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["04"] = _ensure_character_relationship_targets_column(artifacts["04"]).replace(
        "Fear of institutional misuse pressures duty. | none | fear of institutional misuse pressures duty",
        "Personal attachment to the senior pressures duty. | HLD-04-99 | attachment to the senior pressures duty",
    ).replace(
        "Fear of institutional misuse pressures duty. none fear of institutional misuse pressures duty",
        "Personal attachment to the senior pressures duty. HLD-04-99 attachment to the senior pressures duty",
    ).replace(
        "Fear of institutional misuse pressures duty. fear of institutional misuse pressures duty",
        "Personal attachment to the senior pressures duty. HLD-04-99 attachment to the senior pressures duty",
    )

    with pytest.raises(ValueError, match="unresolved character relationship target"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_self_character_relationship_target():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["04"] = _ensure_character_relationship_targets_column(artifacts["04"]).replace(
        "Fear of institutional misuse pressures duty. | none | fear of institutional misuse pressures duty",
        "Personal attachment to the senior pressures duty. | HLD-04-01 | attachment to the senior pressures duty",
    ).replace(
        "Fear of institutional misuse pressures duty. none fear of institutional misuse pressures duty",
        "Personal attachment to the senior pressures duty. HLD-04-01 attachment to the senior pressures duty",
    ).replace(
        "Fear of institutional misuse pressures duty. fear of institutional misuse pressures duty",
        "Personal attachment to the senior pressures duty. HLD-04-01 attachment to the senior pressures duty",
    )

    with pytest.raises(ValueError, match="self character relationship target"):
        _validate_hld_artifact_package(contract, artifacts)


@pytest.mark.parametrize(("relationship_text", "motive_text"), [
    (
        "Personal attachment to the senior pressures duty.",
        "attachment to the senior pressures duty",
    ),
    (
        "Loyalty conflicts with fear of institutional misuse.",
        "loyalty conflicts with fear of institutional misuse",
    ),
    (
        "Concealment of the truth pressures duty.",
        "concealment of truth pressures duty",
    ),
    (
        "Protection pressure creates fear of exposure.",
        "protection pressure creates fear of exposure",
    ),
    (
        "Trust pressure creates fear of betrayal.",
        "trust pressure creates fear of betrayal",
    ),
    (
        "Distrust creates fear of institutional misuse.",
        "distrust creates fear of institutional misuse",
    ),
])
def test_artifact_package_rejects_relationship_pressure_without_target(relationship_text, motive_text):
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["04"] = artifacts["04"].replace(
        "Fear of institutional misuse pressures duty. | none | fear of institutional misuse pressures duty",
        f"{relationship_text} | none | {motive_text}",
    ).replace(
        "Fear of institutional misuse pressures duty. none fear of institutional misuse pressures duty",
        f"{relationship_text} none {motive_text}",
    ).replace(
        "Fear of institutional misuse pressures duty. fear of institutional misuse pressures duty",
        f"{relationship_text} {motive_text}",
    )

    with pytest.raises(ValueError, match="missing character relationship target"):
        _validate_hld_artifact_package(contract, artifacts)


def test_character_skill_relationship_bound_terms_match_validator():
    skill_text = validator.read(validator.ROOT / "skills/novel-character-system-designer/SKILL.md")
    for term in validator.RELATIONSHIP_BOUND_MOTIVE_TERMS:
        assert term in skill_text


def test_artifact_package_rejects_character_trace_source_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["04"] = artifacts["04"].replace(
        "| HLD-04-01 | UPF-PRD-S01-01 | upstream fact |",
        "| HLD-04-01 | UPF-PRD-S01-01 | upstream fact |",
    ).replace(
        "| scene:PRD-S01 | explain | supports test package | preserved |",
        "| claim:CLAIM-01 | explain | supports test package | preserved |",
        1,
    )

    with pytest.raises(ValueError, match="fact trace source mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_support_inventory_obligation_bound_to_wrong_character():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = _add_inventory_row(artifacts["01"], "HLD-01-02", "analyst")
    artifacts["02"] = _add_support_row(
        artifacts["02"],
        "HLD-02-98",
        owner="artifact 04",
        inventory_obligations="HLD-01-02",
    )
    artifacts["04"] = _ensure_character_relationship_targets_column(artifacts["04"]).replace(
        "| HLD-02-02 | scene:PRD-S01 |",
        "| HLD-02-02, HLD-02-98 | scene:PRD-S01 |",
    ).replace(
        "human researcher identity remains distinct from senior and digital life HLD-02-02 LLD-CHAR-01",
        "human researcher identity remains distinct from senior and digital life HLD-02-02, HLD-02-98 LLD-CHAR-01",
    ).replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-04-02 | HLD-01-02 | character | analyst | analyst | Interprets institutional pressure around the crisis. | Fear of organizational misuse pressures analyst duty. | none | fear of organizational misuse pressures analyst duty | Can access institutional orders but cannot access locked memory. | identity remains distinct from researcher and digital life | HLD-02-02 | scene:PRD-S01 | LLD-CHAR-02 | none |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-04-02 | UPF-PRD-S01-01 | PRD-S01 requires analyst. | HLD-01-02 character analyst analyst Interprets institutional pressure around the crisis. Fear of organizational misuse pressures analyst duty. fear of organizational misuse pressures analyst duty Can access institutional orders but cannot access locked memory. identity remains distinct from researcher and digital life HLD-02-02 LLD-CHAR-02 | scene:PRD-S01 | permission | defines analyst character pressure | bounded_expansion |\n\n## Skill Verdict\n",
    )
    artifacts["10"] = artifacts["10"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-01-02 | HLD-10-02 | analyst | character | artifact 04 | artifact 04 | accept | none | inventory:INV-02 | Analyst is required by PRD scene support. | scene:PRD-S01 | closed |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-01-02 | UPF-PRD-S01-01 | PRD-S01 requires analyst. | analyst accept inventory:INV-02 Analyst is required by PRD scene support. | scene:PRD-S01 | handoff | finalizes character inventory | preserved |\n\n## Skill Verdict\n",
    )

    with pytest.raises(ValueError, match="support inventory obligation not consumed by bound character"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_digital_life_without_identity_boundary():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = _add_inventory_row(artifacts["01"], "HLD-01-02", "digital life")
    artifacts["04"] = artifacts["04"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-04-02 | HLD-01-02 | character | digital life | digital-life subject | Maintains dialogue agency without becoming the senior. | Seeks self-protection against instrumental reuse. | none | self-protection against instrumental reuse | Can speak from injected memory fragments but cannot equal the senior. | none | HLD-02-02 | scene:PRD-S01 | LLD-CHAR-02 | none |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-04-02 | UPF-PRD-S01-01 | PRD-S01 requires digital life. | HLD-01-02 character digital life digital-life subject Maintains dialogue agency without becoming the senior. Seeks self-protection against instrumental reuse. self-protection against instrumental reuse Can speak from injected memory fragments but cannot equal the senior. HLD-02-02 LLD-CHAR-02 | scene:PRD-S01 | permission | defines digital-life identity pressure | bounded_expansion |\n\n## Skill Verdict\n",
    )
    artifacts["10"] = artifacts["10"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-01-02 | HLD-10-02 | digital life | character | artifact 04 | artifact 04 | accept | none | inventory:INV-02 | Digital life is required by PRD scene support. | scene:PRD-S01 | closed |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-01-02 | UPF-PRD-S01-01 | PRD-S01 requires digital life. | digital life accept inventory:INV-02 Digital life is required by PRD scene support. | scene:PRD-S01 | handoff | finalizes character inventory | preserved |\n\n## Skill Verdict\n",
    )

    with pytest.raises(ValueError, match="missing digital-life identity boundary"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_digital_life_contradictory_identity_boundary():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = _add_inventory_row(artifacts["01"], "HLD-01-02", "digital life")
    artifacts["04"] = artifacts["04"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-04-02 | HLD-01-02 | character | digital life | digital-life subject | Maintains dialogue agency without becoming the senior. | Seeks self-protection against instrumental reuse. | none | self-protection against instrumental reuse | Can speak from injected memory fragments but cannot equal the senior. | independent identity but it is the senior resurrected | HLD-02-02 | scene:PRD-S01 | LLD-CHAR-02 | none |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-04-02 | UPF-PRD-S01-01 | PRD-S01 requires digital life. | HLD-01-02 character digital life digital-life subject Maintains dialogue agency without becoming the senior. Seeks self-protection against instrumental reuse. self-protection against instrumental reuse Can speak from injected memory fragments but cannot equal the senior. independent identity but it is the senior resurrected HLD-02-02 LLD-CHAR-02 | scene:PRD-S01 | permission | defines digital-life identity pressure | bounded_expansion |\n\n## Skill Verdict\n",
    )
    artifacts["10"] = artifacts["10"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-01-02 | HLD-10-02 | digital life | character | artifact 04 | artifact 04 | accept | none | inventory:INV-02 | Digital life is required by PRD scene support. | scene:PRD-S01 | closed |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-01-02 | UPF-PRD-S01-01 | PRD-S01 requires digital life. | digital life accept inventory:INV-02 Digital life is required by PRD scene support. | scene:PRD-S01 | handoff | finalizes character inventory | preserved |\n\n## Skill Verdict\n",
    )

    with pytest.raises(ValueError, match="invalid digital-life identity boundary"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_character_inventory_design_without_matching_inventory_id():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = _add_inventory_row(artifacts["01"], "HLD-01-02", "researcher")
    artifacts["10"] = artifacts["10"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-01-02 | HLD-10-02 | researcher | character | artifact 04 | artifact 04 | accept | none | inventory:INV-02 | Researcher duplicate inventory row requires its own design binding. | scene:PRD-S01 | closed |\n\n## HLD Fact Trace\n",
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-01-02 | UPF-PRD-S01-01 | PRD-S01 requires researcher. | researcher accept inventory:INV-02 Researcher duplicate inventory row requires its own design binding. | scene:PRD-S01 | handoff | finalizes character inventory | preserved |\n\n## Skill Verdict\n",
    )

    with pytest.raises(ValueError, match="missing character inventory design"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_unclosed_world_rule_amendment_request():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["03"] = artifacts["03"].replace("| LLD-RULE-01 | none |", "| LLD-RULE-01 | HLD-AMEND-01 |")
    artifacts["03"] = artifacts["03"].replace(
        "technology Closed memory cannot be opened by direct brainwave analysis. HLD-02-01 Direct extraction remains impossible. LLD-RULE-01",
        "technology Closed memory cannot be opened by direct brainwave analysis. HLD-02-01 Direct extraction remains impossible. LLD-RULE-01 HLD-AMEND-01",
    )

    with pytest.raises(ValueError, match="unclosed amendment request"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_inventory_entity_without_final_disposition():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["01"] = _add_inventory_row(
        artifacts["01"],
        "HLD-01-02",
        "digital enclosure",
        owner="artifact 05",
        entity_type="environment",
    )
    artifacts["05"] = _add_environment_design_row(
        artifacts["05"],
        "HLD-01-02",
        "digital enclosure",
    )
    artifacts["06"] = artifacts["06"].replace(
        "| HLD-05-01 | ENV-STATE-05-01 | ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY | ENV-STATE-05-01 [access]: emergency authorization narrows laboratory entry. |",
        "| HLD-05-01, HLD-05-02 | ENV-STATE-05-01, ENV-STATE-05-02 | "
        "ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY; ENV-STATE-05-02:VISIBILITY_NORMAL=>VISIBILITY_EMERGENCY_ONLY | "
        "ENV-STATE-05-01 [access]: emergency authorization narrows laboratory entry.; "
        "ENV-STATE-05-02 [visibility]: the enclosure display narrows to emergency status. |",
    ).replace(
        "HLD-05-01 ENV-STATE-05-01 ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY ENV-STATE-05-01 [access]: emergency authorization narrows laboratory entry.",
        "HLD-05-01, HLD-05-02 ENV-STATE-05-01, ENV-STATE-05-02 "
        "ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY; ENV-STATE-05-02:VISIBILITY_NORMAL=>VISIBILITY_EMERGENCY_ONLY "
        "ENV-STATE-05-01 [access]: emergency authorization narrows laboratory entry.; "
        "ENV-STATE-05-02 [visibility]: the enclosure display narrows to emergency status.",
    )

    with pytest.raises(ValueError, match="missing final inventory disposition"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_source_map_final_id_not_minted_by_artifact_10():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["11"] = artifacts["11"].replace("inventory:INV-01", "inventory:INV-99")

    with pytest.raises(ValueError, match="unresolved final inventory id"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_non_inventory_final_id_in_reconciler():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["10"] = artifacts["10"].replace("inventory:INV-01", "scene:PRD-S01")

    with pytest.raises(ValueError, match="invalid Final inventory id"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_non_inventory_final_id_in_source_map():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["11"] = artifacts["11"].replace("inventory:INV-01", "claim:CLAIM-01")

    with pytest.raises(ValueError, match="invalid Final inventory id"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_reconciliation_identity_and_owner_spoof():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["10"] = artifacts["10"].replace(
        "| HLD-01-01 | HLD-10-01 | researcher | character | artifact 04 | artifact 04 | accept | none |",
        "| HLD-01-01 | HLD-10-01 | forged event | event | artifact 06 | artifact 09 | accept | none |",
    ).replace(
        "researcher accept none inventory:INV-01",
        "forged event accept none inventory:INV-01",
    )

    with pytest.raises(ValueError, match="reconciliation inventory identity mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_phantom_reconciliation_amendment():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["10"] = artifacts["10"].replace(
        "\n## HLD Fact Trace\n",
        "\n| HLD-AMEND-99 | HLD-10-99 | phantom amendment | unresolved amendment | artifact 10 | artifact 09 | accept | none | inventory:INV-99 | phantom approval | scene:PRD-S01 | closed |\n\n## HLD Fact Trace\n",
        1,
    ).replace(
        "\n## Skill Verdict\n",
        "\n| HLD-AMEND-99 | UPF-PRD-S01-01 | upstream fact | phantom amendment accept inventory:INV-99 phantom approval | scene:PRD-S01 | explain | supports test package | preserved |\n\n## Skill Verdict\n",
        1,
    )

    with pytest.raises(ValueError, match="unexpected reconciliation subject"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_merge_without_canonical_subject():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["10"] = artifacts["10"].replace(
        "| artifact 04 | accept | none | inventory:INV-01 |",
        "| artifact 04 | merge | none | inventory:INV-01 |",
        1,
    ).replace(
        "researcher accept none inventory:INV-01",
        "researcher merge none inventory:INV-01",
        1,
    )

    with pytest.raises(ValueError, match="merge reconciliation requires canonical subject"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_multiple_final_ids_for_one_subject():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["10"] = artifacts["10"].replace(
        "inventory:INV-01 | Researcher",
        "inventory:INV-01, inventory:INV-77 | Researcher",
        1,
    ).replace(
        "researcher accept none inventory:INV-01 Researcher",
        "researcher accept none inventory:INV-01, inventory:INV-77 Researcher",
        1,
    )

    with pytest.raises(ValueError, match="exactly one final inventory id"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_reconciliation_final_id_renumbering():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    previous_reconciliation_text = artifacts["10"]
    artifacts["10"] = artifacts["10"].replace(
        "inventory:INV-01",
        "inventory:INV-77",
    )
    artifacts["11"] = artifacts["11"].replace(
        "inventory:INV-01",
        "inventory:INV-77",
    )
    artifacts["12"] = artifacts["12"].replace(
        "inventory:INV-01",
        "inventory:INV-77",
    )
    artifacts["10"] = artifacts["10"].replace(
        "| Version | v1 |",
        "| Version | v1 |\n| Reconciliation mode | continuity |\n"
        f"| Previous reconciliation SHA256 | {hashlib.sha256(previous_reconciliation_text.encode('utf-8')).hexdigest()} |",
    )

    with pytest.raises(ValueError, match="reconciliation final inventory id changed"):
        _validate_hld_artifact_package(
            contract,
            artifacts,
            previous_reconciliation_text=previous_reconciliation_text,
        )


def test_artifact_package_requires_previous_reconciliation_for_continuity_mode():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["10"] = artifacts["10"].replace(
        "| Version | v1 |",
        "| Version | v1 |\n| Reconciliation mode | continuity |\n| Previous reconciliation SHA256 | pending |",
    )

    with pytest.raises(ValueError, match="continuity reconciliation requires previous artifact"):
        _validate_hld_artifact_package(contract, artifacts)


def test_reconciliation_amendment_trace_rejects_rewritten_origin_fact():
    origin_trace = {
        "Upstream fact id": "UPF-PRD-S01-01",
        "Upstream fact atom": "original amendment fact",
        "Source refs": "scene:PRD-S01",
    }
    reconciliation_trace = {
        "Upstream fact id": "UPF-PRD-S01-01",
        "Upstream fact atom": "rewritten amendment fact",
        "Source refs": "scene:PRD-S01",
    }

    with pytest.raises(ValueError, match="reconciliation amendment fact trace mismatch"):
        validator.validate_reconciliation_amendment_trace(origin_trace, reconciliation_trace, "HLD-AMEND-01")


def test_artifact_12_rubric_requires_reconciliation_quality_checks():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace(
        "Reconciliation subject register, origin binding, canonical merge target, single final inventory id, amendment blocking, and continuity check evidence recorded",
        "Inventory reconciliation rubric checked",
    )

    with pytest.raises(ValueError, match="Artifact 10 rubric missing reconciliation quality checks"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_source_map_reconciliation_owner_drift():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["11"] = artifacts["11"].replace(
        "| artifact 04 | inventory:INV-01 |",
        "| artifact 03 | inventory:INV-01 |",
    )

    with pytest.raises(ValueError, match="Source Map reconciliation owner mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_invalid_world_rule_type():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["03"] = artifacts["03"].replace("| HLD-03-01 | technology |", "| HLD-03-01 | decorative lore |")
    artifacts["03"] = artifacts["03"].replace(
        "technology Closed memory cannot be opened by direct brainwave analysis. HLD-02-01 Direct extraction remains impossible. LLD-RULE-01",
        "decorative lore Closed memory cannot be opened by direct brainwave analysis. HLD-02-01 Direct extraction remains impossible. LLD-RULE-01",
    )

    with pytest.raises(ValueError, match="invalid Rule type"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_invalid_event_type():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["06"] = artifacts["06"].replace(
        "| HLD-06-01 | HLD-01-91 | event | memory-lock disclosure | trigger |",
        "| HLD-06-01 | HLD-01-91 | event | memory-lock disclosure | chronology |",
    )

    with pytest.raises(ValueError, match="invalid Event type"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_invalid_thread_type_and_closure_state():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["08"] = artifacts["08"].replace("| HLD-08-01 | main |", "| HLD-08-01 | vibe |")

    with pytest.raises(ValueError, match="invalid Thread type"):
        _validate_hld_artifact_package(contract, artifacts)

    artifacts["08"] = _minimal_artifact_text(next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "08"))
    artifacts["08"] = artifacts["08"].replace(
        "| closed | The crisis is resolved",
        "| vague | The crisis is resolved",
    )
    artifacts["08"] = artifacts["08"].replace(
        "closed The crisis is resolved",
        "vague The crisis is resolved",
    )

    with pytest.raises(ValueError, match="invalid Closure state"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_thread_system_without_required_core_types():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract, complete_threads=False)

    with pytest.raises(ValueError, match="missing required thread types"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_nonsemantic_thread_core_question():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["08"] = artifacts["08"].replace(
        "Can the crisis be resolved without destroying the protected human cause?",
        "x",
    )

    with pytest.raises(ValueError, match="invalid thread core question"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_core_threads_with_duplicate_question():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    main_question = "Can the crisis be resolved without destroying the protected human cause?"
    for core_question in (
        "What private cause does the memory lock conceal?",
        "Can the researcher distinguish grief from responsibility?",
        "What does protection cost when truth can be extracted?",
        "Can the organization close the case without owning every truth?",
        "Who is the digital life when memory is not a resurrection?",
    ):
        artifacts["08"] = artifacts["08"].replace(core_question, main_question)

    with pytest.raises(ValueError, match="duplicate core thread question"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_core_thread_function_relabeling():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["08"] = artifacts["08"].replace(
        "withhold_then_reframe_cause",
        "advance_crisis_resolution",
    )

    with pytest.raises(ValueError, match="invalid core thread function"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_core_threads_with_shared_only_pressure():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    for scene_ref in ("scene:PRD-S02", "scene:PRD-S03", "scene:PRD-S04", "scene:PRD-S05", "scene:PRD-S06"):
        artifacts["02"] = artifacts["02"].replace(scene_ref, "scene:PRD-S01")
        artifacts["08"] = artifacts["08"].replace(scene_ref, "scene:PRD-S01")

    with pytest.raises(ValueError, match="core thread lacks distinct pressure ref"):
        _validate_hld_artifact_package(contract, artifacts)


def test_thread_system_rejects_unordered_or_stateless_progression():
    threads, support_by_id = _core_thread_rows_for_contract_tests()
    threads[0]["Thread progression"] = "HLD-06-01, HLD-07-01"

    with pytest.raises(ValueError, match="invalid thread progression"):
        validator.validate_thread_system_rows(
            threads,
            {"HLD-06-01"},
            {"HLD-07-01"},
            support_by_id,
        )


def test_thread_system_rejects_type_without_required_design_anchor():
    threads, support_by_id = _core_thread_rows_for_contract_tests()
    threads[0]["Thread anchor refs"] = "character:HLD-04-01"

    with pytest.raises(ValueError, match="missing required thread anchor type"):
        validator.validate_thread_system_rows(
            threads,
            {"HLD-06-01"},
            {"HLD-07-01"},
            support_by_id,
        )


def test_artifact_package_rejects_thread_rubric_without_core_thread_quality_checks():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    start = artifacts["12"].index("## Thread closure checks")
    end = artifacts["12"].index("## HLD Convergence Log")
    artifacts["12"] = artifacts["12"][:start] + artifacts["12"][end:]

    with pytest.raises(ValueError, match="missing heading: Thread closure checks"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_required_style_rule_types():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["09"] = "\n".join(
        line
        for line in artifacts["09"].splitlines()
        if not any(line.startswith(f"| HLD-09-{index:02d} |") for index in range(2, 8))
    )

    with pytest.raises(ValueError, match="missing required Style/POV Rule types"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_style_rule_with_unresolved_hld_refs():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["09"] = artifacts["09"].replace(
        "info:HLD-07-01",
        "info:HLD-07-99",
    )

    with pytest.raises(ValueError, match="unresolved style information ref"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_style_system_without_closure_checks():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    start = artifacts["12"].index("## Style/POV closure checks")
    end = artifacts["12"].index("## HLD Convergence Log")
    artifacts["12"] = artifacts["12"][:start] + artifacts["12"][end:]

    with pytest.raises(ValueError, match="missing heading: Style/POV closure checks"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_style_system_without_language_profile_rule():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["09"] = "\n".join(
        line for line in artifacts["09"].splitlines()
        if not line.startswith("| HLD-09-08 |")
    )

    with pytest.raises(ValueError, match="missing required Style/POV Rule types"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_style_rule_without_reader_disclosure_mode():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["09"] = artifacts["09"].replace("external_inference", "direct_reveal")

    with pytest.raises(ValueError, match="invalid style reader disclosure mode"):
        _validate_hld_artifact_package(contract, artifacts)


def test_style_skill_rule_type_catalog_matches_validator():
    skill_text = validator.read(
        validator.ROOT / "skills" / "novel-style-pov-system-designer" / "SKILL.md"
    )
    rule_type_line = next(
        line for line in skill_text.splitlines()
        if line.startswith("- Rule type must be one of")
    )

    normalized_rule_type_line = rule_type_line.casefold()
    for rule_type in validator.STYLE_POV_RULE_TYPES:
        assert rule_type in normalized_rule_type_line


def test_artifact_package_rejects_unstructured_style_execution_fields():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    replacements = {
        "rule=Filter digital-life agency through observation; scope=info:HLD-07-01; effect=Readers infer interiority from visible signs.": "Style outcome appears pleasing overall.",
        "focalizer=researcher; permitted=Report observed dialogue and behavior; evidence=info:HLD-07-01": "Write from an appropriate angle.",
        "forbidden=State unrestricted digital-life thoughts; target=thread:HLD-08-01; trigger=external_inference": "Avoid inappropriate wording throughout.",
    }
    for artifact_id, artifact_text in artifacts.items():
        for old_value, new_value in replacements.items():
            artifact_text = artifact_text.replace(old_value, new_value)
        artifacts[artifact_id] = artifact_text

    with pytest.raises(ValueError, match="invalid style execution constraint"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_style_execution_without_type_specific_behavior():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts = {
        artifact_id: artifact_text.replace(
            "rule=Filter digital-life agency through observation",
            "rule=uniform_rule_for_everything",
        )
        for artifact_id, artifact_text in artifacts.items()
    }

    with pytest.raises(ValueError, match="invalid style execution rule"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_accepts_short_chinese_style_focalizer():
    validator.validate_style_focalizer("林岚", {"林岚"}, "HLD-09-01")


def test_artifact_package_rejects_unresolved_style_focalizer():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts = {
        artifact_id: artifact_text.replace(
            "focalizer=researcher",
            "focalizer=不存在者",
        )
        for artifact_id, artifact_text in artifacts.items()
    }

    with pytest.raises(ValueError, match="unresolved style focalizer"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_execution_refs_outside_row_contract():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    replacements = {
        "scope=info:HLD-07-01": "scope=info:HLD-07-99",
        "evidence=info:HLD-07-01": "evidence=info:HLD-07-99",
        "target=thread:HLD-08-01": "target=thread:HLD-08-99",
        "trigger=external_inference": "trigger=unregistered_disclosure_mode",
    }
    for artifact_id, artifact_text in artifacts.items():
        for old_value, new_value in replacements.items():
            artifact_text = artifact_text.replace(old_value, new_value)
        artifacts[artifact_id] = artifact_text

    with pytest.raises(ValueError, match="style execution .* mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_vague_chinese_style_effect():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts = {
        artifact_id: artifact_text.replace(
            "effect=Readers infer interiority from visible signs.",
            "effect=整体感觉十分优美自然动人。",
        )
        for artifact_id, artifact_text in artifacts.items()
    }

    with pytest.raises(ValueError, match="invalid style execution constraint"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_language_profile_without_dimension_instructions():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    old_profile = (
        "register=mode:restrained formal narration, limit:avoid evaluative abstraction; "
        "syntax=sentence:balanced clauses with controlled breaks, variation:shorten under immediate pressure; "
        "diction=prefer:precise institutional and sensory terms, avoid:ungrounded technical jargon; "
        "rhythm=pace:measured sentences with pressure pauses, shift:accelerate only during verified action"
    )
    incomplete_profile = (
        "register=mode:restrained formality; syntax=sentence:balanced clauses; "
        "diction=prefer:precise terminology; rhythm=pace:measured pacing"
    )
    artifacts = {
        artifact_id: artifact_text.replace(old_profile, incomplete_profile)
        for artifact_id, artifact_text in artifacts.items()
    }

    with pytest.raises(ValueError, match="invalid language profile"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_unresolved_event_participant():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["06"] = artifacts["06"].replace("HLD-04-01", "HLD-04-99")

    with pytest.raises(ValueError, match="unresolved participant reference"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_artifact_12_missing_rubric_coverage():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    text = artifacts["12"]
    start = text.index("## Artifact rubric coverage")
    end = text.index("## HLD Convergence Log")
    artifacts["12"] = text[:start] + text[end:]

    with pytest.raises(ValueError, match="missing heading: Artifact rubric coverage"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_blocking_risk_without_fact_trace():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    text = artifacts["12"]
    text = text.replace("| Agent quality verdict | pass |", "| Agent quality verdict | fail |")
    text = text.replace("| LLD entry verdict | pass_to_lld |", "| LLD entry verdict | blocked_revision_required |")
    text = text.replace(
        "| Agent quality verdict | all required checks pass and no unresolved P0/P1 | all required checks pass and no unresolved P0/P1 | pass | pass |",
        "| Agent quality verdict | all required checks pass and no unresolved P0/P1 | all required checks pass and no unresolved P0/P1 | fail | pass |",
    )
    text = text.replace(
        "| LLD entry verdict | Agent quality pass plus human review confirmed or not_required | pass_to_lld conditions satisfied | pass_to_lld | pass |",
        "| LLD entry verdict | Agent quality pass plus human review confirmed or not_required | pass_to_lld conditions satisfied | blocked_revision_required | pass |",
    )
    text = text.replace(
        "| none | P3 | none | none | none | none | none |",
        "| HLD-RISK-01 | P1 | scene:PRD-S01 | artifact 11 | artifact 11 | unresolved source drift | blocks pass_to_lld |",
        1,
    )
    text = text.replace(
        "| none | P3 | none | none | none | 0 | none | closed |",
        "| HLD-RISK-01 | P1 | Source Map drift. | Rerun artifact 11. | validator rejects drift. | 1 | artifact 11 | open |",
    )
    text = text.replace("| Skill quality verdict | pass |", "| Skill quality verdict | fail |")
    text = text.replace("| Source closure | closed |", "| Source closure | open:source drift |")
    text = text.replace("| Downstream readiness | ready |", "| Downstream readiness | blocked:source drift |")
    text = text.replace("| Blocking issue | none |", "| Blocking issue | HLD-RISK-01 |")
    text = text.replace("| Rerun target | none |", "| Rerun target | artifact 11 |")
    artifacts["12"] = text

    with pytest.raises(ValueError, match="blocking risk lacks fact trace"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_failed_verdict_matrix_row():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["12"] = artifacts["12"].replace(
        "| LLD entry verdict | Agent quality pass plus human review confirmed or not_required | pass_to_lld conditions satisfied | pass_to_lld | pass |",
        "| LLD entry verdict | Agent quality pass plus human review confirmed or not_required | pass_to_lld conditions satisfied | pass_to_lld | fail |",
    )

    with pytest.raises(ValueError, match="verdict matrix contains non-pass consistency"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_risk_without_traceability_values():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["12"] = artifacts["12"].replace(
        "| none | P3 | none | none | none | none | none |",
        "| HLD-RISK-02 | P2 | none | none | none | unresolved style drift | nonblocking report |",
        1,
    )

    with pytest.raises(ValueError, match="risk row missing traceability values"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_nonblocking_risk_without_fact_trace():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["12"] = artifacts["12"].replace(
        "| none | P3 | none | none | none | none | none |",
        "| HLD-RISK-03 | P2 | scene:PRD-S01 | artifact 09 | artifact 09 | resolved:style wording needs cleanup | nonblocking report |",
        1,
    )

    with pytest.raises(ValueError, match="risk lacks fact trace"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_failed_rubric_coverage():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    artifacts["12"] = artifacts["12"].replace(
            "| Artifact 06 | Event inventory coverage, causal-chain closure, concrete event action, consequence, visibility, environment integration, and Source Map trace closure checked | Missing event inventory, cause, action, consequence, visibility, environment integration, or Source Map closure blocks | pass |",
            "| Artifact 06 | Event inventory coverage, causal-chain closure, concrete event action, consequence, visibility, environment integration, and Source Map trace closure checked | Missing event inventory, cause, action, consequence, visibility, environment integration, or Source Map closure blocks | fail |",
    )

    with pytest.raises(ValueError, match="rubric coverage contains non-pass verdict"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_12_rubric_requires_event_quality_checks():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace(
        "Event inventory coverage, causal-chain closure, concrete event action, consequence, visibility, environment integration, and Source Map trace closure checked",
        "Event system checked",
    ).replace(
        "Missing event inventory, cause, action, consequence, visibility, environment integration, or Source Map closure blocks",
        "Event system checked",
    )

    with pytest.raises(ValueError, match="Artifact 06 rubric missing event quality checks"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_12_rubric_requires_character_quality_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    text = _minimal_artifact_12_text(artifact_12).replace(
        "Actors have function, concrete motive pressure, relationship target closure, information permission, and digital-life identity boundary",
        "Actors have function, relationship, and information permission",
    )

    with pytest.raises(ValueError, match="Artifact 04 rubric missing character quality checks"):
        validator.validate_artifact_12_rubric_coverage(text)


def test_artifact_12_rubric_requires_complete_style_pov_quality_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    text = _minimal_artifact_12_text(artifact_12).replace(
        "prohibited expression, and language style have Access policy",
        "prohibited expression have Access policy",
    )

    with pytest.raises(ValueError, match="Artifact 09 rubric missing Style/POV quality checks"):
        validator.validate_artifact_12_rubric_coverage(text)


def test_artifact_12_rubric_requires_structured_style_execution_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    text = _minimal_artifact_12_text(artifact_12).replace(
        "Language profile directives, type-specific behavior, execution reference closure, focalizer resolution, structured Design fact, POV permission, Prohibited expression execution fields",
        "Language profile directives, type-specific behavior, execution reference closure, focalizer resolution, Design fact, POV permission, Prohibited expression execution fields",
    ).replace(
        "Language profile directives, type-specific behavior, vague expression, execution reference closure, focalizer resolution, structured execution fields",
        "Language profile directives, type-specific behavior, vague expression, execution reference closure, focalizer resolution",
    )

    with pytest.raises(ValueError, match="Artifact 09 rubric missing Style/POV quality checks"):
        validator.validate_artifact_12_rubric_coverage(text)


def test_artifact_12_rubric_requires_type_specific_style_behavior_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    text = _minimal_artifact_12_text(artifact_12).replace(
        "Language profile directives, type-specific behavior, execution reference closure, focalizer resolution, structured Design fact",
        "Language profile directives, execution reference closure, focalizer resolution, structured Design fact",
    ).replace(
        "Language profile directives, type-specific behavior, vague expression, execution reference closure, focalizer resolution, structured execution fields",
        "Language profile directives, vague expression, execution reference closure, focalizer resolution, structured execution fields",
    )

    with pytest.raises(ValueError, match="Artifact 09 rubric missing Style/POV quality checks"):
        validator.validate_artifact_12_rubric_coverage(text)


def test_artifact_12_rubric_requires_style_execution_reference_closure_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    text = _minimal_artifact_12_text(artifact_12).replace(
        "type-specific behavior, execution reference closure, focalizer resolution, structured Design fact",
        "type-specific behavior, structured Design fact",
    ).replace(
        "type-specific behavior, vague expression, execution reference closure, focalizer resolution, structured execution fields",
        "type-specific behavior, vague expression, structured execution fields",
    )

    with pytest.raises(ValueError, match="Artifact 09 rubric missing Style/POV quality checks"):
        validator.validate_artifact_12_rubric_coverage(text)


def test_artifact_12_rubric_requires_environment_closure_checks():
    contract = validator.load_hld_contract()
    artifact_12 = next(artifact for artifact in contract["artifacts"] if artifact.get("id") == "12")
    text = _minimal_artifact_12_text(artifact_12).replace(
        "Environments have inventory coverage, spatial relation, state-change dimension, state transition, event state realization, and Source Map trace closure",
        "Environments have causal function",
    )

    with pytest.raises(ValueError, match="Artifact 05 rubric missing environment closure checks"):
        validator.validate_artifact_12_rubric_coverage(text)


def test_artifact_package_rejects_missing_environment_closure_evidence_table():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace(
        "\n## Environment closure checks\n",
        "\n## Removed environment closure checks\n",
    )

    with pytest.raises(ValueError, match="missing heading: Environment closure checks"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_closure_state_change_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace("ENV-STATE-05-01", "ENV-STATE-05-99")

    with pytest.raises(ValueError, match="environment closure state change mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_closure_event_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace("HLD-06-01", "HLD-06-99")

    with pytest.raises(ValueError, match="environment closure event mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_closure_source_map_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace("HLD-F-05", "HLD-F-99")

    with pytest.raises(ValueError, match="environment closure Source Map mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_information_source_map_closure():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["11"] = artifacts["11"].replace("| artifact 07 |", "| artifact 09 |")

    with pytest.raises(ValueError, match="Source Map reconciliation owner mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_missing_character_source_map_closure():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["11"] = "\n".join(
        line for line in artifacts["11"].splitlines()
        if "| HLD-F-01 |" not in line
    )

    with pytest.raises(ValueError, match="missing Source Map closure: artifact 04 HLD-04-01"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_requires_lld_handoff_index():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    handoff_start = artifacts["11"].index("## LLD handoff index")
    trace_start = artifacts["11"].index("## HLD Fact Trace")
    artifacts["11"] = artifacts["11"][:handoff_start] + artifacts["11"][trace_start:]

    with pytest.raises(ValueError, match="missing heading: LLD handoff index"):
        _validate_hld_artifact_package(contract, artifacts, normalize_integrator=False)


def test_artifact_package_rejects_lld_handoff_index_source_drift():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["11"] = artifacts["11"].replace(
        "| artifact 04 | inventory:INV-01 | UPF-PRD-S01-01 | upstream fact |",
        "| artifact 04 | inventory:INV-01 | UPF-PRD-S01-01 | rewritten upstream fact |",
        1,
    )

    with pytest.raises(ValueError, match="LLD handoff index drift: HLD-F-01"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_extra_conflicting_lld_handoff_index_row():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    handoff_row = next(
        line for line in artifacts["11"].splitlines()
        if line.startswith("| LLD-CHAR-01 | HLD-F-01 |")
    )
    conflicting_row = handoff_row.replace("| LLD-CHAR-01 |", "| LLD-CHAR-99 |", 1)
    artifacts["11"] = artifacts["11"].replace(
        "\n## HLD Fact Trace\n",
        f"\n{conflicting_row}\n\n## HLD Fact Trace\n",
        1,
    )

    with pytest.raises(ValueError, match="duplicate LLD handoff mappings for HLD fact: HLD-F-01"):
        _validate_hld_artifact_package(contract, artifacts)


def test_integrator_output_table_schemas_are_well_formed():
    text = validator.read(validator.ROOT / "skills/novel-hld-integrator/SKILL.md")
    for heading, column_count in [("HLD Source Map", 12), ("LLD handoff index", 9)]:
        section = text.split(f"Produce `## {heading}` with columns:", 1)[1].lstrip().split("\n\n", 1)[0]
        lines = [line for line in section.splitlines() if line.startswith("|")]
        assert len(lines) == 2
        assert len(lines[0].strip("|").split("|")) == column_count
        assert len(lines[1].strip("|").split("|")) == column_count
        assert all(set(cell.strip()) <= {"-", ":"} for cell in lines[1].strip("|").split("|"))


def test_artifact_package_rejects_information_closure_source_map_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace("HLD-F-07", "HLD-F-99")

    with pytest.raises(ValueError, match="information closure Source Map mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_closure_realization_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace(
        "| HLD-06-01:ENV-STATE-05-01 | HLD-F-05 |",
        "| HLD-06-01:ENV-STATE-05-99 | HLD-F-05 |",
    )

    with pytest.raises(ValueError, match="environment closure realization mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_environment_closure_transition_mismatch():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace(
        "HLD-06-01:ENV-STATE-05-01:ACCESS_STANDARD=>ACCESS_EMERGENCY_ONLY",
        "HLD-06-01:ENV-STATE-05-01:ACCESS_EMERGENCY_ONLY=>ACCESS_STANDARD",
    )

    with pytest.raises(ValueError, match="environment closure transition mismatch"):
        _validate_hld_artifact_package(contract, artifacts)


def test_integrity_skill_rule_validation_rejects_v2_environment_terms():
    text = validator.read(validator.ROOT / "skills/novel-hld-integrity-checker/SKILL.md")
    text = text.replace(
        "state-change dimension, state transition, event state realization",
        "state change, event integration",
    )
    text += "\n## Legacy Terms\n\nstate-change dimension; state transition; event state realization\n"

    with pytest.raises(ValueError, match="Artifact 05 rubric terms"):
        validator.validate_hld_integrity_environment_rule_terms(text)


def test_artifact_package_rejects_environment_trace_atom_mismatching_prd_canonical_atom():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    upstream_text = _minimal_upstream_text().replace(
        "PRD-S01 requires lab.",
        "PRD-S01 requires an unmodified lab boundary.",
    )

    with pytest.raises(ValueError, match="artifact 01 upstream fact atom mismatch"):
        validator.validate_hld_artifact_package(contract, artifacts, upstream_text=upstream_text)


def test_artifact_package_validation_accepts_complete_minimal_package():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    _validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_requires_upstream_source_inventory():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )

    with pytest.raises(ValueError, match="upstream source inventory required"):
        validator.validate_hld_artifact_package(contract, artifacts)


def test_artifact_package_rejects_unauthenticated_information_boundary_table():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)

    with pytest.raises(ValueError, match="authenticated PRD information-boundary sources required"):
        validator.validate_hld_artifact_package(
            contract,
            artifacts,
            upstream_text=_minimal_upstream_text(),
        )


def test_information_boundary_alignment_rejects_actor_knowledge_drift():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    upstream_text = _minimal_upstream_text().replace(
        "| PRD-INFO-01 | PRD-S01 | PRD-S01 | 1 | operational_intelligence | usable intelligence | concealed | entity:researcher | reader | none | action | freeze:PRD-FREEZE-01 | scene:PRD-S01 | HLD must bind the usable intelligence reveal to the PRD scene. |",
        "| PRD-INFO-01 | PRD-S01 | PRD-S01 | 1 | operational_intelligence | usable intelligence | concealed | entity:organization | reader, entity:researcher | none | action | freeze:PRD-FREEZE-01 | scene:PRD-S01 | HLD must bind the usable intelligence reveal to the PRD scene. |",
    )

    with pytest.raises(ValueError, match="knowledge state mismatch"):
        validator.validate_upstream_information_boundary_alignment(upstream_text, artifacts)


def test_artifact_package_runs_upstream_source_coverage_when_upstream_text_provided():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    upstream_text = "PRD-S01 is covered. PRD-S02 and CLAIM-01 must also be covered."

    with pytest.raises(ValueError, match="artifact 01 missing upstream source coverage"):
        validator.validate_hld_artifact_package(contract, artifacts, upstream_text=upstream_text)


def test_artifact_dir_runs_upstream_source_coverage_from_upstream_files(tmp_path):
    contract = validator.load_hld_contract()
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    for artifact_id, text in _minimal_hld_artifacts(contract).items():
        (artifact_dir / f"{artifact_id}.md").write_text(text, encoding="utf-8")
    upstream_path = tmp_path / "upstream.md"
    upstream_path.write_text("PRD-S01 is covered. PRD-S02 and CLAIM-01 must also be covered.", encoding="utf-8")

    with pytest.raises(ValueError, match="artifact 01 missing upstream source coverage"):
        validator.validate_hld_artifact_dir(
            contract,
            artifact_dir,
            [upstream_path],
            authenticate_prd_handoff=False,
        )


def test_upstream_source_coverage_rejects_missing_artifact_01_ref():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    upstream_text = """
    PRD-S01 requires direct reading failure.
    PRD-S02 requires digital-life handoff.
    CLAIM-01 and HLD-REQ-01 must be preserved.
    """
    artifacts["02"] = artifacts["02"].replace("scene:PRD-S01", "scene:PRD-S01, scene:PRD-S02, claim:CLAIM-01, hldreq:HLD-REQ-01")

    with pytest.raises(ValueError, match="artifact 01 missing upstream source coverage"):
        validator.validate_upstream_source_coverage(upstream_text, artifacts)


def test_upstream_source_coverage_rejects_missing_artifact_02_ref():
    contract = validator.load_hld_contract()
    artifacts = {}
    for artifact in contract["artifacts"]:
        if not artifact.get("skill"):
            continue
        artifacts[artifact["id"]] = (
            _minimal_artifact_12_text(artifact)
            if artifact["id"] == "12"
            else _minimal_artifact_text(artifact)
        )
    upstream_text = """
    PRD-S01 requires direct reading failure.
    PRD-S02 requires digital-life handoff.
    CLAIM-01 and HLD-REQ-01 must be preserved.
    """
    artifacts["01"] = artifacts["01"].replace("scene:PRD-S01", "scene:PRD-S01, scene:PRD-S02, claim:CLAIM-01, hldreq:HLD-REQ-01")

    with pytest.raises(ValueError, match="artifact 02 missing upstream source coverage"):
        validator.validate_upstream_source_coverage(upstream_text, artifacts)


def test_p0_p1_blocks_lld_entry_verdict():
    with pytest.raises(ValueError, match="unresolved P0/P1"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | not_required |
| LLD entry verdict | pass_to_lld |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| HLD-RISK-01 | P1 | scene:PRD-S01 | artifact 11 | artifact 11 | unresolved source drift | blocks pass_to_lld |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| HLD-RISK-01 | P1 | Source Map changed fact. | Rerun artifact 11. | validator rejects drift before fix. | 1 | artifact 11 | open |
""")


def test_human_review_pending_blocks_lld_pass():
    with pytest.raises(ValueError, match="human review state"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | pending_required |
| LLD entry verdict | pass_to_lld |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| none | P3 | none | none | none | none | none |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| none | P3 | none | none | none | 0 | none | closed |
""")


def test_failed_agent_quality_cannot_be_routed_to_pending_human_review():
    with pytest.raises(ValueError, match="failed Agent quality must require blocked_revision_required"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| Agent quality verdict | fail |
| HLD human review state | pending_required |
| LLD entry verdict | blocked_pending_human_review |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| none | P3 | none | none | none | none | none |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| none | P3 | none | none | none | 0 | none | closed |
""")


def test_artifact_12_risk_trace_rejects_invalid_upstream_fact_id():
    with pytest.raises(ValueError, match="invalid risk fact trace upstream fact id: HLD-RISK-01"):
        validator.validate_artifact_12_risk_trace_binding("""
## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-RISK-01 | invented-source | source atom | risk finding | scene:PRD-S01 | explain | audit | risk_reported |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| HLD-RISK-01 | P1 | scene:PRD-S01 | artifact 11 | artifact 11 | unresolved source drift | blocks pass_to_lld |
""")


def test_artifact_12_risk_trace_requires_existing_hld_source_binding():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    report = """
## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-RISK-01 | UPF-PRD-S99-01 | invented source atom | risk finding | scene:PRD-S01 | explain | audit | risk_reported |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| HLD-RISK-01 | P1 | scene:PRD-S01 | artifact 11 | artifact 11 | unresolved source drift | blocks pass_to_lld |
"""

    with pytest.raises(ValueError, match="risk fact trace lacks HLD source binding: HLD-RISK-01"):
        validator.validate_artifact_12_risk_trace_binding(report, artifacts)


def test_convergence_log_must_cover_p1_risk():
    with pytest.raises(ValueError, match="lacks convergence"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| Agent quality verdict | fail |
| HLD human review state | not_required |
| LLD entry verdict | blocked_revision_required |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| HLD-RISK-02 | P1 | inventory:INV-01 | artifact 10 | artifact 10 | unresolved missing inventory | blocks pass_to_lld |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| HLD-RISK-99 | P1 | Other issue. | Rerun artifact 10. | validator. | 1 | artifact 10 | open |
""")


def test_open_p1_convergence_issue_requires_matching_risk_row():
    with pytest.raises(ValueError, match="convergence issue lacks Risk row: HLD-RISK-01"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | not_required |
| LLD entry verdict | pass_to_lld |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| none | P3 | none | none | none | none | none |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| HLD-RISK-01 | P1 | source drift | rerun artifact 11 | validator test | 1 | artifact 11 | open |
""")


def test_artifact_12_output_requires_all_authoritative_verdicts():
    with pytest.raises(ValueError, match="Output missing verdict fields"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| HLD human review state | not_required |
| LLD entry verdict | pass_to_lld |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| none | P3 | none | none | none | none | none |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| none | P3 | none | none | none | 0 | none | closed |
""")


def test_artifact_12_rejects_malformed_convergence_log_without_risks():
    with pytest.raises(ValueError, match="HLD Convergence Log missing required columns"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | not_required |
| LLD entry verdict | pass_to_lld |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| none | P3 | none | none | none | none | none |

## HLD Convergence Log

| Note | Detail |
|---|---|
| none | none |
""")


def test_artifact_12_rejects_mismatched_p3_convergence_for_unresolved_p1():
    with pytest.raises(ValueError, match="convergence severity mismatch: HLD-RISK-01"):
        validator.validate_risk_verdict_consistency("""
## Output

| Field | Value |
|---|---|
| Agent quality verdict | fail |
| HLD human review state | not_required |
| LLD entry verdict | blocked_revision_required |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| HLD-RISK-01 | P1 | scene:PRD-S01 | artifact 11 | artifact 11 | unresolved source drift | blocks pass_to_lld |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| HLD-RISK-01 | P3 | unrelated root cause | unrelated fix | unrelated proof | 1 | artifact 11 | fixed |
""")


def test_artifact_12_risk_trace_requires_complete_fact_trace_fields():
    with pytest.raises(ValueError, match="HLD Fact Trace missing required columns"):
        validator.validate_artifact_12_risk_trace_binding("""
## HLD Fact Trace

| Fact trace id |
|---|
| HLD-RISK-01 |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| HLD-RISK-01 | P1 | scene:PRD-S01 | artifact 11 | artifact 11 | unresolved source drift | blocks pass_to_lld |
""")


def test_artifact_12_verdict_matrix_requires_output_value_binding():
    contract = validator.load_hld_contract()
    artifacts = _minimal_hld_artifacts(contract)
    artifacts["12"] = artifacts["12"].replace(
        "| Agent quality verdict | all required checks pass and no unresolved P0/P1 | all required checks pass and no unresolved P0/P1 | pass | pass |",
        "| Agent quality verdict | all required checks pass and no unresolved P0/P1 | all required checks pass and no unresolved P0/P1 | fail | pass |",
    )

    with pytest.raises(ValueError, match="Verdict consistency matrix value mismatch: Agent quality verdict"):
        _validate_hld_artifact_package(contract, artifacts)


def test_legacy_hld_writer_is_not_authoritative():
    contract = validator.load_hld_contract()
    validator.validate_legacy_writer_demoted(contract)


def test_methodology_reference_has_sources_and_artifact_rubrics():
    contract = validator.load_hld_contract()
    validator.validate_methodology_reference(contract)


def test_contract_rule_coverage_is_executable():
    contract = validator.load_hld_contract()
    validator.validate_contract_rule_coverage(contract)


def test_contract_rule_10_names_all_risk_traceability():
    contract = validator.load_hld_contract()
    rule = next(rule for rule in contract["contract_rules"] if rule["id"] == "HLD-CONTRACT-10")
    assert "every non-none risk" in rule["rule"]
    assert "relationship target closure" in rule["rule"]
    assert "event state realization" in rule["rule"]
    assert "Source Map trace closure" in rule["rule"]


def test_contract_rule_13_names_character_and_environment_regressions():
    contract = validator.load_hld_contract()
    coverage = contract["rule_coverage"]["HLD-CONTRACT-13"]["tests"]
    assert "test_character_skill_references_define_good_delivery_standards" in coverage
    assert "test_artifact_package_rejects_abstract_character_motive_evidence" in coverage
    assert "test_artifact_package_rejects_vague_character_motive_evidence" in coverage
    assert "test_artifact_package_rejects_missing_character_core_field" in coverage
    assert "test_artifact_package_rejects_unresolved_character_relationship_target" in coverage
    assert "test_artifact_package_rejects_self_character_relationship_target" in coverage
    assert "test_artifact_package_rejects_relationship_pressure_without_target" in coverage
    assert "test_character_skill_relationship_bound_terms_match_validator" in coverage
    assert "test_artifact_package_rejects_character_trace_source_mismatch" in coverage
    assert "test_artifact_package_rejects_support_inventory_obligation_bound_to_wrong_character" in coverage
    assert "test_artifact_package_rejects_digital_life_without_identity_boundary" in coverage
    assert "test_artifact_package_rejects_digital_life_contradictory_identity_boundary" in coverage
    assert "test_artifact_05_schema_requires_inventory_identity_columns" in coverage
    assert "test_artifact_06_schema_requires_environment_integration_columns" in coverage
    assert "test_environment_skill_references_define_good_delivery_standards" in coverage
    assert "test_artifact_package_rejects_missing_environment_inventory_design" in coverage
    assert "test_artifact_package_rejects_missing_environment_core_field" in coverage
    assert "test_artifact_package_rejects_environment_inventory_identity_mismatch" in coverage
    assert "test_artifact_package_rejects_environment_inventory_source_mismatch" in coverage
    assert "test_artifact_package_rejects_environment_inventory_upstream_fact_mismatch" in coverage
    assert "test_artifact_package_rejects_environment_trace_upstream_fact_atom_rewrite" in coverage
    assert "test_artifact_package_rejects_environment_fact_missing_source_map_closure" in coverage
    assert "test_artifact_package_rejects_unresolved_event_environment_ref" in coverage
    assert "test_artifact_package_rejects_invalid_environment_state_change_id" in coverage
    assert "test_artifact_package_rejects_duplicate_environment_state_change_id" in coverage
    assert "test_artifact_package_rejects_missing_event_environment_state_change_refs" in coverage
    assert "test_artifact_package_rejects_event_environment_state_change_mismatch" in coverage
    assert "test_artifact_package_rejects_missing_event_environment_state_realization" in coverage
    assert "test_artifact_package_rejects_event_environment_state_realization_dimension_mismatch" in coverage
    assert "test_artifact_package_rejects_environment_without_event_integration" in coverage
    assert "test_artifact_package_rejects_support_inventory_obligation_bound_to_wrong_environment" in coverage
