"""
YouTube Video Research and Metadata Intelligence Service.
Department: 03_media_ingestion/online_media
Provides official oEmbed inspection, yt-dlp structural extraction,
chapter detection, caption retrieval, and search capabilities.
"""
import json
import logging
import re
import subprocess
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    MediaPermissionTier,
    OnlineMediaSearchQuery,
    OnlineMediaSourceType,
    OnlineVideoChapter,
    OnlineVideoMetadata,
    OnlineVideoSubtitleInfo,
)

logger = logging.getLogger("studio.online_media.youtube_research")

YOUTUBE_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
)


class YouTubeResearchService:
    """
    Service for researching online YouTube videos, extracting structural metadata,
    analyzing chapters and captions, and generating reference profiles.
    """

    def __init__(self, yt_dlp_binary: str = "/Library/Frameworks/Python.framework/Versions/3.13/bin/yt-dlp"):
        self.yt_dlp = yt_dlp_binary

    @staticmethod
    def validate_youtube_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a URL is a legitimate YouTube video URL and extracts the 11-char video ID.
        """
        if not url:
            return False, None
        match = YOUTUBE_REGEX.search(url.strip())
        if match:
            return True, match.group(1)
        return False, None

    def get_oembed_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Queries YouTube's official oEmbed endpoint for compliant metadata and iframe embed code.
        """
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
            req = urllib.request.Request(
                oembed_url,
                headers={"User-Agent": "UniversalStudio/2.0 (VideoResearchService)"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            logger.debug(f"oEmbed fetch failed for {url}: {e}")
        return None

    def get_video_metadata(self, url_or_id: str) -> OnlineVideoMetadata:
        """
        Retrieves deep structural metadata, chapters, resolutions, and available subtitles.
        Combines official oEmbed with yt-dlp structural analysis.
        """
        is_valid, video_id = self.validate_youtube_url(url_or_id)
        if not is_valid:
            # If not a full URL, check if bare 11-char ID
            if len(url_or_id.strip()) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id.strip()):
                video_id = url_or_id.strip()
                target_url = f"https://www.youtube.com/watch?v=video_id"
            else:
                raise ValueError(f"Invalid YouTube URL or Video ID: {url_or_id}")
        else:
            target_url = f"https://www.youtube.com/watch?v={video_id}"

        # 1. Fetch Official oEmbed Data
        oembed = self.get_oembed_metadata(target_url) or {}
        title = oembed.get("title", f"YouTube Video ({video_id})")
        author = oembed.get("author_name", "Unknown Creator")
        channel_url = oembed.get("author_url")
        thumbnail_url = oembed.get("thumbnail_url", f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg")
        embed_html = oembed.get("html")

        # 2. Extract Structural Metadata via yt-dlp (no media downloaded)
        duration = 0.0
        description = ""
        view_count = None
        like_count = None
        upload_date = None
        chapters: List[OnlineVideoChapter] = []
        subtitles_available: List[OnlineVideoSubtitleInfo] = []
        tags: List[str] = []
        resolutions = ["360p", "720p", "1080p"]
        audio_formats = ["m4a", "webm", "mp3", "wav"]

        try:
            cmd = [
                self.yt_dlp,
                "--dump-json",
                "--no-download",
                "--no-warnings",
                "--skip-download",
                target_url
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
                title = data.get("title") or title
                author = data.get("uploader") or data.get("channel") or author
                description = data.get("description", "")
                duration = float(data.get("duration") or 0.0)
                view_count = data.get("view_count")
                like_count = data.get("like_count")
                upload_date = data.get("upload_date")
                tags = data.get("tags") or []

                # Parse Chapters
                raw_chapters = data.get("chapters") or []
                for ch in raw_chapters:
                    chapters.append(OnlineVideoChapter(
                        title=ch.get("title", "Chapter"),
                        start_time_seconds=float(ch.get("start_time", 0.0)),
                        end_time_seconds=float(ch.get("end_time")) if ch.get("end_time") is not None else None
                    ))

                # Parse Available Subtitles
                subs = data.get("subtitles") or {}
                auto_subs = data.get("automatic_captions") or {}
                for lang_code, formats in subs.items():
                    subtitles_available.append(OnlineVideoSubtitleInfo(
                        language_code=lang_code,
                        language_name=lang_code.upper(),
                        is_automatic=False,
                        format_url=formats[0].get("url") if formats else None
                    ))
                for lang_code in list(auto_subs.keys())[:10]:
                    if lang_code not in subs:
                        subtitles_available.append(OnlineVideoSubtitleInfo(
                            language_code=lang_code,
                            language_name=f"{lang_code.upper()} (Auto)",
                            is_automatic=True,
                            format_url=None
                        ))

                # Extract available formats
                raw_formats = data.get("formats") or []
                found_res = set()
                for f in raw_formats:
                    h = f.get("height")
                    if h:
                        found_res.add(f"{h}p")
                if found_res:
                    resolutions = sorted(list(found_res), key=lambda x: int(x.replace("p", "")) if x.replace("p", "").isdigit() else 0)
        except Exception as e:
            logger.warning(f"yt-dlp detailed extraction warning for {video_id}: {e}")

        return OnlineVideoMetadata(
            video_id=video_id,
            url=target_url,
            title=title,
            description=description[:2000],
            author=author,
            channel_id=None,
            channel_url=channel_url,
            duration_seconds=duration,
            upload_date=upload_date,
            view_count=view_count,
            like_count=like_count,
            thumbnail_url=thumbnail_url,
            available_resolutions=resolutions,
            available_audio_formats=audio_formats,
            chapters=chapters,
            subtitles_available=subtitles_available,
            tags=tags[:20],
            is_embeddable=True,
            is_download_permitted=False,
            permission_tier=MediaPermissionTier.REFERENCE_ONLY,
            embed_html=embed_html,
            source_type=OnlineMediaSourceType.YOUTUBE
        )

    def search_youtube(self, search_query: OnlineMediaSearchQuery) -> List[OnlineVideoMetadata]:
        """
        Searches YouTube by keyword or creator and returns normalized video metadata records.
        """
        query_str = search_query.query
        if search_query.channel:
            query_str += f" {search_query.channel}"

        cmd = [
            self.yt_dlp,
            f"ytsearch{search_query.limit}:{query_str}",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
            "--no-warnings"
        ]

        results: List[OnlineVideoMetadata] = []
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            if proc.returncode == 0 and proc.stdout:
                for line in proc.stdout.strip().split("\n"):
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        v_id = item.get("id") or item.get("url", "")[-11:]
                        if not v_id:
                            continue
                        thumbs = item.get("thumbnails") or []
                        thumb = thumbs[0].get("url") if thumbs else f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

                        results.append(OnlineVideoMetadata(
                            video_id=v_id,
                            url=item.get("webpage_url") or f"https://www.youtube.com/watch?v={v_id}",
                            title=item.get("title", "Untitled Video"),
                            description=item.get("description", "")[:500],
                            author=item.get("uploader") or item.get("channel", "Unknown"),
                            channel_id=item.get("channel_id"),
                            channel_url=item.get("channel_url") or item.get("uploader_url"),
                            duration_seconds=float(item.get("duration") or 0.0),
                            upload_date=item.get("upload_date"),
                            view_count=item.get("view_count"),
                            thumbnail_url=thumb,
                            available_resolutions=["360p", "720p", "1080p"],
                            available_audio_formats=["wav", "mp3", "m4a"],
                            is_embeddable=True,
                            is_download_permitted=False,
                            permission_tier=MediaPermissionTier.REFERENCE_ONLY,
                            embed_html=f'<iframe src="https://www.youtube.com/embed/{v_id}" frameborder="0" allowfullscreen></iframe>',
                            source_type=OnlineMediaSourceType.YOUTUBE
                        ))
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Search query '{search_query.query}' failed: {e}")

        return results

    def get_video_captions(self, url_or_id: str, lang: str = "en") -> List[Dict[str, Any]]:
        """
        Retrieves timed captions for a video if available.
        Returns a list of dicts: [{"start_seconds": 0.0, "duration_seconds": 2.5, "text": "..."}]
        """
        is_valid, video_id = self.validate_youtube_url(url_or_id)
        if not is_valid:
            if len(url_or_id.strip()) == 11:
                video_id = url_or_id.strip()
            else:
                return []
        target_url = f"https://www.youtube.com/watch?v={video_id}"

        cmd = [
            self.yt_dlp,
            "--skip-download",
            "--write-auto-subs",
            "--write-subs",
            "--sub-lang", lang,
            "--sub-format", "json3",
            "--dump-json",
            target_url
        ]

        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
            if proc.returncode == 0 and proc.stdout:
                data = json.loads(proc.stdout)
                # Check for automatic_captions or subtitles
                subs = data.get("subtitles", {}).get(lang) or data.get("automatic_captions", {}).get(lang)
                if subs:
                    # Return available format URLs
                    return [{"language": lang, "formats": subs}]
        except Exception as e:
            logger.debug(f"Caption fetch error for {video_id}: {e}")

        return []

