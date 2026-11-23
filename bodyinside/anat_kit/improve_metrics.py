"""Join the first 48 h of audience evidence to the published anatomy edition."""

import os
from pathlib import Path

from improvement_log import ARCHIVE, finding, read


def ingest():
    work = ARCHIVE.parent
    ledger = Path(os.environ.get("FACTORY_LEDGER", work / "upload/ledger.json"))
    if not ledger.is_file():
        return []
    daily = Path(os.environ.get("ANAT_ANALYTICS", work / "channel/analytics/daily"))
    api, studio = {}, {}
    for path in sorted(daily.glob("api_*_anatomy*.json")):
        for row in read(path).get("first_48h", []):
            if row.get("views", 0) > 0:
                api[row["video_id"]] = (row, path.name)
    for path in sorted(daily.glob("????-??-??.json")):
        for row in read(path).get("videos", []):
            if row.get("metric_period") == "first_48h":
                studio[row["video_id"]] = (row, path.name)

    findings = []
    for entry in read(ledger)["entries"]:
        if entry.get("channel") != "anatomy" or entry.get("state") not in (
            "published",
            "scheduled",
        ):
            continue
        vid = entry["video_id"]
        report, pull = api.get(vid, ({}, None))
        observed, snapshot = studio.get(vid, ({}, None))
        if entry["state"] == "scheduled" and not report.get("published_at"):
            continue
        if not (report or observed):
            continue
        folder = work / entry.get("pkg", entry["qid"])
        ep = (
            read(folder / "episode.json") if (folder / "episode.json").is_file() else {}
        )
        version = entry.get("template_version") or ep.get("template_version")
        hook = entry.get("hook_type") or ep.get("hook_type")
        metrics = dict(
            swipe_through_pct=observed.get("viewed_pct"),
            avg_view_pct=observed.get("average_percentage_viewed"),
            subscriber_conversion_pct=None,
            engaged_share_pct=None,
        )
        sources = {k: snapshot for k, v in metrics.items() if v is not None}
        if observed.get("views") and observed.get("subscribers_net") is not None:
            metrics["subscriber_conversion_pct"] = (
                100 * observed["subscribers_net"] / observed["views"]
            )
            sources["subscriber_conversion_pct"] = snapshot
        if report:
            views = report["views"]
            metrics["engaged_share_pct"] = 100 * report["engagedViews"] / views
            if metrics["avg_view_pct"] is None:
                metrics["avg_view_pct"] = report["averageViewPercentage"]
            if (
                metrics["subscriber_conversion_pct"] is None
                and report.get("subscribersLost") is not None
            ):
                metrics["subscriber_conversion_pct"] = (
                    100
                    * (report["subscribersGained"] - report["subscribersLost"])
                    / views
                )
            sources.update(
                {
                    k: pull
                    for k, v in metrics.items()
                    if k not in sources and v is not None
                }
            )
        if not sources:
            continue
        findings.append(
            finding(
                ep.get("id", folder.name),
                "metric",
                "First 48 h of audience measurements",
                "info",
                "first 48h",
                vid,
                video_id=vid,
                template=entry.get("template") or ep.get("template"),
                template_version=version,
                hook_type=hook,
                metrics=metrics,
                sources=sources,
                published_at=report.get("published_at") or entry.get("publish_at"),
                api_reporting_days=[report["start"], report["end"]] if report else None,
            )
        )
    return findings


def experiment(metrics):
    if not metrics:
        return "Next experiment awaits a published episode with 48 h data."
    metrics = [r for r in metrics if r.get("template_version") and r.get("hook_type")]
    if not metrics:
        return "Record the published template version and hook type before selecting an experiment."
    latest = max(metrics, key=lambda r: r.get("published_at") or r["ref"])
    options = [
        ("swipe_through_pct", "opening framing", "swipe-through"),
        ("engaged_share_pct", "opening framing", "engaged-view share"),
        ("avg_view_pct", "shot duration", "average view percentage"),
        (
            "subscriber_conversion_pct",
            "closing question timing",
            "net subscriber conversion",
        ),
    ]
    for field, variable, label in options:
        value = latest["metrics"].get(field)
        if value is not None:
            return (
                f"On {latest.get('template') or latest['episode']} {latest['template_version']} "
                f"with the {latest['hook_type']} hook, change only {variable} and compare "
                f"{label} with {value:.1f}%."
            )
    return "Next experiment awaits a measured outcome."
