# Rendering & Quality Control Test Report & Verification

## 1. Test Suite Architecture
The test suite in `tests/unit/test_rendering_delivery.py` provides end-to-end verification of Department 18 (`quality_control`) and Department 19 (`rendering_delivery`), honoring all 35 required acceptance criteria:
1. Validate complete production project.
2. Detect missing source media.
3. Detect missing font.
4. Detect missing LUT.
5. Compile valid render plan DAG.
6. Reject invalid render plan.
7. Render simple video sequence.
8. Render multitrack sequence.
9. Render sequence with transitions.
10. Render motion graphics.
11. Render VFX composition.
12. Render 2D animation sequence.
13. Submit Part 09 3D rendering task.
14. Render sequence with graded footage.
15. Render HDR workflow where supported.
16. Export professional master (ProRes 422 HQ).
17. Export social media delivery profile (YouTube / Reels).
18. Export subtitles and multiple audio tracks.
19. Validate audio loudness (EBU R128).
20. Detect black frames.
21. Detect frozen frames.
22. Detect corrupted media file.
23. Detect incorrect resolution.
24. Detect incorrect frame rate.
25. Validate color metadata (NCLX).
26. Validate subtitle timing (CPS, CPL).
27. Detect audio/video synchronization errors.
28. Generate technical QC report.
29. Fail job when critical QC rule fails.
30. Recover interrupted render job from checkpoint.
31. Retry failed task with exponential backoff.
32. Validate final file SHA-256 checksum.
33. Generate machine-readable delivery manifest.
34. Create complete delivery package.
35. Verify original source media remains unchanged.

## 2. Test Execution Baseline
- **Platform:** macOS Sonoma, Apple M4, 16GB RAM.
- **Python:** 3.11.
- **Target Pass Rate:** 100% pass across all 35 acceptance tests without regressions to prior 179 studio platform tests.

