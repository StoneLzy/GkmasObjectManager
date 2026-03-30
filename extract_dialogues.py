"""
extract_dialogues.py
Simple CLI for exporting Gakumas dialogue scripts and voice lines.
"""

from __future__ import annotations

import json
from argparse import ArgumentParser
from pathlib import Path

import GkmasObjectManager as gom


PATTERN_PRESETS = {
    "produce-story": (
        "adv_pstory_001_{idol}_.*",
        "sud_vo_adv_pstory_001_{idol}_.*",
    ),
    "idol-card": (
        "adv_cidol-{idol}-.*",
        "sud_vo_adv_cidol-{idol}-.*",
    ),
    "dear": (
        "adv_dear_{idol}_.*",
        "sud_vo_adv_dear_{idol}_.*",
    ),
    "all-idol": (
        "adv_.*{idol}.*",
        "sud_vo_adv_.*{idol}.*",
    ),
    "event": (
        "adv_event_.*",
        "sud_vo_adv_event_.*",
    ),
    "unit": (
        "adv_unit_.*",
        "sud_vo_adv_unit_.*",
    ),
}


def require_idol_if_needed(pattern: str, idol: str) -> str:
    if "{idol}" not in pattern:
        return pattern
    if not idol:
        raise SystemExit("--idol is required for the selected preset unless you provide a custom pattern.")
    return pattern.format(idol=idol)


def derive_voice_pattern(script_pattern: str) -> str:
    if "sud_vo_adv_" in script_pattern:
        return script_pattern
    if "adv_" not in script_pattern:
        raise SystemExit("Cannot infer a voice pattern from --script-pattern. Please pass --voice-pattern explicitly.")

    return (
        script_pattern.replace("adv_", "sud_vo_adv_", 1)
        .replace(r"\.txt", r"\.acb")
        .replace(".txt", ".acb")
    )


def derive_script_pattern(voice_pattern: str) -> str:
    if voice_pattern.startswith("adv_"):
        return voice_pattern
    if "sud_vo_adv_" not in voice_pattern:
        raise SystemExit("Cannot infer a script pattern from --voice-pattern. Please pass --script-pattern explicitly.")

    return (
        voice_pattern.replace("sud_vo_", "", 1)
        .replace(r"\.acb", r"\.txt")
        .replace(".acb", ".txt")
    )


def build_patterns(args) -> tuple[str | None, str | None]:
    preset_script, preset_voice = PATTERN_PRESETS[args.kind]

    script_pattern = args.script_pattern
    voice_pattern = args.voice_pattern

    needs_scripts = args.mode in {"script", "both"} or args.captions
    needs_voice = args.mode in {"voice", "both"}

    if needs_scripts and not script_pattern:
        if voice_pattern and args.mode == "voice" and args.captions:
            script_pattern = derive_script_pattern(voice_pattern)
        else:
            script_pattern = require_idol_if_needed(preset_script, args.idol)

    if needs_voice and not voice_pattern:
        if script_pattern and args.script_pattern:
            voice_pattern = derive_voice_pattern(script_pattern)
        else:
            voice_pattern = require_idol_if_needed(preset_voice, args.idol)

    return script_pattern, voice_pattern


def select_matches(matches: list, latest_only: bool, limit: int | None) -> list:
    if not matches:
        return []
    if latest_only:
        return [matches[-1]]
    if limit is not None and limit > 0:
        return matches[-limit:]
    return matches


def find_matches(manifest, pattern: str | None, latest_only: bool, limit: int | None) -> list:
    if not pattern:
        return []
    matches = manifest.search(pattern, by_name=False, ascending=True)
    return select_matches(matches, latest_only=latest_only, limit=limit)


def export_scripts(objects: list, output_dir: Path, flat: bool, raw_script: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for obj in objects:
        obj.download(
            path=output_dir,
            categorize=not flat,
            convert_text=not raw_script,
        )


def export_voices(
    objects: list,
    output_dir: Path,
    flat: bool,
    raw_voice: bool,
    audio_format: str,
    keep_archive: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for obj in objects:
        kwargs = {
            "path": output_dir,
            "categorize": not flat,
        }
        if raw_voice:
            kwargs["convert_audio"] = False
        else:
            kwargs["audio_format"] = audio_format
            kwargs["unpack_subsongs"] = not keep_archive
        try:
            obj.download(**kwargs)
        except Exception as exc:
            print(
                f"Voice conversion failed for {obj.name}; raw archive fallback was kept if possible. "
                f"Reason: {exc}"
            )


def export_captions(objects: list, output_path: Path) -> None:
    caption_map = {}
    for obj in objects:
        media = obj.media
        if hasattr(media, "caption_map"):
            caption_map.update(media.caption_map)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(caption_map, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Caption map written to: {output_path}")


def print_selected(label: str, pattern: str | None, selected: list) -> None:
    if not pattern:
        return
    print(f"{label} pattern: {pattern}")
    print(f"{label} selected: {len(selected)}")
    for obj in selected:
        print(f"  - ID {obj.id:05}: {obj.name}")


def main() -> None:
    parser = ArgumentParser(description="Export Gakumas dialogue scripts and voice lines from the latest manifest.")
    parser.add_argument(
        "--idol",
        type=str,
        default="",
        help="Idol short code, for example hski / ttmr / fktn.",
    )
    parser.add_argument(
        "--kind",
        type=str,
        default="produce-story",
        choices=sorted(PATTERN_PRESETS),
        help="Built-in dialogue preset.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="script",
        choices=["script", "voice", "both"],
        help="Choose whether to export scripts, voices, or both.",
    )
    parser.add_argument(
        "--script-pattern",
        type=str,
        default="",
        help="Custom regex for adv_ script resources.",
    )
    parser.add_argument(
        "--voice-pattern",
        type=str,
        default="",
        help="Custom regex for sud_vo_adv_ voice resources.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="out/dialogues",
        help="Base output directory.",
    )
    parser.add_argument(
        "--audio-format",
        type=str,
        default="wav",
        help="Voice export format, usually wav or mp3.",
    )
    parser.add_argument(
        "--raw-script",
        action="store_true",
        help="Export raw .txt scripts instead of parsed JSON.",
    )
    parser.add_argument(
        "--raw-voice",
        action="store_true",
        help="Export raw .acb archives instead of converting audio.",
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Keep converted multi-track voice archives as .zip instead of unpacking them.",
    )
    parser.add_argument(
        "--captions",
        action="store_true",
        help="Also export a captions.json map built from matched scripts.",
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
        help="Export only the newest matched object on each side.",
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

    script_pattern, voice_pattern = build_patterns(args)
    base_output = Path(args.out)
    base_output.mkdir(parents=True, exist_ok=True)

    print("Fetching manifest...")
    manifest = gom.fetch(pc=args.pc)
    print(f"Fetched revision: {manifest.revision.canon_repr}")

    selected_scripts = find_matches(
        manifest,
        script_pattern,
        latest_only=args.latest_only,
        limit=args.limit or None,
    )
    selected_voices = find_matches(
        manifest,
        voice_pattern,
        latest_only=args.latest_only,
        limit=args.limit or None,
    )

    print_selected("Script", script_pattern, selected_scripts)
    print_selected("Voice", voice_pattern, selected_voices)

    if args.dry_run:
        return

    if args.mode in {"script", "both"} and selected_scripts:
        script_dir = base_output / "scripts" if args.mode == "both" else base_output
        export_scripts(
            selected_scripts,
            output_dir=script_dir,
            flat=args.flat,
            raw_script=args.raw_script,
        )

    if args.mode in {"voice", "both"} and selected_voices:
        voice_dir = base_output / "voices" if args.mode == "both" else base_output
        export_voices(
            selected_voices,
            output_dir=voice_dir,
            flat=args.flat,
            raw_voice=args.raw_voice,
            audio_format=args.audio_format,
            keep_archive=args.keep_archive,
        )

    if args.captions and selected_scripts:
        export_captions(selected_scripts, base_output / "captions.json")


if __name__ == "__main__":
    main()
