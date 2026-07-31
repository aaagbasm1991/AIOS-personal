#!/usr/bin/env python3
"""會議音檔轉錄：Breeze-ASR-25（台灣國語＋中英夾雜特化）via faster-whisper。

用法：
    python transcribe.py <音檔> [--glossary <術語表.md>] [--output <輸出目錄>]
                          [--model <HF模型ID或本機路徑>] [--srt]

流程：ffmpeg 前處理（16kHz 單聲道＋音量正規化）→ faster-whisper CPU int8 推論
     → 輸出 <音檔名>.transcript.txt（含時間戳）與可選 .srt。

首次執行會從 HuggingFace 下載模型（約 3GB），之後走本機快取。
輸出為初稿；同音錯字請依 SKILL.md 的「校正段」用術語表過一遍再整理。
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_MODEL = "SoybeanMilk/faster-whisper-Breeze-ASR-25"
AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".aac", ".wma",
              ".mp4", ".mov", ".mkv", ".webm"}


def load_glossary_terms(path: Path) -> list[str]:
    """從術語表的表格列抓出反引號包住的詞（第一欄），餵給 initial_prompt 做辨識偏置。"""
    terms: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        for match in re.findall(r"`([^`\n]{1,30})`", line):
            if match not in terms:
                terms.append(match)
    return terms


def preprocess(src: Path, workdir: Path) -> Path:
    """ffmpeg：轉 16kHz 單聲道 wav 並做響度正規化（遠端與會者收音差很多）。"""
    out = workdir / (src.stem + ".16k.wav")
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"ffmpeg 前處理失敗：\n{result.stderr[-800:]}")
    return out


def fmt_ts(seconds: float, srt: bool = False) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    if srt:
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Breeze-ASR-25 會議轉錄")
    parser.add_argument("audio", type=Path, help="音檔或影片檔路徑")
    parser.add_argument("--glossary", type=Path, default=None,
                        help="術語表 markdown（預設找同 skill 的 references/glossary.md）")
    parser.add_argument("--output", type=Path, default=None,
                        help="輸出目錄（預設與音檔同層）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"模型 ID 或路徑（預設 {DEFAULT_MODEL}）")
    parser.add_argument("--srt", action="store_true", help="同時輸出 .srt 字幕檔")
    args = parser.parse_args()

    if not args.audio.exists():
        sys.exit(f"找不到檔案：{args.audio}")
    if args.audio.suffix.lower() not in AUDIO_EXTS:
        sys.exit(f"不支援的格式 {args.audio.suffix}（支援：{', '.join(sorted(AUDIO_EXTS))}）")

    glossary = args.glossary or (Path(__file__).parent.parent / "references" / "glossary.md")
    terms = load_glossary_terms(glossary) if glossary.exists() else []
    # Whisper prompt 上限約 224 token，術語太多時取前段
    initial_prompt = ("以下是繁體中文的會議逐字稿，可能中英夾雜。常見詞彙：" +
                      "、".join(terms[:60]) + "。") if terms else \
                     "以下是繁體中文的會議逐字稿，可能中英夾雜。"

    outdir = args.output or args.audio.parent
    outdir.mkdir(parents=True, exist_ok=True)

    from faster_whisper import WhisperModel

    print(f"[1/3] ffmpeg 前處理 {args.audio.name} …", flush=True)
    with tempfile.TemporaryDirectory() as td:
        wav = preprocess(args.audio, Path(td))

        print(f"[2/3] 載入模型 {args.model}（首次執行需下載約 3GB）…", flush=True)
        model = WhisperModel(args.model, device="cpu", compute_type="int8")

        print("[3/3] 轉錄中（CPU 推論，長會議請耐心等）…", flush=True)
        segments, info = model.transcribe(
            str(wav),
            language="zh",
            initial_prompt=initial_prompt,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 700},
        )

        txt_path = outdir / (args.audio.stem + ".transcript.txt")
        srt_path = outdir / (args.audio.stem + ".srt")
        lines, srt_blocks = [], []
        for i, seg in enumerate(segments, 1):
            text = seg.text.strip()
            if not text:
                continue
            lines.append(f"[{fmt_ts(seg.start)}] {text}")
            srt_blocks.append(
                f"{i}\n{fmt_ts(seg.start, srt=True)} --> {fmt_ts(seg.end, srt=True)}\n{text}\n")
            print(f"  [{fmt_ts(seg.start)}] {text}", flush=True)

        txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if args.srt:
            srt_path.write_text("\n".join(srt_blocks), encoding="utf-8")

    print(f"\n完成。音訊長度 {fmt_ts(info.duration)}，逐字稿：{txt_path}")
    if args.srt:
        print(f"字幕：{srt_path}")
    print("提醒：這是初稿，請依 SKILL.md 的校正段用術語表修一遍同音錯字再整理。")


if __name__ == "__main__":
    main()
