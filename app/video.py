
from pathlib import Path
from typing import List, Tuple, Optional
from moviepy.editor import (VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math, os

W, H = 1080, 1920  # 9:16 vertical

def _fit_clip_to_vertical(clip):
    # Center-crop or resize to fill 9:16 frame
    w, h = clip.size
    target_ratio = W / H
    ratio = w / h
    if ratio > target_ratio:  # too wide -> crop sides
        new_w = int(h * target_ratio)
        x1 = (w - new_w) // 2
        clip = clip.crop(x1=x1, x2=x1+new_w)
    else:  # too tall -> crop top/bottom minimally
        new_h = int(w / target_ratio)
        y1 = max(0, (h - new_h) // 2)
        clip = clip.crop(y1=y1, y2=y1+new_h)
    return clip.resize((W, H))

def _render_text_image(text: str, max_width: int = W-120, padding: int = 24) -> Image.Image:
    # Create a caption image with PIL
    bg = Image.new("RGBA", (max_width + padding*2, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)

    # Try to load a common font; fallback to default
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, 64)
            break
    if font is None:
        font = ImageFont.load_default()

    # Wrap text
    words = text.split()
    lines = []
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2] > max_width and line:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)

    line_heights = []
    max_line_w = 0
    for ln in lines:
        bbox = draw.textbbox((0,0), ln, font=font)
        max_line_w = max(max_line_w, bbox[2])
        line_heights.append(bbox[3])

    total_h = sum(line_heights) + padding*2 + (len(lines)-1)*8
    img = Image.new("RGBA", (max_line_w + padding*2, total_h), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    # Draw semi-transparent rectangle backdrop
    rect_color = (0,0,0,140)
    draw.rounded_rectangle((0,0,img.width,img.height), radius=20, fill=rect_color)

    y = padding
    for i, ln in enumerate(lines):
        bbox = draw.textbbox((0,0), ln, font=font)
        draw.text(((img.width - bbox[2])//2, y), ln, font=font, fill=(255,255,255,255))
        y += bbox[3] + 8

    return img

def compose_video(audio_path: Path, img_paths: List[Path], vid_paths: List[Path], captions: List[Tuple[str,float,float]], brand_handle: str, bgm_path: Optional[Path], out_path: Path) -> Path:
    voice = AudioFileClip(str(audio_path))
    duration = voice.duration

    # Build visuals: prioritize videos; if none, use images with simple pan
    visuals = []
    t_accum = 0.0

    parts = vid_paths if vid_paths else img_paths
    if not parts:
        # solid background fallback
        bg = ImageClip(np.full((H, W, 3), 10, dtype=np.uint8)).set_duration(duration)
        visuals.append(bg)
    else:
        # tile clips to cover full duration
        idx = 0
        while t_accum < duration and idx < len(parts) * 5:  # loop up to 5x
            p = parts[idx % len(parts)]
            if str(p).lower().endswith((".mp4",".mov",".webm",".mkv",".avi")):
                try:
                    clip = VideoFileClip(str(p)).without_audio()
                    clip = _fit_clip_to_vertical(clip)
                    seg_dur = min(clip.duration, duration - t_accum)
                    visuals.append(clip.subclip(0, seg_dur))
                    t_accum += seg_dur
                except Exception:
                    pass
            else:
                seg_dur = min( max(1.5, duration/len(parts)), duration - t_accum )
                try:
                    ic = ImageClip(str(p)).set_duration(seg_dur)
                    ic = _fit_clip_to_vertical(ic)
                    visuals.append(ic)
                    t_accum += seg_dur
                except Exception:
                    pass
            idx += 1

    from moviepy.editor import concatenate_videoclips, CompositeVideoClip
    base = concatenate_videoclips(visuals).set_duration(duration)

    overlays = []

    # Watermark / handle
    wm_img = _render_text_image(brand_handle)
    wm_path = out_path.parent / "wm.png"
    wm_img.save(wm_path)
    wm_clip = ImageClip(str(wm_path)).set_duration(duration).set_position(("center", H-200))
    overlays.append(wm_clip.set_opacity(0.7))

    # Captions overlay (burned-in)
    for text, start, end in captions:
        if end <= start: continue
        cap_img = _render_text_image(text)
        cap_path = out_path.parent / f"cap_{int(start*1000)}.png"
        cap_img.save(cap_path)
        cap_clip = ImageClip(str(cap_path)).set_start(start).set_duration(end-start).set_position(("center","center"))
        overlays.append(cap_clip)

    composite = CompositeVideoClip([base, *overlays]).set_audio(voice)

    # Background music (quiet under voice) — optional simple mix
    if bgm_path and Path(bgm_path).exists():
        try:
            bgm = AudioFileClip(str(bgm_path)).volumex(0.12)
            if bgm.duration < duration:
                loops = [bgm] * int(math.ceil(duration / bgm.duration))
                from moviepy.editor import concatenate_audioclips
                bgm = concatenate_audioclips(loops).set_duration(duration)
            else:
                bgm = bgm.subclip(0, duration)
            from moviepy.editor import CompositeAudioClip
            composite = composite.set_audio(CompositeAudioClip([voice, bgm]))
        except Exception:
            pass

    out_path.parent.mkdir(parents=True, exist_ok=True)
    composite.write_videofile(str(out_path), codec="libx264", audio_codec="aac", fps=30, threads=4, preset="medium")
    composite.close()
    return out_path
