"""Frozen topology, ownership, source access and package profiles."""

from __future__ import annotations

HARNESS = "novel-hld-autonomous"
VERSION = "0.1.0"

STAGES = ("HB0", "HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HQ1", "HP1", "HQ2", "HH1", "HF1")

SKILLS = {
    "HB0": "novel-hld-baseline-admitter",
    "HA1": "novel-hld-narrative-architect",
    "HS1": "novel-hld-storyline-choreographer",
    "HC1": "novel-hld-character-arc-placer",
    "HI1": "novel-hld-information-architect",
    "HR1": "novel-hld-rhythm-continuity-architect",
    "HK1": "novel-hld-key-scene-function-planner",
    "HQ1": "novel-hld-semantic-reviewer",
    "HP1": "novel-hld-package-assembler",
    "HQ2": "novel-hld-lld-readiness-evaluator",
    "HH1": "novel-hld-human-review-composite",
    "HF1": "novel-hld-finalizer",
}

UPSTREAM = {
    "HB0": (),
    "HA1": ("HB0",),
    "HS1": ("HB0", "HA1"),
    "HC1": ("HB0", "HA1", "HS1"),
    "HI1": ("HB0", "HA1", "HS1", "HC1"),
    "HR1": ("HB0", "HA1", "HS1", "HC1", "HI1"),
    "HK1": ("HB0", "HA1", "HS1", "HC1", "HI1", "HR1"),
    "HQ1": ("HB0", "HA1", "HS1", "HC1", "HI1", "HR1", "HK1"),
    "HP1": ("HB0", "HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HQ1"),
    "HQ2": ("HB0", "HP1"),
    "HH1": ("HB0", "HP1", "HQ2"),
    "HF1": ("HB0", "HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HQ1", "HP1", "HQ2", "HH1"),
}

NON_QUALITY_DOMAINS = ("intent", "storylines", "world", "environments", "events", "characters", "narrative", "cross-domain")
ALL_SOURCE_DOMAINS = NON_QUALITY_DOMAINS + ("quality",)
DESIGN_STAGES = ("HA1", "HS1", "HC1", "HI1", "HR1", "HK1")

SOURCE_ACCESS_MATRIX = {
    "HB0": ALL_SOURCE_DOMAINS,
    **{stage: NON_QUALITY_DOMAINS for stage in DESIGN_STAGES},
    "HQ1": ALL_SOURCE_DOMAINS,
    "HP1": (), "HQ2": (), "HH1": (), "HF1": (),
}

ID_OWNER_PREFIX = {
    "HST": "HA1", "HNU": "HA1", "HCH": "HA1",
    "HTS": "HS1", "HTC": "HS1",
    "HAS": "HC1", "HRS": "HC1",
    "HPV": "HI1", "HKS": "HI1", "HSP": "HI1", "HIN": "HI1",
    "HTM": "HR1", "HPC": "HR1", "HTN": "HR1",
    "HKF": "HK1", "LWR": "HK1", "LWK": "HP1",
    "HFN": "HQ1",
    "HRE": "HH1", "HVG": "HH1", "HUI": "HH1",
}

READY_PACKAGE_PROFILES = {
    "HB0": (
        "hld-control-baseline.json", "hld-source-index.json", "hb0-execution.json",
        "validation.json", "package-manifest.json", "stage-completion.json",
    ),
    "HQ1": (
        "hld-semantic-review.json", "review-session.json", "review-execution.json",
        "validation.json", "package-manifest.json", "stage-completion.json",
    ),
    "HP1": (
        "novel-hld-package.json", "novel-hld-spec.md", "hld-cross-index.json",
        "hld-traceability-matrix.json", "hld-traceability-matrix.md", "lld-handoff.json",
        "canonical-models/narrative-architecture.json", "canonical-models/storyline-choreography.json",
        "canonical-models/character-arc-placement.json", "canonical-models/narrative-information-architecture.json",
        "canonical-models/rhythm-continuity-architecture.json", "canonical-models/key-scene-function-map.json",
        "canonical-models/hld-semantic-review.json",
        "assembly-execution.json", "validation.json", "package-manifest.json", "stage-completion.json",
    ),
    "HQ2": (
        "lld-handoff-acceptance.json", "q2-publish-execution.json", "validation.json",
        "package-manifest.json", "stage-completion.json",
    ),
    "HH1": (
        "hld-human-review-report.json", "presentation-fidelity-review.json",
        "hld-human-review-report.html", "render-target-registry.json",
        "hh1-publish-execution.json", "validation.json", "package-manifest.json",
        "stage-completion.json",
    ),
}

INTERNAL_READY_PACKAGE_PROFILES = {
    "HQ2.consumer_test": (
        "handoff-consumption-test.json", "review-session.json", "consumption-test-execution.json",
        "validation.json", "package-manifest.json",
    ),
    "HQ2.fidelity_test": (
        "handoff-fidelity-test.json", "review-session.json", "fidelity-test-execution.json",
        "validation.json", "package-manifest.json",
    ),
    "HH1.A": (
        "hld-human-review-report.json", "generation-session.json", "report-assembly-execution.json",
        "validation.json", "package-manifest.json",
    ),
    "HH1.B": (
        "presentation-fidelity-review.json", "review-session.json", "fidelity-review-execution.json",
        "validation.json", "package-manifest.json",
    ),
    "HH1.C": (
        "hld-human-review-report.html", "render-target-registry.json", "render-execution.json",
        "validation.json", "package-manifest.json",
    ),
}

BOUNDED_EVAL_DIMENSIONS = (
    "scope_fidelity", "input_gate_obedience", "output_contract_correctness",
    "semantic_or_deterministic_correctness", "boundary_discipline", "parent_consumability",
)

HLD_ASSIGNMENT = {
    "next_stage": "novel-hld",
    "responsibilities": (
        "overall-narrative-architecture", "multi-thread-choreography", "character-arc-placement",
        "act-and-chapter-progression", "key-scene-functions",
        "suspense-setup-probe-reveal-payoff",
        "time-space-pacing-tension-pov-information-architecture",
        "hld-to-lld-handoff-and-acceptance",
    ),
    "required_capabilities": (
        "traceable-conception-inheritance", "complete-multi-thread-architecture",
        "character-arc-and-event-alignment", "time-space-pacing-pov-information-control",
        "key-scene-function-coverage", "lld-ready-handoff-with-acceptance",
    ),
    "prohibitions": (
        "change-conception-authority", "resolve-author-owned-question",
        "produce-lld-material", "write-prose",
    ),
}


def next_stage(stage: str) -> str | None:
    index = STAGES.index(stage)
    return STAGES[index + 1] if index + 1 < len(STAGES) else None


def owner_for_id(stable_id: str) -> str:
    prefix = stable_id.split("-", 1)[0]
    if prefix in ID_OWNER_PREFIX:
        if prefix in {"HRE", "HVG"}:
            return "HH1-A"
        if prefix == "HUI":
            return "HH1-C"
        return ID_OWNER_PREFIX[prefix]
    raise ValueError(f"unregistered stable ID prefix: {stable_id}")


def invalidated_suffix(owner: str, target_kind: str) -> tuple[str, ...]:
    if target_kind == "render_expression":
        return ("HH1", "HF1")
    if target_kind in {"report_content", "presentation_review"}:
        return ("HH1", "HF1")
    stage = owner.split("-", 1)[0]
    start = STAGES.index(stage)
    return STAGES[start:]
