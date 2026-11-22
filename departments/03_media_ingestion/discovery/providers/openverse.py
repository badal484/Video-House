"""
Openverse Creative Commons Resource Provider Adapter.
Department: 03_media_ingestion/discovery/providers
"""
import json
import urllib.parse
import urllib.request
from typing import List, Optional

from .base import BaseResourceProvider
from ..models import DiscoveredAsset, LicenseCategory, ResourceMediaType, ResourceQuery


class OpenverseProvider(BaseResourceProvider):
    """
    Search adapter for the Openverse API (700M+ CC licensed images and audio).
    Public domain, CC0, CC BY, and museum archive coverage.
    """

    def __init__(self, is_enabled: bool = True):
        super().__init__(name="Openverse", is_enabled=is_enabled)
        self.base_url = "https://api.openverse.org/v1"
        self.headers = {
            "User-Agent": "UniversalVideoStudio/1.0 (creative@videostudio.studio)"
        }

    def search(self, query: ResourceQuery) -> List[DiscoveredAsset]:
        if not self.is_enabled:
            return []

        # Openverse currently indexes images and audio
        endpoint = "images" if query.media_type != ResourceMediaType.AUDIO else "audio"
        params = {
            "q": query.query,
            "page_size": min(query.limit, 20),
            "format": "json"
        }
        url = f"{self.base_url}/{endpoint}/?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return []

        results = data.get("results", [])
        discovered: List[DiscoveredAsset] = []

        for item in results:
            item_id = str(item.get("id", ""))
            title = item.get("title", "Untitled")
            dl_url = item.get("url", "")
            if not dl_url:
                continue

            lic = item.get("license", "cc")
            lic_cat = LicenseCategory.from_string(lic)
            creator = item.get("creator", "Unknown Creator")
            source = item.get("source", "Openverse")
            w = item.get("width")
            h = item.get("height")

            discovered.append(DiscoveredAsset(
                asset_id=f"openverse_{item_id}",
                provider=self.name,
                title=title,
                description=f"Source: {source} • Creator: {creator}",
                media_type=ResourceMediaType.IMAGE if endpoint == "images" else ResourceMediaType.AUDIO,
                source_page_url=item.get("foreign_landing_url", dl_url),
                download_url=dl_url,
                preview_url=item.get("thumbnail", dl_url),
                width=w,
                height=h,
                mime_type=item.get("filetype", "image/jpeg"),
                license_category=lic_cat,
                license_name=lic.upper(),
                author=creator,
                attribution_text=f"{title} by {creator} via {source} ({lic.upper()})",
                tags=[tag.get("name", "") for tag in item.get("tags", []) if isinstance(tag, dict)],
                raw_metadata=item
            ))

        return discovered[:query.limit]

    def get_asset_details(self, asset_id: str) -> Optional[DiscoveredAsset]:
        # Openverse detail query
        clean_id = asset_id.replace("openverse_", "")
        url = f"{self.base_url}/images/{clean_id}/"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                query = ResourceQuery(query=data.get("title", ""), limit=1)
                res = self.search(query)
                return res[0] if res else None
        except Exception:
            return None
