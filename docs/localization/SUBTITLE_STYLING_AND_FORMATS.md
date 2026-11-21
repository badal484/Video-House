# Subtitle Styling and Formats Specification

## 1. Visual Styling Taxonomy & Design Presets
Modern video consumption spans classical cinematic viewing, high-contrast web players, and dynamic social media reels with animated typography. The `SubtitleStyler` provides standard presets:

### 1.1 Preset Profiles
1. **Cinematic Standard:**
   - Font: Inter / Arial / Helvetica Neue.
   - Size: 24pt (1080p canvas).
   - Color: Off-white (`#F0F0F0`) with 2px semi-transparent black drop shadow or stroke (`#00000080`).
   - Placement: Bottom center, 8% safe-zone margin.
2. **Social Media / Reels Kinetic:**
   - Font: Montserrat Bold / Futura Heavy.
   - Size: 38pt, all-caps.
   - Fill: Bright Yellow (`#FFDE00`) or White with thick black border (4px).
   - Placement: Screen center (vertical middle) or 35% from bottom.
   - Effect: Word-by-word karaoke highlight tag (`{\k<duration>}`) where the currently spoken word illuminates with a bright accent color.
3. **Accessibility / SDH High Contrast:**
   - Font: Tiresias / Roboto.
   - Background: Solid black bounding box with 80% opacity.
   - Color: White text, with speaker-differentiated colors (e.g. Yellow for Speaker 1, Cyan for Speaker 2).

## 2. Video Safe Zone Conformance
All rendered and formatted subtitles honor SMPTE and broadcast safe-title areas:
- Title Safe Area: Within 80% of screen width and height.
- Action Safe Area: Within 90% of screen width and height.
- Dynamic adjustments lift subtitles up if lower-third title cards or on-screen graphics are detected in Department 06/09.
