"""Configuration, integrity checks and validation. No network or incident analysis."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import math
import re

METRICS = (
    ("01_annual_incidents", "各服务年度事故数量", "事故记录数（起）", "incident_count"),
    ("02_incidents_per_30_days", "每 30 天事故频次", "事故记录数 / 30 天", "incidents_per_30_days"),
    ("03_full_hours", "年度影响时长：仅全部中断", "影响时间并集（小时）", "full_hours"),
    ("04_full_partial_hours", "年度影响时长：全部＋部分中断", "影响时间并集（小时）", "full_partial_hours"),
    ("05_all_hours", "年度影响时长：全部三个等级", "影响时间并集（小时）", "all_hours"),
    ("06_availability_full", "年度可用性：仅扣除全部中断", "可用性估计（%）", "availability_full"),
    ("07_availability_full_partial", "年度可用性：扣除全部＋部分中断", "可用性估计（%）", "availability_full_partial"),
    ("08_availability_all", "年度可用性：扣除全部三个等级", "可用性估计（%）", "availability_all"),
)
HOURS = ("full_hours", "full_partial_hours", "all_hours")
AVAILABILITY = ("availability_full", "availability_full_partial", "availability_all")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def timestamp(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid ISO timestamp: {value!r}") from exc
    require(result.tzinfo is not None, f"Timestamp needs an explicit timezone: {value!r}")
    return result.astimezone(timezone.utc)


def number(value: Any, name: str, *, integer: bool = False) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0, f"{name}: expected a finite non-negative number")
    require(not integer or value == int(value), f"{name}: expected an integer")
    return float(value)


def relative_path(value: str) -> Path:
    require(isinstance(value, str) and bool(value), "Expected a non-empty relative path")
    require(not any(x in value for x in ("\\", ":", "\x00", "\n", "\r")), f"Unsafe path: {value!r}")
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts and path.parts != (), f"Unsafe path: {value!r}")
    return path


def child(root: Path, value: str) -> Path:
    path = (root / relative_path(value)).resolve()
    require(path.is_relative_to(root.resolve()), f"Path escapes its directory: {value}")
    return path


def checked_bytes(path: Path, expected: str | None, label: str) -> bytes:
    result = path.read_bytes()
    if expected is not None:
        require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
                f"{label}: SHA-256 must be 64 lower-case hex characters")
        require(sha256(result) == expected, f"{label}: SHA-256 mismatch; input has not been modified")
    return result


def normalize_rows(rows: list[dict], groups: list[str], cutoff: datetime, *, annual: bool) -> list[dict]:
    require(isinstance(rows, list), "Rows must be an array")
    normalized: list[dict] = []
    seen: set[tuple] = set()
    for raw in rows:
        require(isinstance(raw, dict), "Every row must be an object")
        row = dict(raw)
        year, group = row.get("year"), row.get("group")
        require(type(year) is int and 1900 <= year < 9999, "Row year must be an integer in [1900, 9998]")
        require(group in groups, f"Unconfigured service group: {group!r}")
        require((year, group) not in seen, f"Duplicate year/group: {year}/{group}")
        seen.add((year, group))
        prefix = f"{year}/{group}"
        if row.get("incident_count") is None:
            require(row.get("denominator_seconds", 0) in (0, None), f"{prefix}: missing count in an active window")
            require(all(row.get(k) is None for k in (*HOURS, *AVAILABILITY, "incidents_per_30_days")),
                    f"{prefix}: unavailable service must not be represented as zero downtime or 100% uptime")
            row.update(partial_year=None, observation_days=0.0, incidents_per_30_days=None)
            normalized.append(row)
            continue
        number(row["incident_count"], f"{prefix}/incident_count", integer=True)
        start, end = timestamp(row.get("window_start")), timestamp(row.get("window_end"))
        require(start < end <= cutoff, f"{prefix}: window must be positive and not exceed the data cutoff")
        year_start = datetime(year, 1, 1, tzinfo=timezone.utc)
        year_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        require(year_start <= start < end <= year_end, f"{prefix}: window must lie within the specified UTC year")
        seconds = (end - start).total_seconds()
        if "denominator_seconds" in row:
            number(row["denominator_seconds"], f"{prefix}/denominator_seconds")
            require(math.isclose(row["denominator_seconds"], seconds, abs_tol=0.01), f"{prefix}: denominator does not match its window")
        days = seconds / 86400
        if "observation_days" in row:
            number(row["observation_days"], f"{prefix}/observation_days")
            require(math.isclose(row["observation_days"], days, abs_tol=1e-6), f"{prefix}: observation_days mismatch")
        partial = start != year_start or end != year_end
        if annual and "partial_year" in row:
            require(type(row["partial_year"]) is bool and row["partial_year"] == partial,
                    f"{prefix}: partial_year does not match its window")
        hours = [number(row.get(key), f"{prefix}/{key}") for key in HOURS]
        require(hours[0] <= hours[1] + 1e-7 and hours[1] <= hours[2] + 1e-7
                and hours[2] <= seconds / 3600 + 1e-7, f"{prefix}: invalid nested downtime unions")
        for key, duration in zip(AVAILABILITY, hours):
            value = number(row.get(key), f"{prefix}/{key}")
            require(value <= 1 and math.isclose(value, 1 - duration * 3600 / seconds, abs_tol=1e-8),
                    f"{prefix}/{key}: expected a ratio in [0,1] consistent with downtime")
        rate = row["incident_count"] * 30 / days
        if row.get("incidents_per_30_days") is not None:
            number(row["incidents_per_30_days"], f"{prefix}/incidents_per_30_days")
            require(math.isclose(row["incidents_per_30_days"], rate, abs_tol=1e-6), f"{prefix}: normalized frequency mismatch")
        if "unknown_time_count" in row:
            require(number(row["unknown_time_count"], f"{prefix}/unknown_time_count", integer=True) <= row["incident_count"],
                    f"{prefix}: unknown count exceeds total")
        row.update(denominator_seconds=seconds, observation_days=days, partial_year=partial, incidents_per_30_days=rate)
        normalized.append(row)
    return normalized


def validate_matches(rows: list[dict]) -> None:
    """Compare month/day/time and counting basis, not just the number of days."""
    for group in {r["group"] for r in rows}:
        active = [r for r in rows if r["group"] == group and r.get("incident_count") is not None]
        signatures = set()
        for row in active:
            bounds = [timestamp(row[key]).strftime("%m-%dT%H:%M:%S.%f") for key in ("window_start", "window_end")]
            basis = row.get("count_basis")
            require(isinstance(basis, str) and bool(basis), f"{group}: matched comparison requires count_basis")
            signatures.add((*bounds, basis))
        require(len(signatures) <= 1, f"{group}: matched windows differ in calendar boundaries or count basis")


@dataclass
class Report:
    config_path: Path
    config: dict
    data: dict
    markdown_path: Path
    data_path: Path
    markdown_bytes: bytes
    data_bytes: bytes
    groups: list[dict]
    annual: list[dict]
    matched: list[dict]
    years: list[int]
    cutoff: datetime

    @property
    def company(self) -> str:
        return self.config["company"]["name"]

    @property
    def stem(self) -> str:
        return self.config["output"]["stem"]

    @property
    def output(self) -> Path:
        return self.config_path.parent / self.config["output"]["directory"]


def load_report(path: Path) -> Report:
    path = path.resolve()
    cfg = json.loads(path.read_text(encoding="utf-8"))
    require(cfg.get("schema_version") == 1, "Unsupported configuration schema_version")
    require(type(cfg.get("synthetic", False)) is bool, "synthetic must be a boolean")
    for section in ("company", "report", "inputs", "output"):
        require(isinstance(cfg.get(section), dict), f"Missing configuration section: {section}")
    for section, keys in {"company": ("id", "name"), "report": ("date", "version", "title"),
                          "inputs": ("markdown", "data"), "output": ("directory", "stem")}.items():
        for key in keys:
            require(isinstance(cfg[section].get(key), str) and bool(cfg[section][key].strip()), f"Missing {section}.{key}")
    date.fromisoformat(cfg["report"]["date"])
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", cfg["company"]["id"]) is not None, "Invalid company.id")
    output = cfg["output"]
    require(len(relative_path(output["stem"]).parts) == 1, "output.stem must be a filename stem")
    output.setdefault("charts_directory", "charts")
    output.setdefault("overview_counts_file", "annual_incidents.png")
    output.setdefault("overview_modes_file", "availability_modes.png")
    relative_path(output["charts_directory"])
    for key in ("overview_counts_file", "overview_modes_file"):
        require(relative_path(output[key]).suffix == ".png", f"{key} must be a relative PNG filename")
    require(output["overview_counts_file"] != output["overview_modes_file"], "Overview filenames must differ")
    integrity = cfg.get("integrity", {})
    require(isinstance(integrity, dict), "integrity must be an object")
    md_path = (path.parent / cfg["inputs"]["markdown"]).resolve()
    data_path = (path.parent / cfg["inputs"]["data"]).resolve()
    md = checked_bytes(md_path, integrity.get("markdown_sha256"), "Markdown")
    raw = checked_bytes(data_path, integrity.get("data_sha256"), "Trend data")
    md.decode("utf-8")
    data = json.loads(raw)
    require(data.get("schema_version", 1) == 1, "Unsupported trend data schema_version")
    cutoff = timestamp(data.get("cutoff_utc"))
    groups = cfg.get("groups")
    require(isinstance(groups, list) and len(groups) > 0, "At least one configured service group is required")
    for group in groups:
        require(isinstance(group, dict) and isinstance(group.get("id"), str) and bool(group["id"])
                and isinstance(group.get("label"), str) and bool(group["label"]), "Each group requires id and label")
    ids = [g["id"] for g in groups]
    require(len(set(ids)) == len(ids), "Duplicate configured group IDs")
    require(cfg.get("overall_group") in ids, "overall_group must identify a configured group")
    overview = cfg.get("overview_groups", [g for g in ids if g != cfg["overall_group"]] or ids)
    require(isinstance(overview, list) and bool(overview) and len(set(overview)) == len(overview)
            and all(g in ids for g in overview), "Invalid overview_groups")
    cfg["overview_groups"] = overview
    annual = normalize_rows(data.get("annual"), ids, cutoff, annual=True)
    require(any(r.get("incident_count") is not None for r in annual), "Annual data has no observed service windows")
    require(any(r["group"] == cfg["overall_group"] and r.get("incident_count") is not None for r in annual),
            "overall_group has no observed data")
    matched = normalize_rows(data.get("matched_windows", []), ids, cutoff, annual=False)
    validate_matches(matched)
    years = list(range(min(r["year"] for r in annual), max(r["year"] for r in annual) + 1))
    require(len(years) <= 100, "Annual span exceeds 100 years")
    return Report(path, cfg, data, md_path, data_path, md, raw, groups, annual, matched, years, cutoff)
