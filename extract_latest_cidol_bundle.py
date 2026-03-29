"""
extract_latest_cidol_bundle.py
Export the latest idol card image together with its matching scripts and voice lines.
"""

from __future__ import annotations

import json
from argparse import ArgumentParser
from pathlib import Path

import GkmasObjectManager as gom


def find_latest_card(manifest, idol: str) -> object:
    pattern = rf"img_general_cidol-{idol}.*full" if idol else r"img_general_cidol.*full"
    matches = manifest.search(pattern, by_name=False, ascending=True)
    if not matches:
        scope = idol or "all idols"
        raise SystemExit(f"No full idol card images found for {scope}.")
    return matches[-1]


def derive_story_base(card_name: str) -> str:
    return (
        card_name.removeprefix("img_general_")
        .removesuffix("_1-full.unity3d")
        .removesuffix("-full.unity3d")
    )


def find_story_assets(manifest, story_base: str) -> tuple[list, list]:
    script_pattern = rf"adv_{story_base}_.*"
    voice_pattern = rf"sud_vo_adv_{story_base}_.*"

    scripts = manifest.search(script_pattern, by_name=False, ascending=True)
    voices = manifest.search(voice_pattern, by_name=False, ascending=True)
    return scripts, voices


def export_card(card, output_dir: Path, image_format: str, image_resize: str) -> None:
    kwargs = {
        "path": output_dir,
        "categorize": False,
        "image_format": image_format,
    }
    if image_resize:
        kwargs["image_resize"] = image_resize
    card.download(**kwargs)


def export_scripts(scripts: list, output_dir: Path, raw_script: bool) -> None:
    for obj in scripts:
        obj.download(
            path=output_dir,
            categorize=False,
            convert_text=not raw_script,
        )


def export_voices(
    voices: list,
    output_dir: Path,
    raw_voice: bool,
    audio_format: str,
    keep_archive: bool,
) -> None:
    for obj in voices:
        kwargs = {
            "path": output_dir,
            "categorize": False,
        }
        if raw_voice:
            kwargs["convert_audio"] = False
        else:
            kwargs["audio_format"] = audio_format
            kwargs["unpack_subsongs"] = not keep_archive
        obj.download(**kwargs)


def export_captions(scripts: list, output_path: Path) -> None:
    caption_map = {}
    for obj in scripts:
        media = obj.media
        if hasattr(media, "caption_map"):
            caption_map.update(media.caption_map)

    output_path.write_text(
        json.dumps(caption_map, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    parser = ArgumentParser(
        description="Export the latest idol card image with its matching script and voice assets."
    )
    parser.add_argument(
        "--idol",
        type=str,
        default="",
        help="Optional idol short code. If omitted, use the latest idol card across all idols.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="out/latest_cidol_bundle",
        help="Base output directory.",
    )
    parser.add_argument(
        "--image-format",
        type=str,
        default="png",
        help="Card image export format, usually png or jpeg.",
    )
    parser.add_argument(
        "--image-resize",
        type=str,
        default="",
        help="Optional card image resize ratio such as 9:16.",
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
        help="Export raw .acb voice archives instead of converted audio.",
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Keep converted multi-track voice exports as .zip instead of unpacking them.",
    )
    parser.add_argument(
        "--pc",
        action="store_true",
        help="Use the PC manifest API instead of the mobile one.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the resolved latest card and related assets.",
    )
    args = parser.parse_args()

    base_output = Path(args.out)
    base_output.mkdir(parents=True, exist_ok=True)

    print("Fetching manifest...")
    manifest = gom.fetch(pc=args.pc)
    print(f"Fetched revision: {manifest.revision.canon_repr}")

    card = find_latest_card(manifest, idol=args.idol)
    story_base = derive_story_base(card.name)
    scripts, voices = find_story_assets(manifest, story_base)

    bundle_root = base_output / story_base
    card_dir = bundle_root / "card"
    script_dir = bundle_root / "scripts"
    voice_dir = bundle_root / "voices"
    captions_path = bundle_root / "captions.json"

    print(f"Latest card: ID {card.id:05} {card.name}")
    print(f"Story base: {story_base}")
    print(f"Bundle root: {bundle_root}")
    print(f"Scripts matched: {len(scripts)}")
    for obj in scripts:
        print(f"  - ID {obj.id:05}: {obj.name}")
    print(f"Voices matched: {len(voices)}")
    for obj in voices:
        print(f"  - ID {obj.id:05}: {obj.name}")

    if args.dry_run:
        return

    card_dir.mkdir(parents=True, exist_ok=True)
    script_dir.mkdir(parents=True, exist_ok=True)
    voice_dir.mkdir(parents=True, exist_ok=True)

    export_card(
        card,
        output_dir=card_dir,
        image_format=args.image_format,
        image_resize=args.image_resize,
    )
    if scripts:
        export_scripts(scripts, output_dir=script_dir, raw_script=args.raw_script)
        export_captions(scripts, captions_path)
        print(f"Caption map written to: {captions_path}")
    if voices:
        export_voices(
            voices,
            output_dir=voice_dir,
            raw_voice=args.raw_voice,
            audio_format=args.audio_format,
            keep_archive=args.keep_archive,
        )


if __name__ == "__main__":
    main()
