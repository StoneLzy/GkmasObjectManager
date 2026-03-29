# GkmasObjectManager

An OOP interface for interacting with object databases
in the mobile game [Gakuen Idolm@ster](https://gakuen.idolmaster-official.jp/).

Designed with ❤ by [Ziyuan "Heartcore" Chen](https://allenheartcore.github.io/). <br>
Refactored from [gkmasToolkit](https://github.com/kishidanatsumi/gkmasToolkit) by Kishida Natsumi, <br>
which in turn was adapted from [HoshimiToolkit](https://github.com/MalitsPlus/HoshimiToolkit) by Vibbit. <br>
Request API & decryption algorithms borrowed from [HatsuboshiToolkit](https://github.com/DreamGallery/HatsuboshiToolkit) by DreamGallery.



## Features

- Fetch, decrypt, deserialize, and export manifest as ProtoDB, JSON, or CSV
- Differentiate between / add (apply patch to) manifest revisions
- Download and deobfuscate assetbundles and resources in parallel
- Media conversion plugins for Texture2D, AudioClip audio, AWB audio, and USM video



## Example Usage

```python
import GkmasObjectManager as gom

m = gom.fetch()  # fetch latest
m.export("manifest.json")

m_old = gom.load("octocacheevai")
m_diff = m - m_old
m_diff.export("manifest_diff.json")

m.download(
    "img.*cidol.*full.*", "img.*csprt.*full.*",  # character & support cards
    image_format="JPEG", image_resize="16:9"
)
m.download("sud.*inst.*.awb", audio_format="WAV")  # instrumental songs
m.download("mov.*cidol.*loop.usm", video_format="MP4")  # animated character cards
m.download(
    "sud_vo_adv_unit.*",
    path="mainstory_voicelines",
    audio_format="mp3",  # applies to all subsongs
    unpack_subsongs=True,  # unpack ZIP to output directory
)

m.download_preset("presets/namecard_kit.yml")
```



## Helper Scripts

If you already have a Conda environment for this project, run the helper scripts
from the repository root with `conda run -n <env> python ...`.
Examples below assume your environment is named `gakumas`.

### `extract_card_images.py`

Exports card images from the latest manifest.

- Default output directory: `out/cards`
- Default export format: `png`
- If `--flat` is **not** set, files are placed into nested subdirectories under
  `out/cards/` based on object names, such as
  `out/cards/img/general/cidol-hski/...`
- If `--flat` is set, matched files are written directly into `--out`

Examples:

```bash
conda run -n gakumas python extract_card_images.py --idol hski --kind full --latest-only --dry-run
conda run -n gakumas python extract_card_images.py --idol hski --kind full --latest-only --out out/hski
conda run -n gakumas python extract_card_images.py --idol hski --kind portrait --out out/hski_portrait
conda run -n gakumas python extract_card_images.py --kind support-full --latest-only --out out/support
conda run -n gakumas python extract_card_images.py --pattern "img_general_cidol-hski.*full" --limit 5 --out out/custom
```

Common options:

- `--idol`: idol short code such as `hski`, `ttmr`, `fktn`
- `--kind`: one of `full`, `portrait`, `landscape`, `all`, `support-full`, `support-thumb`
- `--out`: output directory, defaults to `out/cards`
- `--format`: image format such as `png` or `jpeg`
- `--resize`: optional resize ratio such as `9:16` or `16:9`
- `--latest-only`: only export the newest matched object
- `--limit N`: only export the newest `N` matches
- `--flat`: disable nested subdirectories
- `--dry-run`: list matches without downloading

### `extract_dialogues.py`

Exports dialogue scripts (`adv_*`) and voice archives (`sud_vo_adv_*`) from the latest manifest.

- Default output directory: `out/dialogues`
- If `--mode script`, scripts are written into `out/dialogues`
- If `--mode voice`, voice files are written into `out/dialogues`
- If `--mode both`, scripts go to `out/dialogues/scripts` and voices go to `out/dialogues/voices`
- If `--captions` is set, a caption map is also written to `out/dialogues/captions.json`
- If `--flat` is **not** set, exported files are further organized into nested subdirectories
- If `--raw-script` is **not** set, scripts are converted to JSON
- If `--raw-voice` is **not** set, voice archives are converted to audio files

Examples:

```bash
conda run -n gakumas python extract_dialogues.py --idol hski --kind produce-story
conda run -n gakumas python extract_dialogues.py --idol hski --kind produce-story --mode both --captions
conda run -n gakumas python extract_dialogues.py --idol hski --kind dear --mode voice --audio-format mp3
conda run -n gakumas python extract_dialogues.py --idol hski --kind idol-card --mode voice --raw-voice
conda run -n gakumas python extract_dialogues.py --script-pattern "adv_pstory_001_hski_.*" --voice-pattern "sud_vo_adv_pstory_001_hski_.*" --mode both --latest-only --dry-run
```

Common options:

- `--idol`: idol short code such as `hski`, `ttmr`, `fktn`
- `--kind`: one of `produce-story`, `idol-card`, `dear`, `all-idol`, `event`, `unit`
- `--mode`: `script`, `voice`, or `both`
- `--out`: base output directory, defaults to `out/dialogues`
- `--audio-format`: voice export format such as `wav` or `mp3`
- `--raw-script`: export raw `.txt` scripts instead of parsed JSON
- `--raw-voice`: export raw `.acb` archives instead of converted audio
- `--keep-archive`: keep multi-track voice exports as `.zip` instead of unpacking them
- `--captions`: export `captions.json` generated from matched scripts
- `--latest-only`: only export the newest matched object on each side
- `--limit N`: only export the newest `N` matches
- `--flat`: disable nested subdirectories
- `--dry-run`: list matches without downloading

### `extract_latest_cidol_bundle.py`

Exports the latest idol card image together with its matching `adv_cidol-*` scripts,
`sud_vo_adv_cidol-*` voice lines, and a generated `captions.json`.

- Default output directory: `out/latest_cidol_bundle`
- The script creates a bundle subdirectory named after the resolved card story base,
  for example `out/latest_cidol_bundle/cidol-hski-3-017/`
- Card image goes to `.../card/`
- Scripts go to `.../scripts/`
- Voices go to `.../voices/`
- Captions are written to `.../captions.json`
- If `--idol` is omitted, the script uses the latest idol card across all idols

Examples:

```bash
conda run -n gakumas python extract_latest_cidol_bundle.py --dry-run
conda run -n gakumas python extract_latest_cidol_bundle.py --out out/latest_bundle
conda run -n gakumas python extract_latest_cidol_bundle.py --idol hski --audio-format mp3
conda run -n gakumas python extract_latest_cidol_bundle.py --idol ttmr --image-format jpeg --image-resize 9:16
```

Common options:

- `--idol`: optional idol short code such as `hski`, `ttmr`, `fktn`
- `--out`: base output directory, defaults to `out/latest_cidol_bundle`
- `--image-format`: card image export format such as `png` or `jpeg`
- `--image-resize`: optional card image resize ratio such as `9:16`
- `--audio-format`: voice export format such as `wav` or `mp3`
- `--raw-script`: export raw `.txt` scripts instead of parsed JSON
- `--raw-voice`: export raw `.acb` voice archives instead of converted audio
- `--keep-archive`: keep multi-track voice exports as `.zip` instead of unpacking them
- `--dry-run`: only print the resolved latest card and related assets

## Class Hierarchy

- `manifest.decrypt.AESCBCDecryptor` - Manifest decryption
- `manifest.octodb_pb2.Database` - ProtoDB deserialization
- `manifest.manifest.GkmasManifest` - **ENTRY POINT**
  - `manifest.revision.GkmasManifestRevision` - Manifest revision management
  - `manifest.listing.GkmasObjectList` - Object listing and indexing
    - `object.resource.GkmasResource` - Non-Unity object
      - `media.dummy.GkmasDummyMedia` - Base class for media conversion plugins
      - `media.image.GkmasImage` - PNG image handling
      - `media.audio.GkmasAudio` - MP3 audio handling
      - `media.audio.GkmasAWBAudio` - ACB/AWB audio conversion
      - `media.video.GkmasUSMVideo` - USM video conversion
    - `object.deobfuscate.GkmasAssetBundleDeobfuscator`
    - `object.assetbundle.GkmasAssetBundle` - Unity object
      - `media.dummy.GkmasDummyMedia`
      - `media.image.GkmasUnityImage` - Texture2D image handling
      - `media.audio.GkmasUnityAudio` - AudioClip audio handling



## Object Hierarchy

`#` denotes a number. <br>
`IDOL` denotes `(hski|ttmr|fktn|amao|kllj|kcna|ssmk|shro|hrnm|hume|hmsz|jsna)`.

- Image `img`
  - `adv`
    - `img_adv_speaker_(krnh|andk|sson|sgka)_###-###`
    - `img_adv_still_all_cmmn_###-##`
    - `img_adv_still_dear_IDOL_###-###`
    - `img_adv_still_pstory_cmmn_###-##`
  - `chr`
    - `img_chr_IDOL_##-(audition|bustup|full|thumb-circle|thumb-push)`
    - `img_chr_(atbm|nasr|trvo|trda|trvi)_##-thumb-circle`
  - `cos`
    - `img_cos_IDOL-(schl|trng|casl|cstm|othr)-####_body`
    - `img_cos_costume_head_IDOL-(schl|casl|cstm|hair)-####_head`
  - `gasha`
    - `img_gasha_banner_gasha-#####-(standard|pickup|select-pickup|free)-###-(logo|select|select-m|select-s)`
    - `img_gasha_banner_gasha-#####-(pidol|support)-select-pickup-###-(logo|select-m|select-s)`
    - `img_gasha_banner_gasha_ticket_ssr_(idol|support|idol_support)_#-(logo|select-m|select-s)`
    - `img_gasha_banner_gasha_ssr_##-(logo|select-m|select-s)`
    - `img_gasha_text_*`
  - `general`
    - `img_general_achievement_(common|produce|char_IDOL)_###`
    - `img_general_achievement_IDOL-(#-###|master|tower)_###`
    - `img_general_cidol-IDOL-#-###_#-(full|thumb-(landscape|landscape-large|portrait|square|gasha))`
    - `img_general_csprt-1-####_(full|thumb-(landscape|square))`
    - `img_general_(comic_####|comic4_####|comic4_####-thumb)`
    - `img_general_commu_(top|part|support|event)-header_###`
    - `img_general_commu_chapter-(header|thumb)_##-##`
    - `img_general_commu_thumb_unit_##-##-##`
    - `img_general_commu_idol-top_IDOL-thumb`
    - `img_general_commu_dearness_IDOL-banner`
    - ...
  - ...
- Audio `sud`
  - ...
- Video `mov`
  - Major
    - `mov_adv_dear_ed_IDOL_###`
    - `mov_general_cidol-IDOL-3-###_1(|-loop)(|-gasha)`
    - `mov_general_gasha_bg_idol_cidol-IDOL-3-###`
    - `mov_general_gasha_bg_support_csprt-#-####`
    - `mov_general_gasha_live_i_card-skin-IDOL-3-###-result`
  - Minor
    - `mov_adv_unit_explanation_cmmn_001`
    - `mov_gasha_monitor_(monitor|step1|tap)-(000|002|003|004_IDOL)`
    - `mov_gasha_movie_tap-(000|002|003|004)`
    - `mov_general_gasha_(school-logo|taptostart)-alpha`
    - `mov_general_media_(opening|pv|pv_jsna)_001`
    - `mov_general_monitor_(01|03)`
- Text `adv`
  - Major
    - `adv_cidol-IDOL-3-###_##`
    - `adv_csprt-#-####_##`
    - `adv_dear_IDOL_(###|010-01)`
    - `adv_event_###_main-##`
    - `adv_live_IDOL_001_(start|end)-(##-01|04-02)`
    - `adv_pevent_001_IDOL_(activity_(###|(017|018)-(01-02))|school_###)`
    - `adv_pevent_002_IDOL_sales_#-###-(01|02)`
    - `adv_pgrowth_001_IDOL_##`
    - `adv_pstep_001_cmmn_(before|after)-(lesson|jyugyo|odekake|rest|sikyu)-##-(a|b|c|d|cmn)(|-02)`
    - `adv_pstep_002_cmmn_((before-lesson-##-(a|b|c|d))|((before|after)-eigyo|after-present)-##-cmn-(01|02))`
    - `adv_pstory_001_IDOL_(opening|after-step-(1|2)|ending)-(normal|true)-##`
    - `adv_pstory_001_IDOL_(before|after)-audition-(mid|final)-(normal|failure)-##`
    - `adv_unit_01-##_##`
  - Minor
    - `adv_event_highscore_introduction-01`
    - `adv_presult_(001|002)_(midterm-failure|final-(failure|normal-##|true))`
    - `adv_produce-refresh_(001|002)_before-audition-(final|mid)`
    - `adv_produce-week-skip_002_01`
    - `adv_pweek_001_cmmn_(toschool|schoolroom|corridor|classroom)-(01|02)-(a|b|c|d|ac)(|-02)`
    - `adv_startup_202#_(|user-)bd-01_IDOL-01`
    - `adv_tower-001`
    - `adv_tutorial_first_(cmmn|hski|ttmr|fktn)-##`
    - `adv_warmup`
- Models
  - Model `mdl`
    - ...
  - Motion `mot`
    - ...
  - Environment `env`
    - ...
  - FBX `fbx`
  - MEF `mef`
  - Timeline `tln`
  - Crowd `crw`
  - Effect `eff`
- Miscellaneous
  - `scl`
  - `ttn`
  - `fgd`
  - `t`
  - `sky`
  - `image_sprite_atlas.unity3d`
  - `actor-shader.unity3d`
  - `ui-shader.unity3d`
  - `shader.unity3d`
  - `m_fdc.unity3d`
  - `Custom.acf`
  - `musics.txt`
