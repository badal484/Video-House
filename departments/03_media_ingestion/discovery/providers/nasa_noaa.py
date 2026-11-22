"""
NASA & NOAA Public Scientific Media Provider Adapter.
Department: 03_media_ingestion/discovery/providers
"""
import json
import urllib.parse
import urllib.request
from typing import List, Optional

from .base import BaseResourceProvider
from ..models import DiscoveredAsset, LicenseCategory, ResourceMediaType, ResourceQuery


class NasaNoaaProvider(BaseResourceProvider):
    """
    Search adapter for NASA and NOAA public scientific archives.
    All government scientific imagery is Public Domain (US Gov Work).
    """

    def __init__(self, is_enabled: bool = True):
        super().__init__(name="NASA & NOAA Scientific Archive", is_enabled=is_enabled)
        self.api_url = "https://images-api.nasa.gov/search"
        self.headers = {
            "User-Agent": "UniversalVideoStudio/1.0"
        }

    def search(self, query: ResourceQuery) -> List[DiscoveredAsset]:
        if not self.is_enabled:
            return []

        media_type_filter = "video" if query.media_type == ResourceMediaType.VIDEO else "image"
        params = {
            "q": query.query,
            "media_type": media_type_filter,
            "page_size": min(query.limit, 15)
        }
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return []

        items = data.get("collection", {}).get("items", [])
        discovered: List[DiscoveredAsset] = []

        for item in items:
            data_arr = item.get("data", [{}])
            meta = data_arr[0] if data_arr else {}
            nasa_id = meta.get("nasa_id", "")
            title = meta.get("title", "NASA Asset")
            desc = meta.get("description", "")
            center = meta.get("center", "NASA")

            # Thumbnail link
            links = item.get("links", [])
            preview_url = links[0].get("href", "") if links else None

            # Actual file collection URL
            href = item.get("href", "")
            dl_url = href  # Will resolve to collection json or direct file

            discovered.append(DiscoveredAsset(
                asset_id=f"nasa_{nasa_id}",
                provider=self.name,
                title=title,
                description=desc[:200] if desc else title,
                media_type=query.media_type,
                source_page_url=f"https://images.nasa.gov/details/{nasa_id}",
                download_url=preview_url or dl_url,
                preview_url=preview_url,
                license_category=LicenseCategory.PUBLIC_DOMAIN,
                license_name="Public Domain (US Gov Work)",
                author=f"NASA / {center}",
                attribution_text=f"Image/Video Credit: NASA / {center} (Public Domain)",
                tags=["nasa", "scientific", "public_domain"],
                raw_metadata=meta
            ))

        return discovered[:query.limit]

    def get_asset_details(self, asset_id: str) -> Optional[DiscoveredAsset]:
        clean_id = asset_id.replace("nasa_", "")
        query = ResourceQuery(query=clean_id, limit=1)
        res = self.search(query)
        return res[0] if res else None
