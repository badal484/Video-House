"""
Wikimedia Commons Resource Provider Adapter.
Department: 03_media_ingestion/discovery/providers
"""
import json
import urllib.parse
import urllib.request
from typing import List, Optional

from .base import BaseResourceProvider
from ..models import DiscoveredAsset, LicenseCategory, ResourceMediaType, ResourceQuery


class WikimediaCommonsProvider(BaseResourceProvider):
    """
    Search and metadata resolver for Wikimedia Commons API.
    Provides authentic wildlife footage, biological plates, and public domain media.
    """

    def __init__(self, is_enabled: bool = True):
        super().__init__(name="Wikimedia Commons", is_enabled=is_enabled)
        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def search(self, query: ResourceQuery) -> List[DiscoveredAsset]:
        if not self.is_enabled:
            return []

        search_term = query.query
        if query.media_type == ResourceMediaType.VIDEO:
            if "filetype:video" not in search_term.lower() and not any(ext in search_term.lower() for ext in [".webm", ".ogv", ".mp4"]):
                search_term += " filetype:video"

        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_term,
            "srnamespace": "6",  # File: namespace
            "srlimit": min(query.limit * 2, 30),
            "format": "json"
        }
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return []

        search_items = data.get("query", {}).get("search", [])
        if not search_items:
            return []

        titles = [item["title"] for item in search_items]
        return self._fetch_batch_details(titles, query.media_type)[:query.limit]

    def get_asset_details(self, asset_id: str) -> Optional[DiscoveredAsset]:
        title = asset_id if asset_id.startswith("File:") else f"File:{asset_id}"
        results = self._fetch_batch_details([title], ResourceMediaType.VIDEO)
        return results[0] if results else None

    def _fetch_batch_details(self, titles: List[str], target_type: ResourceMediaType) -> List[DiscoveredAsset]:
        if not titles:
            return []

        info_params = {
            "action": "query",
            "titles": "|".join(titles),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "format": "json"
        }
        url = f"{self.api_url}?{urllib.parse.urlencode(info_params)}"
        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return []

        pages = data.get("query", {}).get("pages", {})
        discovered: List[DiscoveredAsset] = []

        for p in pages.values():
            title = p.get("title", "")
            imageinfo = p.get("imageinfo", [])
            if not imageinfo:
                continue
            info = imageinfo[0]
            dl_url = info.get("url", "")
            if not dl_url:
                continue

            mime = info.get("mime", "")
            width = info.get("width", 0)
            height = info.get("height", 0)
            duration = info.get("duration", None)
            file_size = info.get("size", 0)

            # Determine Media Type
            if "video" in mime or title.lower().endswith((".webm", ".ogv", ".mp4")):
                actual_type = ResourceMediaType.VIDEO
            elif "image" in mime or title.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                actual_type = ResourceMediaType.IMAGE
            elif title.lower().endswith(".svg"):
                actual_type = ResourceMediaType.VECTOR
            else:
                actual_type = target_type

            # License metadata
            extmeta = info.get("extmetadata", {})
            raw_lic = extmeta.get("LicenseShortName", {}).get("value", "CC")
            lic_cat = LicenseCategory.from_string(raw_lic)
            artist = extmeta.get("Artist", {}).get("value", "Wikimedia Contributor")
            desc = extmeta.get("ImageDescription", {}).get("value", "")

            discovered.append(DiscoveredAsset(
                asset_id=title,
                provider=self.name,
                title=title.replace("File:", "").replace("_", " "),
                description=desc[:200] if desc else title,
                media_type=actual_type,
                source_page_url=f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}",
                download_url=dl_url,
                preview_url=info.get("thumburl", dl_url),
                width=width,
                height=height,
                duration=float(duration) if duration else None,
                file_size_bytes=file_size,
                mime_type=mime,
                license_category=lic_cat,
                license_name=raw_lic,
                author=artist[:80],
                attribution_text=f"{artist} / Wikimedia Commons ({raw_lic})",
                tags=[actual_type.value, "commons", "public_access"],
                raw_metadata=extmeta
            ))

        return discovered
