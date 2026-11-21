"""
Semantic Search and Multimodal Media Retrieval Service.
Combines transcript full-text search, structured visual/camera filters,
and semantic query decomposition across analyzed media.
"""
import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from core.assets.database import AssetDatabase
from core.assets.intelligence_models import (
    AudioEventType,
    CameraMotionType
)

logger = logging.getLogger("studio.semantic_search")

class SemanticSearchService:
    def __init__(self, db: AssetDatabase):
        self.db = db

    def search_project_media(
        self,
        project_id: UUID,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search across transcripts, detected objects, camera movements, and audio events.
        """
        results: List[Dict[str, Any]] = []
        clean_query = query.strip().lower()
        query_tokens = set(re.findall(r'\w+', clean_query))

        # 1. Full-Text Search on Transcripts
        with self.db.get_connection() as conn:
            transcript_rows = conn.execute("""
                SELECT t.*, a.original_filename, a.display_name
                FROM transcripts t
                JOIN assets a ON t.asset_id = a.asset_id
                WHERE a.project_id = ? AND lower(t.text) LIKE ?
                LIMIT ?
            """, (str(project_id), f"%{clean_query}%", limit)).fetchall()

            for r in transcript_rows:
                results.append({
                    "asset_id": r["asset_id"],
                    "asset_name": r["display_name"] or r["original_filename"],
                    "match_type": "TRANSCRIPT_SPEECH",
                    "start_seconds": r["start_sec"],
                    "end_seconds": r["end_sec"],
                    "headline": f"Spoken Dialogue: \"{r['text']}\"",
                    "speaker_id": r["speaker_id"],
                    "relevance_score": 0.95,
                    "evidence": {
                        "matched_text": r["text"],
                        "confidence": r["confidence"]
                    }
                })

        # 2. Structured Object Detection Search
        # Check if query mentions common detected labels (e.g. "person", "car", "face")
        detected_labels = ["person", "car", "vehicle", "chair", "table", "dog", "cat"]
        matched_labels = [l for l in detected_labels if l in query_tokens]

        if matched_labels:
            with self.db.get_connection() as conn:
                for lbl in matched_labels:
                    obj_rows = conn.execute("""
                        SELECT d.*, a.original_filename, a.display_name
                        FROM detected_objects d
                        JOIN assets a ON d.asset_id = a.asset_id
                        WHERE a.project_id = ? AND d.label = ?
                        ORDER BY d.confidence DESC
                        LIMIT ?
                    """, (str(project_id), lbl, limit)).fetchall()

                    for r in obj_rows:
                        results.append({
                            "asset_id": r["asset_id"],
                            "asset_name": r["display_name"] or r["original_filename"],
                            "match_type": "VISUAL_OBJECT_DETECTION",
                            "start_seconds": r["timestamp_sec"],
                            "end_seconds": r["timestamp_sec"] + 1.0,
                            "headline": f"Detected Visual Subject: {r['label'].capitalize()}",
                            "relevance_score": round(float(r["confidence"]), 2),
                            "evidence": {
                                "track_id": r["track_id"],
                                "frame_number": r["frame_number"],
                                "bounding_box": r["box_json"]
                            }
                        })

        # 3. Camera Movement Search
        motion_keywords = {
            "pan": ["PAN_LEFT", "PAN_RIGHT"],
            "tilt": ["TILT_UP", "TILT_DOWN"],
            "zoom": ["ZOOM_IN", "ZOOM_OUT"],
            "dolly": ["DOLLY_IN", "DOLLY_OUT"],
            "static": ["STATIC"],
            "handheld": ["HANDHELD_JITTER"],
            "tracking": ["TRACKING"]
        }
        for kw, motion_types in motion_keywords.items():
            if kw in query_tokens:
                with self.db.get_connection() as conn:
                    for mt in motion_types:
                        cam_rows = conn.execute("""
                            SELECT c.*, a.original_filename, a.display_name
                            FROM camera_movements c
                            JOIN assets a ON c.asset_id = a.asset_id
                            WHERE a.project_id = ? AND c.motion_type = ?
                            LIMIT ?
                        """, (str(project_id), mt, limit)).fetchall()

                        for r in cam_rows:
                            results.append({
                                "asset_id": r["asset_id"],
                                "asset_name": r["display_name"] or r["original_filename"],
                                "match_type": "CINEMATOGRAPHY_CAMERA_MOTION",
                                "start_seconds": r["start_sec"],
                                "end_seconds": r["end_sec"],
                                "headline": f"Camera Movement: {r['motion_type']}",
                                "relevance_score": round(float(r["confidence"]), 2),
                                "evidence": {
                                    "magnitude": r["magnitude"],
                                    "direction": r["direction_json"]
                                }
                            })

        # 4. Audio Event & Music Search
        if any(w in query_tokens for w in ["music", "song", "beat", "audio", "sound"]):
            with self.db.get_connection() as conn:
                music_rows = conn.execute("""
                    SELECT m.*, a.original_filename, a.display_name
                    FROM music_segments m
                    JOIN assets a ON m.asset_id = a.asset_id
                    WHERE a.project_id = ?
                    LIMIT ?
                """, (str(project_id), limit)).fetchall()

                for r in music_rows:
                    results.append({
                        "asset_id": r["asset_id"],
                        "asset_name": r["display_name"] or r["original_filename"],
                        "match_type": "ACOUSTIC_MUSIC",
                        "start_seconds": r["start_sec"],
                        "end_seconds": r["end_sec"],
                        "headline": f"Music Score: {r['tempo_bpm']} BPM ({r['mood']})",
                        "relevance_score": round(float(r["confidence"]), 2),
                        "evidence": {
                            "tempo_bpm": r["tempo_bpm"],
                            "rhythmic_energy": r["rhythmic_energy"]
                        }
                    })

        # 5. On-Screen Text / OCR Search
        with self.db.get_connection() as conn:
            ocr_rows = conn.execute("""
                SELECT o.*, a.original_filename, a.display_name
                FROM ocr_observations o
                JOIN assets a ON o.asset_id = a.asset_id
                WHERE a.project_id = ? AND lower(o.text) LIKE ?
                LIMIT ?
            """, (str(project_id), f"%{clean_query}%", limit)).fetchall()

            for r in ocr_rows:
                results.append({
                    "asset_id": r["asset_id"],
                    "asset_name": r["display_name"] or r["original_filename"],
                    "match_type": "ON_SCREEN_OCR",
                    "start_seconds": r["timestamp_sec"],
                    "end_seconds": r["timestamp_sec"] + 1.0,
                    "headline": f"On-Screen Typography: \"{r['text']}\"",
                    "relevance_score": 0.90,
                    "evidence": {
                        "category": r["text_category"],
                        "bounding_box": r["box_json"]
                    }
                })

        # Sort results by relevance score descending
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]

