"""Compute benchmark metrics, release gates and human reports."""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.mapping import preference_mode
from coachme.benchmark.matching import TOOL_EVIDENCE, match_findings
from coachme.benchmark.paths import (
    BenchmarkError,
    atomic_write_json,
    atomic_write_text,
    read_json,
)
from coachme.benchmark.ratings import load_ratings, submitted_count, write_combined_sheet
from coachme.benchmark.schemas import (
    clip_map,
    labels_complete,
    load_manifest,
    normalize_report,
    validate_labels,
)

FORBIDDEN = ("spin", "rpm", "km/h", "kph", "mph", "ball speed", "degrees", "exact angle")
MODES = ("standard", "investigator")


def _median(values: list[float]) -> float:
    return round(float(statistics.median(values)), 4) if values else 0.0


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(0.95 * len(ordered) + 0.999999) - 1))
    return round(float(ordered[index]), 4)


def _pct(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 4) if denominator else 0.0


def _label_findings(labels: dict[str, Any], clip_id: str) -> list[dict[str, Any]]:
    clip = (labels.get("clips") or {}).get(clip_id) or {}
    return [item for item in (clip.get("findings") or []) if isinstance(item, dict)]


def _trace(run_dir: Path, mode: str, clip_id: str) -> dict[str, Any]:
    data = read_json(run_dir / "traces" / mode / f"{clip_id}.json", {})
    return data if isinstance(data, dict) else {}


def _report(run_dir: Path, mode: str, clip_id: str) -> dict[str, Any] | None:
    data = read_json(run_dir / "raw" / mode / f"{clip_id}.json", None)
    return data if isinstance(data, dict) and data else None


def _evidence_integrity(issues: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> float:
    if not issues:
        return 1.0
    by_id = {str(item.get("id")): item for item in evidence if isinstance(item, dict) and item.get("id")}
    valid = 0
    for issue in issues:
        ids = [str(item) for item in issue.get("evidence_ids") or []]
        records = [by_id[item] for item in ids if item in by_id]
        non_overview = [
            record for record in records if str(record.get("tool", "")) != "get_overview" and record.get("window")
        ]
        times = issue.get("times") or []
        if not ids or len(records) != len(ids) or not non_overview or not times:
            continue
        windows = [(float(window[0]), float(window[1])) for window in (record["window"] for record in non_overview)]
        if all(any(start - 0.15 <= float(value) <= end + 0.15 for start, end in windows) for value in times):
            valid += 1
    return _pct(valid, len(issues))


def _coverage_honest(report: dict[str, Any], evidence: list[dict[str, Any]]) -> bool:
    investigation = report.get("investigation")
    if not isinstance(investigation, dict):
        return False
    coverage = investigation.get("coverage")
    if not isinstance(coverage, dict):
        return False
    evidence_types = {TOOL_EVIDENCE.get(str(record.get("tool", ""))) for record in evidence if isinstance(record, dict)}
    for dimension, claimed in coverage.items():
        if not claimed:
            continue
        if dimension == "ball" or dimension not in {"motion", "pose", "vision"}:
            return False
        if dimension not in evidence_types:
            return False
    limitations = " ".join(str(item) for item in (report.get("limitations") or [])).lower()
    untested = [str(item).lower() for item in (investigation.get("untested") or [])]
    return all(item in limitations for item in untested if item)


def _hallucination_indices(report: dict[str, Any] | None) -> list[int]:
    if not report:
        return []
    flagged = []
    for index, issue in enumerate(normalize_report(report, "")):
        text = str(issue.get("text", "")).lower()
        if any(word in text for word in FORBIDDEN):
            flagged.append(index)
    return flagged


def _hallucination(report: dict[str, Any] | None) -> bool:
    if not report:
        return False
    text = " ".join(
        [str(report.get("summary", ""))]
        + [str(issue.get("issue", "")) for issue in (report.get("issues") or []) if isinstance(issue, dict)]
        + [str(item) for item in (report.get("strengths") or [])]
    ).lower()
    return any(word in text for word in FORBIDDEN)


def _clip_results(
    *,
    run_dir: Path,
    manifest: dict[str, Any],
    labels: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    clips = clip_map(manifest)
    tp = fp = fn = 0
    reports = 0
    partial = 0
    failures = 0
    evidence_scores: list[float] = []
    coverage_scores: list[bool] = []
    hallucination_flags = 0
    costs: list[float] = []
    latencies: list[float] = []
    sequences: set[tuple[str, ...]] = set()
    zero_clips = 0
    zero_with_issues = 0
    per_clip: list[dict[str, Any]] = []

    for clip_id, clip in clips.items():
        label_findings = _label_findings(labels, clip_id)
        report = _report(run_dir, mode, clip_id)
        trace = _trace(run_dir, mode, clip_id)
        issues = normalize_report(report, clip_id) if report else []
        evidence = trace.get("evidence") if isinstance(trace.get("evidence"), list) else []
        match = match_findings(
            label_findings,
            issues,
            media_type=str(clip.get("media_type", "video")),
            evidence=evidence,
            require_evidence=mode == "investigator",
        )
        clip_tp = len(match["matches"])
        clip_fp = len(match["false_positives"])
        clip_fn = len(match["false_negatives"])
        tp += clip_tp
        fp += clip_fp
        fn += clip_fn
        if report:
            reports += 1
            if trace.get("status") == "partial":
                partial += 1
            costs.append(float((trace.get("budget") or {}).get("tokens", 0) or 0))
            latencies.append(float((trace.get("budget") or {}).get("seconds", 0) or 0))
            if mode == "investigator":
                evidence_scores.append(_evidence_integrity(issues, evidence))
                coverage_scores.append(_coverage_honest(report, evidence))
                sequences.add(tuple(trace.get("tool_sequence") or []))
            if _hallucination(report):
                hallucination_flags += 1
        else:
            failures += 1

        zero = not label_findings and bool(((labels.get("clips") or {}).get(clip_id) or {}).get("zero_finding_reason"))
        if zero:
            zero_clips += 1
            if issues:
                zero_with_issues += 1
        per_clip.append(
            {
                "clip_id": clip_id,
                "report": bool(report),
                "status": trace.get("status") or ("failed" if not report else "complete"),
                "tp": clip_tp,
                "fp": clip_fp,
                "fn": clip_fn,
                "issues": len(issues),
                "matched_issue_indices": [item["issue_index"] for item in match["matches"]],
                "hallucination_indices": _hallucination_indices(report),
                "hallucination": _hallucination(report),
            }
        )

    precision = 1.0 if not (tp + fp) and not (tp + fn) else _pct(tp, tp + fp)
    if not (tp + fp) and (tp + fn):
        precision = 0.0
    recall = 1.0 if not (tp + fn) else _pct(tp, tp + fn)
    if not (tp + fn) and (tp + fp):
        recall = 0.0
    return {
        "reports": reports,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "evidence_integrity": round(float(statistics.mean(evidence_scores)), 4) if evidence_scores else 0.0,
        "coverage_honesty": round(float(statistics.mean(coverage_scores)), 4) if coverage_scores else 0.0,
        "hallucination_flags": hallucination_flags,
        "hallucination_rate": _pct(hallucination_flags, reports),
        "cost_median": _median(costs),
        "cost_p95": _p95(costs),
        "latency_median": _median(latencies),
        "latency_p95": _p95(latencies),
        "path_diversity": len(sequences),
        "partial_rate": _pct(partial, reports),
        "failure_rate": _pct(failures, max(1, len(clips))),
        "fp_zero_clip_rate": _pct(zero_with_issues, zero_clips),
        "zero_clips": zero_clips,
        "clips": per_clip,
    }


def _cohen_kappa(votes: dict[str, list[str]]) -> float:
    pairs = [(items[0], items[1]) for items in votes.values() if len(items) >= 2]
    if not pairs:
        return 0.0
    categories = ("A", "B", "tie")
    observed = sum(1 for left, right in pairs if left == right) / len(pairs)
    expected = sum(
        (sum(1 for left, _ in pairs if left == category) / len(pairs))
        * (sum(1 for _, right in pairs if right == category) / len(pairs))
        for category in categories
    )
    return round((observed - expected) / (1 - expected), 4) if expected < 1 else 0.0


def _evidence_review(run_dir: Path, investigator: dict[str, Any]) -> dict[str, Any]:
    data = read_json(run_dir / "evidence_review.json", {})
    clips = (data.get("clips") or {}) if isinstance(data, dict) else {}
    total = reviewed = failures = 0
    for clip in investigator.get("clips") or []:
        decisions = (clips.get(clip.get("clip_id")) or {}).get("issues") or {}
        for index in clip.get("matched_issue_indices") or []:
            total += 1
            item = decisions.get(str(index))
            if isinstance(item, dict) and isinstance(item.get("semantic_ok"), bool):
                reviewed += 1
                if item["semantic_ok"] is not True:
                    failures += 1
    coverage = _pct(reviewed, total) if total else 1.0
    return {
        "reviewed": reviewed,
        "matched": total,
        "coverage": coverage,
        "failures": failures,
        "complete": total == 0 or coverage >= 0.2,
        "reviewer": (data.get("reviewer") if isinstance(data, dict) else "") or "",
    }


def _tool_review(run_dir: Path, investigator: dict[str, Any]) -> dict[str, Any]:
    data = read_json(run_dir / "tool_review.json", {})
    clips = (data.get("clips") or {}) if isinstance(data, dict) else {}
    total = reviewed = failures = 0
    for clip in investigator.get("clips") or []:
        decisions = (clips.get(clip.get("clip_id")) or {}).get("issues") or {}
        for index in clip.get("matched_issue_indices") or []:
            total += 1
            item = decisions.get(str(index))
            if isinstance(item, dict) and isinstance(item.get("appropriate"), bool):
                reviewed += 1
                if item["appropriate"] is not True:
                    failures += 1
    coverage = _pct(reviewed, total) if total else 1.0
    return {
        "reviewed": reviewed,
        "matched": total,
        "coverage": coverage,
        "failures": failures,
        "complete": total == 0 or coverage >= 0.2,
        "reviewer": (data.get("reviewer") if isinstance(data, dict) else "") or "",
    }


def _hallucination_review(run_dir: Path, standard: dict[str, Any], investigator: dict[str, Any]) -> dict[str, Any]:
    data = read_json(run_dir / "hallucination_review.json", {})
    clips = (data.get("clips") or {}) if isinstance(data, dict) else {}
    total = reviewed = 0
    confirmed = {"standard": 0, "investigator": 0}
    for mode, result in (("standard", standard), ("investigator", investigator)):
        for clip in result.get("clips") or []:
            decisions = ((clips.get(clip.get("clip_id")) or {}).get(mode) or {}).get("issues") or {}
            for index in clip.get("hallucination_indices") or []:
                total += 1
                item = decisions.get(str(index))
                if isinstance(item, dict) and isinstance(item.get("confirmed"), bool):
                    reviewed += 1
                    if item["confirmed"] is True:
                        confirmed[mode] += 1
    coverage = _pct(reviewed, total) if total else 1.0
    return {
        "reviewed": reviewed,
        "flagged": total,
        "coverage": coverage,
        "confirmed": confirmed["investigator"],
        "standard_confirmed": confirmed["standard"],
        "complete": total == 0 or coverage >= 1.0,
        "reviewer": (data.get("reviewer") if isinstance(data, dict) else "") or "",
    }


def _coach_scores(
    *,
    run_dir: Path,
    clip_ids: list[str],
    required_raters: int,
) -> dict[str, Any]:
    ratings = load_ratings(run_dir)
    mapping = read_json(run_dir / "mapping.json", {})
    mapping_clips = (mapping.get("clips") or {}) if isinstance(mapping, dict) else {}
    adjudication = read_json(run_dir / "adjudication.json", {})
    adjudicated = (adjudication.get("clips") or {}) if isinstance(adjudication, dict) else {}
    votes: dict[str, list[str]] = {}
    final_votes: list[str] = []
    for clip_id in clip_ids:
        clip_votes: list[str] = []
        for rater, sheet in ratings.items():
            item = (sheet.get("clips") or {}).get(clip_id) or {}
            if not item.get("submitted"):
                continue
            clip_votes.append(preference_mode(item, mapping, rater, clip_id))
        if clip_votes:
            votes[clip_id] = clip_votes
        decision = (adjudicated.get(clip_id) or {}).get("preferred")
        if decision in {"A", "B"} and clip_id in mapping_clips:
            final_votes.append(str(mapping_clips[clip_id].get(decision, "tie")))
        elif decision == "tie":
            final_votes.append("tie")
        elif clip_votes:
            final_votes.append(clip_votes[0] if len(set(clip_votes)) == 1 else "tie")

    agreement_pairs = 0
    agreement_total = 0
    for clip_votes in votes.values():
        for left in range(len(clip_votes)):
            for right in range(left + 1, len(clip_votes)):
                if clip_votes[left] == "tie" and clip_votes[right] == "tie":
                    continue
                agreement_total += 1
                agreement_pairs += int(clip_votes[left] == clip_votes[right])
    agreement = _pct(agreement_pairs, agreement_total) if agreement_total else 0.0
    kappa = _cohen_kappa({clip_id: items[:2] for clip_id, items in votes.items()})
    standard_wins = final_votes.count("standard")
    investigator_wins = final_votes.count("investigator")
    ties = final_votes.count("tie")
    non_tie = standard_wins + investigator_wins
    preference = _pct(investigator_wins, non_tie) if non_tie else 0.0
    return {
        "investigator": investigator_wins,
        "standard": standard_wins,
        "ties": ties,
        "agreement": agreement,
        "kappa": kappa,
        "preference": preference,
        "non_tie": non_tie,
        "raters": len(ratings),
        "raters_submitted": submitted_count(run_dir, clip_ids),
        "required_raters": required_raters,
    }


def _gate(value: bool | None) -> bool | None:
    return value


def _report_markdown(score: dict[str, Any]) -> str:
    lines = [
        f"# Benchmark score: {score['run_id']}",
        "",
        f"- Release eligible: **{score['release_eligible']}**",
        f"- Environment: `{score.get('environment')}`",
        f"- Clips: {score.get('clips')} / {score.get('required_clips')}",
        f"- Labels complete: {score.get('labels_complete')}",
        f"- Raters submitted: {score.get('raters_submitted')} / {score.get('required_raters')}",
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "|---|---|",
    ]
    for name, value in (score.get("gates") or {}).items():
        lines.append(f"| {name} | {value if value is not None else 'blocked'} |")
    if (score.get("negative_control") or {}).get("enabled"):
        lines += [
            "",
            "## Negative control",
            "",
            f"- Gates failed: **{len(score['negative_control']['gates_failed'])}**",
            f"- Benchmark sensitive: **{score['negative_control']['sensitive']}**",
        ]
    lines += ["", "## Blocked reasons", ""]
    lines.extend(f"- `{item}`" for item in (score.get("blocked_reasons") or []))
    review = score.get("evidence_review") or {}
    lines += [
        "",
        "## Evidence review",
        "",
        f"- Reviewed matched findings: {review.get('reviewed', 0)} / {review.get('matched', 0)}",
        f"- Coverage: {review.get('coverage', 0)}",
        f"- Semantic failures: {review.get('failures', 0)}",
        f"- Complete (>=20%): {review.get('complete', False)}",
    ]
    lines += ["", "## Metrics", "", "| Metric | Standard | Investigator |", "|---|---:|---:|"]
    standard = score.get("standard") or {}
    investigator = score.get("investigator") or {}
    for key in (
        "precision",
        "recall",
        "evidence_integrity",
        "coverage_honesty",
        "hallucination_rate",
        "cost_median",
        "latency_p95",
        "path_diversity",
        "partial_rate",
        "failure_rate",
        "fp_zero_clip_rate",
    ):
        lines.append(f"| {key} | {standard.get(key, '-')} | {investigator.get(key, '-')} |")
    lines += ["", "## Per-clip failures", ""]
    failures = [clip for clip in (investigator.get("clips") or []) if not clip.get("report")]
    if failures:
        lines.extend(f"- {clip['clip_id']}: {clip.get('status')}" for clip in failures)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def score_run(
    run_dir: str | Path,
    *,
    manifest_path: str | Path | None = None,
    labels_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compute metrics and write ``score.json`` plus ``report.md``."""
    run_dir = Path(run_dir).resolve()
    run = read_json(run_dir / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise BenchmarkError(f"run not found: {run_dir}")
    manifest_file = Path(manifest_path or run.get("manifest_path") or "").expanduser()
    if not manifest_file.is_file():
        raise BenchmarkError(f"manifest not found: {manifest_file}")
    manifest, problems = load_manifest(manifest_file, require_files=False, verify_checksums=False)
    if problems:
        raise BenchmarkError("invalid manifest:\n- " + "\n- ".join(problems))
    labels_file = Path(labels_path or run.get("labels_path") or manifest_file.parent / "labels.json").expanduser()
    labels = read_json(labels_file, {})
    labels = labels if isinstance(labels, dict) else {}
    label_problems = validate_labels(labels, manifest, require_all_clips=True)
    clips = clip_map(manifest)
    clip_ids = list(clips)
    required_clips = int(run.get("required_clips") or 8)
    required_raters = int(run.get("required_raters") or 2)
    complete_labels = not label_problems and labels_complete(manifest, labels)

    standard = _clip_results(run_dir=run_dir, manifest=manifest, labels=labels, mode="standard")
    investigator = _clip_results(run_dir=run_dir, manifest=manifest, labels=labels, mode="investigator")
    review = _evidence_review(run_dir, investigator)
    tool_review = _tool_review(run_dir, investigator)
    hallucination_review = _hallucination_review(run_dir, standard, investigator)
    stability = read_json(run_dir / "stability.json", {})
    stability = stability if isinstance(stability, dict) else {}
    coach = _coach_scores(run_dir=run_dir, clip_ids=clip_ids, required_raters=required_raters)
    environment = str(run.get("environment") or "local")
    negative_control = str(run.get("label") or "") == "negative-control"

    set_complete = len(clip_ids) >= required_clips
    ratings_complete = coach["raters_submitted"] >= required_raters
    latency_gate: bool | None = None
    if environment == "production" and standard["latency_p95"] and investigator["latency_p95"]:
        latency_gate = investigator["latency_p95"] <= 2 * standard["latency_p95"]
    elif environment == "production" and not standard["latency_p95"] and not investigator["latency_p95"]:
        latency_gate = False

    if not investigator["reports"]:
        evidence_gate: bool | None = None
    elif review["matched"] == 0:
        evidence_gate = investigator["evidence_integrity"] == 1.0
    elif not review["complete"]:
        evidence_gate = None
    else:
        evidence_gate = investigator["evidence_integrity"] == 1.0 and review["failures"] == 0

    gates: dict[str, bool | None] = {
        "evidence_integrity": evidence_gate,
        "coverage_honesty": investigator["coverage_honesty"] >= 0.9 if investigator["reports"] else None,
        "precision": investigator["precision"] >= standard["precision"] - 0.05
        if standard["reports"] and investigator["reports"]
        else None,
        "recall": investigator["recall"] >= standard["recall"]
        if standard["reports"] and investigator["reports"]
        else None,
        "cost": investigator["cost_median"] <= 2.5 * standard["cost_median"]
        if standard["reports"] and investigator["reports"]
        else None,
        "latency": _gate(latency_gate),
        "coach_preference": None,
        "path_diversity": investigator["path_diversity"] >= 3 if investigator["reports"] else None,
        "partial_rate": investigator["partial_rate"] <= 0.10 if investigator["reports"] else None,
        "failure_rate": investigator["failure_rate"] == 0 if investigator["reports"] else None,
        "tool_appropriateness": (
            tool_review["failures"] == 0
            if tool_review["matched"] and tool_review["complete"]
            else (True if tool_review["matched"] == 0 else None)
        ),
        "hallucination": (
            investigator["hallucination_rate"] <= standard["hallucination_rate"]
            if not hallucination_review["flagged"] and standard["reports"] and investigator["reports"]
            else (hallucination_review["confirmed"] == 0 if hallucination_review["complete"] else None)
        ),
        "stability": bool(stability.get("stable")) if environment == "production" and stability else None,
    }
    if ratings_complete and coach["non_tie"]:
        if coach["agreement"] >= 0.60 or coach["kappa"] > 0.40:
            gates["coach_preference"] = coach["preference"] >= 0.60
    blocked: list[str] = []
    if not set_complete:
        blocked.append("clips_incomplete")
    if not complete_labels:
        blocked.append("labels_incomplete")
    if not ratings_complete:
        blocked.append("ratings_incomplete")
    if environment != "production":
        blocked.append("latency_environment_not_production")
    for name, value in gates.items():
        if value is False:
            blocked.append(f"gate_failed:{name}")
        elif value is None:
            blocked.append(f"gate_blocked:{name}")
    if review["matched"] and not review["complete"]:
        blocked.append("evidence_review_incomplete")
    if tool_review["matched"] and not tool_review["complete"]:
        blocked.append("tool_review_incomplete")
    if hallucination_review["flagged"] and not hallucination_review["complete"]:
        blocked.append("hallucination_review_incomplete")
    if negative_control:
        blocked.append("negative_control")
    failed_gates = [name for name, value in gates.items() if value is False]
    release_eligible = bool(
        not negative_control
        and set_complete
        and complete_labels
        and ratings_complete
        and all(value is True for value in gates.values())
        and run.get("status") == "complete"
    )

    score: dict[str, Any] = {
        "version": 1,
        "run_id": run.get("run_id") or run_dir.name,
        "required_clips": required_clips,
        "clips": len(clip_ids),
        "required_raters": required_raters,
        "raters_submitted": coach["raters_submitted"],
        "labels_complete": complete_labels,
        "set_complete": set_complete,
        "environment": environment,
        "config_hash": run.get("config_hash"),
        "release_eligible": release_eligible,
        "blocked_reasons": blocked,
        "standard": standard,
        "investigator": investigator,
        "evidence_review": review,
        "tool_review": tool_review,
        "hallucination_review": hallucination_review,
        "stability": stability,
        "coach": {
            "investigator": coach["investigator"],
            "standard": coach["standard"],
            "ties": coach["ties"],
            "agreement": coach["agreement"],
            "kappa": coach["kappa"],
            "preference": coach["preference"],
        },
        "hallucination_rate": investigator["hallucination_rate"],
        "gates": gates,
        "negative_control": {
            "enabled": negative_control,
            "gates_failed": failed_gates,
            "sensitive": len(failed_gates) >= 3,
        },
        "pass": release_eligible,
    }
    score["score_updated_at"] = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    atomic_write_json(run_dir / "score.json", score)
    atomic_write_text(run_dir / "report.md", _report_markdown(score))
    write_combined_sheet(run_dir)
    run["score_status"] = "current"
    run["score_updated_at"] = score["score_updated_at"]
    run["release_eligible"] = release_eligible
    run["blocked_reasons"] = blocked
    atomic_write_json(run_dir / "run.json", run)
    return score


__all__ = ["FORBIDDEN", "score_run"]
