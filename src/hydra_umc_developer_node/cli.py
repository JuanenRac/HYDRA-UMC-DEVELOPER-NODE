# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/cli.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The command line: `hydra-umc-developer-node <group> <command>`.

Exit codes: 0 done, 1 refused (a closed switch, a missing approval, a check that failed), 2 wrong usage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from . import __version__, approvals, evidence, panel, plugin_ci, plugin_full, repro
from .checkouts import CheckoutCache, CheckoutError
from .i18n import t
from .redaction import redact
from .schema import SchemaError
from .settings import LANGUAGES, Settings, SettingsError, load_settings
from .store import Store, StoreError

REFUSALS = (SettingsError, evidence.EvidenceError, approvals.ApprovalError, repro.ReproError, CheckoutError, plugin_ci.PluginError,
            panel.PanelError, StoreError, SchemaError)


def _print_json(document: Any) -> None:
    print(json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False))


def _store(settings: Settings) -> Store:
    return Store(settings.data_path() / "node.sqlite")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hydra-umc-developer-node", description="Developer node of the HYDRA-UMC ecosystem; every part is closed by default.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", help="the configuration file (JSON); without it every switch is closed")
    parser.add_argument("--lang", choices=LANGUAGES, help="the language of the messages (default: language of the configuration)")
    groups = parser.add_subparsers(dest="group", required=True)

    config = groups.add_parser("config", help="check or show the configuration").add_subparsers(dest="command", required=True)
    config.add_parser("check", help="validate the configuration and list the closed switches")
    config.add_parser("show", help="print the effective configuration switches")

    ev = groups.add_parser("evidence", help="evidence bundles of the local technician").add_subparsers(dest="command", required=True)
    verify = ev.add_parser("verify", help="check a bundle file (read only; stores nothing)")
    verify.add_argument("file")
    ingest = ev.add_parser("ingest", help="check a bundle or a signed transport message and store it as a case")
    ingest.add_argument("file")

    case = groups.add_parser("case", help="stored cases").add_subparsers(dest="command", required=True)
    case.add_parser("list")
    show = case.add_parser("show")
    show.add_argument("case_id")

    rp = groups.add_parser("repro", help="repro recipes").add_subparsers(dest="command", required=True)
    rp_check = rp.add_parser("check", help="validate a recipe and print its digest")
    rp_check.add_argument("recipe")
    rp_approve = rp.add_parser("approve", help="a person approves the exact digest of a recipe for a case (needs a terminal)")
    rp_approve.add_argument("case_id")
    rp_approve.add_argument("recipe")
    rp_run = rp.add_parser("run", help="run an approved recipe (the approval is used up)")
    rp_run.add_argument("case_id")
    rp_run.add_argument("recipe")
    rp_run.add_argument("--phase", choices=("before", "after"), required=True)
    where = rp_run.add_mutually_exclusive_group(required=True)
    where.add_argument("--checkout", nargs=3, metavar=("NAME", "REMOTE", "REV"), help="run in the cached checkout of this revision")
    where.add_argument("--workdir", help="run in this folder (needs --fingerprint)")
    rp_run.add_argument("--fingerprint", help="the identifier of the source state when --workdir is used")
    rp_compare = rp.add_parser("compare", help="the verdict of the stored before and after runs (computed by the SDK)")
    rp_compare.add_argument("case_id")
    rp_compare.add_argument("scenario_id")

    co = groups.add_parser("checkout", help="the cache of checkouts by revision").add_subparsers(dest="command", required=True)
    fetch = co.add_parser("fetch", help="make (or reuse) the worktree of a revision")
    fetch.add_argument("name")
    fetch.add_argument("remote")
    fetch.add_argument("rev")
    co.add_parser("list")
    co.add_parser("prune", help="remove the least recently used worktrees until the cache fits its limit")

    pn = groups.add_parser("panel", help="the status document for a dashboard").add_subparsers(dest="command", required=True)
    pn.add_parser("status")
    pn.add_parser("export", help="write <dataDir>/panel/status.json")

    pl = groups.add_parser("plugin", help="plugins").add_subparsers(dest="command", required=True)
    pl.add_parser("list")
    pl.add_parser("plan", help="print the plan of the ecosystem-ci plugin and its digest")
    pl.add_parser("approve", help="a person approves the plan (needs a terminal)")
    pl.add_parser("run", help="run the approved plan and print the consolidated report")
    for name, text in (("full-plan", "print the plan of the complete mode (every command, repository by repository) and its digest"),
                       ("full-approve", "a person approves the whole batch by its digest (needs a terminal)"),
                       ("full-run", "run the approved batch one repository at a time and print the consolidated report")):
        full = pl.add_parser(name, help=text)
        full.add_argument("--exclude", action="append", default=[], metavar="REPO", help="leave this repository out of the batch (repeatable)")
    return parser


def _config(settings: Settings, args: argparse.Namespace) -> int:
    closed = ", ".join(name for name, on in settings.switches().items() if not on) or t("label.none", args.lang)
    if args.command == "check":
        print(t("msg.config_ok", args.lang, closed=closed))
    else:
        _print_json({"dataDir": settings.data_dir, "language": settings.language, "switches": settings.switches()})
    return 0


def _evidence(settings: Settings, args: argparse.Namespace) -> int:
    path = Path(args.file)
    if args.command == "verify":
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise evidence.EvidenceError("cannot read the file as JSON") from error
        print(t("msg.bundle_ok", args.lang, steps=len(evidence.verify_bundle(document))))
        return 0
    with _store(settings) as store:
        case_id, created = evidence.ingest(path, settings.ingest, store, os.environ)
    print(t("msg.ingested" if created else "msg.duplicate", args.lang, case=case_id))
    return 0


def _case(settings: Settings, args: argparse.Namespace) -> int:
    with _store(settings) as store:
        if args.command == "list":
            cases = store.list_cases()
            if not cases:
                print(t("msg.no_cases", args.lang))
            for item in cases:
                print(f"{item['id']}\t{item['status']}\t{item['source']}\t{item['checksum'][:12]}")
        else:
            _print_json(store.get_case(args.case_id))
    return 0


def _repro(settings: Settings, args: argparse.Namespace) -> int:
    if args.command == "compare":
        with _store(settings) as store:
            _print_json(repro.compare(store, args.case_id, args.scenario_id))
        return 0
    recipe = repro.load_recipe(Path(args.recipe), settings.repro)
    digest = approvals.digest_of(recipe)
    if args.command == "check":
        print(digest)
        return 0
    with _store(settings) as store:
        if args.command == "approve":
            store.get_case(args.case_id)
            approvals.approve(store, args.case_id, repro.ACTION, digest)
            print(t("msg.approved", args.lang, what=f"{recipe['scenario_id']} {digest[:12]}"))
            return 0
        if args.checkout:
            name, remote, rev = args.checkout
            workdir, fingerprint = CheckoutCache(settings.checkouts, settings.data_path()).checkout(name, remote, rev)
        else:
            if not args.fingerprint:
                raise repro.ReproError("--workdir needs --fingerprint")
            workdir, fingerprint = Path(args.workdir), args.fingerprint
        document = repro.run_recipe(recipe, store, settings.repro, args.case_id, args.phase, workdir, fingerprint)
    print(t("msg.run_outcome", args.lang, phase=args.phase, outcome=document["observed"]["outcome"]))
    _print_json(document)
    return 0


def _checkout(settings: Settings, args: argparse.Namespace) -> int:
    cache = CheckoutCache(settings.checkouts, settings.data_path())
    if args.command == "fetch":
        path, sha = cache.checkout(args.name, args.remote, args.rev)
        print(t("msg.checkout_ready", args.lang, path=path, sha=sha))
    elif args.command == "list":
        _print_json({"entries": cache.entries(), "bytes": cache.size_bytes(), "limit_bytes": settings.checkouts.max_cache_bytes})
    else:
        removed = cache.prune()
        print(t("msg.pruned", args.lang, count=len(removed)))
        if cache.over_limit():
            print(t("msg.cache_over", args.lang))
            return 1
    return 0


def _panel(settings: Settings, args: argparse.Namespace) -> int:
    with _store(settings) as store:
        if args.command == "status":
            _print_json(panel.build_status(settings, store))
        else:
            print(panel.export_status(settings, store))
    return 0


def _plugin(settings: Settings, args: argparse.Namespace) -> int:
    if args.command == "list":
        _print_json([{"name": plugin_ci.NAME, "enabled": settings.ecosystem_ci.enabled}])
        return 0
    if args.command.startswith("full-"):
        return _plugin_full(settings, args)
    plan = plugin_ci.build_plan(settings.ecosystem_ci)
    digest = plugin_ci.plan_digest(plan)
    if args.command == "plan":
        _print_json({"plan": plan, "sha256": digest})
        return 0
    with _store(settings) as store:
        if args.command == "approve":
            approvals.approve(store, plugin_ci.SUBJECT, plugin_ci.ACTION, digest)
            print(t("msg.approved", args.lang, what=f"{plugin_ci.NAME} {digest[:12]}"))
            return 0
        report = plugin_ci.run(plan, store, settings.ecosystem_ci, settings.data_path())
    summary = report["summary"]
    print(t("msg.ci_done", args.lang, passed=summary["pass"], failed=summary["fail"], errors=summary["error"], skipped=summary["skipped"]))
    return 0 if summary["fail"] == 0 and summary["error"] == 0 else 1


def _plugin_full(settings: Settings, args: argparse.Namespace) -> int:
    exclude = tuple(args.exclude)
    plan = plugin_full.build_plan(settings.ecosystem_ci, settings.ecosystem_ci_full, exclude)
    digest = plugin_full.plan_digest(plan)
    if args.command == "full-plan":
        _print_json({"plan": plan, "sha256": digest})
        for line in plugin_full.describe(plan):
            print(line)
        print(t("msg.full_plan_hint", args.lang))
        return 0
    with _store(settings) as store:
        if args.command == "full-approve":
            if not settings.ecosystem_ci_full.enabled:
                raise plugin_ci.PluginError("ecosystemCiFull is closed: set ecosystemCiFull.enabled to true in the configuration file")
            for line in plugin_full.describe(plan):
                print(line)
            approvals.approve(store, plugin_full.SUBJECT, plugin_full.ACTION, digest)
            print(t("msg.approved", args.lang, what=f"{plugin_full.NAME} {digest[:12]}"))
            return 0
        report = plugin_full.run(plan, store, settings.ecosystem_ci, settings.ecosystem_ci_full, settings.data_path(), exclude)
    for item in report["results"]:
        print(t("msg.full_line", args.lang, repo=item["repo"], status=t(f"label.status_{item['status']}", args.lang), seconds=item["seconds"],
                command=item["command"] or "-"))
    summary = report["summary"]
    print(t("msg.full_done", args.lang, passed=summary["pass"], failed=summary["fail"], timeouts=summary["timeout"], skipped=summary["skipped"]))
    if report["aborted"]:
        print(t("msg.full_aborted", args.lang, reason=report["aborted"]))
    return plugin_full.exit_code(report)


HANDLERS: dict[str, Callable[[Settings, argparse.Namespace], int]] = {
    "config": _config, "evidence": _evidence, "case": _case, "repro": _repro, "checkout": _checkout, "panel": _panel, "plugin": _plugin,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(args.config)
        args.lang = args.lang or settings.language
        return HANDLERS[args.group](settings, args)
    except REFUSALS as error:
        print(t("msg.refused", getattr(args, "lang", "en") or "en", reason=redact(str(error))), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
