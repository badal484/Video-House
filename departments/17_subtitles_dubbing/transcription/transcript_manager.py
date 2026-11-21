"""
Transcript Manager for Department 17.
Maintains canonical transcript state, supports segment splitting, manual corrections,
confidence filtering, and export/import.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from ..core.models import Transcript, TranscriptSegment, WordTimestamp


class TranscriptManager:
    """Manages transcript editing, segment splitting, merging, and search."""

    @staticmethod
    def edit_segment(
        transcript: Transcript,
        segment_id: UUID,
        new_text: str,
        editor: str = "human_operator",
    ) -> bool:
        """Applies a manual correction to a segment, tracking audit history."""
        for seg in transcript.segments:
            if seg.segment_id == segment_id:
                if seg.original_text is None:
                    seg.original_text = seg.text
                seg.text = new_text.strip()
                seg.is_manual_edit = True
                seg.confidence = 1.0
                return True
        return False

    @staticmethod
    def split_segment(
        transcript: Transcript,
        segment_id: UUID,
        split_at_word_index: int,
    ) -> Optional[tuple[TranscriptSegment, TranscriptSegment]]:
        """Splits a single segment into two at the designated word index."""
        for idx, seg in enumerate(transcript.segments):
            if seg.segment_id == segment_id:
                if split_at_word_index <= 0 or split_at_word_index >= len(seg.words):
                    return None

                words_a = seg.words[:split_at_word_index]
                words_b = seg.words[split_at_word_index:]

                seg_a = TranscriptSegment(
                    start_time=words_a[0].start_time,
                    end_time=words_a[-1].end_time,
                    text=" ".join(w.word for w in words_a),
                    speaker_id=seg.speaker_id,
                    words=words_a,
                    confidence=seg.confidence,
                )
                seg_b = TranscriptSegment(
                    start_time=words_b[0].start_time,
                    end_time=words_b[-1].end_time,
                    text=" ".join(w.word for w in words_b),
                    speaker_id=seg.speaker_id,
                    words=words_b,
                    confidence=seg.confidence,
                )

                transcript.segments.pop(idx)
                transcript.segments.insert(idx, seg_a)
                transcript.segments.insert(idx + 1, seg_b)
                return seg_a, seg_b
        return None

    @staticmethod
    def merge_segments(
        transcript: Transcript,
        segment_id_a: UUID,
        segment_id_b: UUID,
    ) -> Optional[TranscriptSegment]:
        """Merges two contiguous segments into one."""
        idx_a = next((i for i, s in enumerate(transcript.segments) if s.segment_id == segment_id_a), None)
        idx_b = next((i for i, s in enumerate(transcript.segments) if s.segment_id == segment_id_b), None)

        if idx_a is None or idx_b is None or abs(idx_a - idx_b) != 1:
            return None

        first_idx, second_idx = sorted([idx_a, idx_b])
        seg1 = transcript.segments[first_idx]
        seg2 = transcript.segments[second_idx]

        combined_words = seg1.words + seg2.words
        merged = TranscriptSegment(
            start_time=seg1.start_time,
            end_time=seg2.end_time,
            text=f"{seg1.text} {seg2.text}",
            speaker_id=seg1.speaker_id,
            words=combined_words,
            confidence=min(seg1.confidence, seg2.confidence),
        )

        transcript.segments.pop(second_idx)
        transcript.segments.pop(first_idx)
        transcript.segments.insert(first_idx, merged)
        return merged

    @staticmethod
    def get_full_text(transcript: Transcript) -> str:
        """Returns concatenated plain text transcript."""
        return " ".join(s.text for s in transcript.segments)

    @staticmethod
    def search_transcript(transcript: Transcript, query: str) -> List[TranscriptSegment]:
        """Finds all segments containing the query substring (case-insensitive)."""
        q = query.lower()
        return [s for s in transcript.segments if q in s.text.lower()]
