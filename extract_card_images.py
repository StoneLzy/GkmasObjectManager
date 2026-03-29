"""
extract_card_images.py
Simple CLI for exporting Gakumas card images with GkmasObjectManager.
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import GkmasObjectManager as gom


PATTERN_PRESETS = {
    "full": "img_general_cidol-{idol}.*full",
    "portrait": "img_general_cidol-{idol}.*thumb-portrait",
    "landscape": "img_general_cidol-{idol}.*thumb-landscape-large",
    "all": "img_general_cidol-{idol}.*(full|thumb-portrait|thumb-landscape-large)",
    "support-full": "img_general_csprt.*full",
    "support-thumb": "img_general_csprt.*thumb-(landscape|square)",
}


def build_pattern(args) -> str:
    if args.pattern:
        return args.pattern

    if args.kind.startswith("support"):
        return PATTERN_PRESETS[args.kind]

    if not args.idol:
        raise SystemExit("--idol is required unless --pattern is provided.")

    return PATTERN_PRESETS[args.kind].format(idol=args.idol)


def select_matches(matches: list, latest_only: bool, limit: int | None) -> list:
    if not matches:
        return []

    if latest_only:
        return [matches[-1]]

    if limit is not None and limit > 0:
        return matches[-limit:]

    return matches


def main() -> None:
    parser = ArgumentParser(description="Export Gakumas card images from the latest manifest.")
    parser.add_argument(
        "--idol",
        type=str,
        default="",
        help="Idol short code, for example hski / ttmr / fktn.",
    )
    parser.add_argument(
        "--kind",
        type=str,
        default="full",
        choices=sorted(PATTERN_PRESETS),
        help="Built-in card image preset.",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="",
        help="Custom regex. Overrides --idol and --kind if provided.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="out/cards",
        help="Output directory.",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        help="Export format, usually png or jpeg.",
    )
    parser.add_argument(
        "--resize",
        type=str,
        default="",
        help="Optional resize ratio such as 9:16 or 16:9.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Keep only the newest N matches by object ID. 0 means no limit.",
    )
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Download only the newest matched card.",
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Do not auto-create nested subdirectories.",
    )
    parser.add_argument(
        "--pc",
        action="store_true",
        help="Use the PC manifest API instead of the mobile one.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list matches, do not download files.",
    )
    args = parser.parse_args()

    pattern = build_pattern(args)
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching manifest...")
    manifest = gom.fetch(pc=args.pc)
    print(f"Fetched revision: {manifest.revision.canon_repr}")
    print(f"Search pattern: {pattern}")

    matches = manifest.search(pattern, by_name=False, ascending=True)
    selected = select_matches(
        matches,
        latest_only=args.latest_only,
        limit=args.limit or None,
    )

    print(f"Matched {len(matches)} object(s); selected {len(selected)} for export.")
    for obj in selected:
        print(f"  - ID {obj.id:05}: {obj.name}")

    if args.dry_run or not selected:
        return

    download_kwargs = {
        "path": output_dir,
        "categorize": not args.flat,
        "image_format": args.format,
    }
    if args.resize:
        download_kwargs["image_resize"] = args.resize

    # Keep the script easy to read: download the chosen objects one by one.
    for obj in selected:
        obj.download(**download_kwargs)


if __name__ == "__main__":
    main()
