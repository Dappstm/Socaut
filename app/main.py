import argparse, asyncio, os
from pathlib import Path
from .utils import load_env, get_env
from .scheduler import run_poll_loop
from .models import Article, VideoJob
from .llm import generate_script
from .tts import synthesize_elevenlabs
from .stock_media import pixabay_search
from .captions import naive_segments, whisper_segments
from .video import compose_video
from .upload.youtube import upload_video as yt_upload
from .upload.tiktok import playwright_upload

async def handle_articles(articles):
    # Take first N for demo
    n_each_run = int(os.getenv("N_PER_RUN","1"))
    brand = os.getenv("BRAND_HANDLE","@YourHandle")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID","21m00Tcm4TlvDq8ikWAM")  # default voice id (Rachel in docs); replace
    outdir = Path(os.getenv("OUTPUT_DIR","output"))

    for art in articles[:n_each_run]:
        topic_context = f"Title: {art.title}\nBody: {art.body or ''}"
        script = generate_script(topic_context)
        print("Generated title:", script.title)

        # Voiceover
        audio_path = synthesize_elevenlabs(script.full_text, voice_id, outdir / "audio")

        # Stock media
        img_paths, vid_paths = pixabay_search(art.title or (art.topic or "technology"), outdir / "assets", max_items=5)

        # Caption segments
        try:
            segs = whisper_segments(audio_path)
        except Exception:
            from pydub import AudioSegment
            dur = AudioSegment.from_file(audio_path).duration_seconds
            segs = naive_segments(script.full_text, dur)

        # Compose video
        safe_title = "".join([c for c in script.title if c.isalnum() or c in (" ","-","_")]).strip()[:90]
        out_path = outdir / f"{safe_title or 'short'}_{art.external_id[:8]}.mp4"
        compose_video(audio_path, img_paths, vid_paths, segs, brand, os.getenv("BGM_PATH"), out_path)

        # Uploads
        tags = ["#shorts","#tiktok","#viral","#ai","#news"]
        try:
            if os.getenv("UPLOAD_YOUTUBE","1") == "1":
                yt = yt_upload(str(out_path), script.title, f"{script.hook}\n\n{script.body}\n\n{script.cta}", tags, categoryId="28", privacyStatus="public")
                print("YouTube video id:", yt.get("id"))
        except Exception as e:
            print("[WARN] YouTube upload failed:", e)

        try:
            if os.getenv("UPLOAD_TIKTOK","0") == "1":
                await playwright_upload(str(out_path), f"{script.title} { ' '.join(tags) }")
        except Exception as e:
            print("[WARN] TikTok upload failed:", e)

async def main():
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/feeds.yaml")
    parser.add_argument("--n_videos", type=int, default=1)
    parser.add_argument("--niche", type=str, default="AI Tools")
    parser.add_argument("--loop", action="store_true", help="Keep polling forever")
    args = parser.parse_args()
    os.environ["N_PER_RUN"] = str(args.n_videos)
    # If you prefer one-shot instead of loop, you can simulate one poll:
    async def on_articles(arts):
        if not arts:
            print("No new articles this cycle.")
            return
        await handle_articles(arts)
    from .scheduler import build_sources, poll_once
    sources, interval = build_sources(Path(args.config))
    if args.loop:
        async def on_articles_loop(arts):
            await handle_articles(arts[:args.n_videos])
        async def loop():
            while True:
                new_articles = await poll_once(sources)
                await on_articles_loop(new_articles)
                import asyncio
                await asyncio.sleep(interval)
        await loop()
    else:
        new_articles = await poll_once(sources)
        await on_articles(new_articles[:args.n_videos])

if __name__ == "__main__":
    asyncio.run(main())
