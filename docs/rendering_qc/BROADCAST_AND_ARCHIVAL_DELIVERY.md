# Broadcast and Archival Delivery Specification

## 1. Broadcast Playout Standards
Broadcast playout servers require strict adherence to file wrappers, stream layouts, continuous timecodes, and legislated loudness compliance (CALM Act, EBU R128).

## 2. Implemented Broadcast & Preservation Profiles

### 2.1 Broadcast MXF OP1a Delivery (`broadcast_mxf_op1a`)
- **Container:** Material Exchange Format OP1a (`.mxf`)
- **Video Codec:** XDCAM HD422 (MPEG-2 50Mbps 4:2:2) or AVC-Intra 100
- **Audio Codec:** Uncompressed 24-bit 48kHz Linear PCM
- **Audio Channel Layout:** 8 discrete channels (Tracks 1-2: Stereo Lt/Rt, Tracks 3-8: 5.1 Surround)
- **Loudness Compliance:** Exactly $-23.0\text{ LUFS} \pm 0.5\text{ LUFS}$ (EBU R128)
- **Timecode:** Continuous non-drop frame timecode track starting at `01:00:00:00` (1-hour program start convention)

### 2.2 Digital Preservation Archival Master (`archival_ffv1_mkv`)
- **Container:** Matroska (`.mkv`) with CRC32 packet checksums
- **Video Codec:** FFV1 Version 3 (Lossless intra-frame video compression)
- **Pixel Format:** `yuv422p10le` (or `yuv444p16le`)
- **Audio Codec:** Uncompressed 24-bit 48kHz PCM
- **Metadata:** Embedded MediaConch compliance policy and C2PA provenance manifest
- **Use Case:** Long-term archival preservation (FIAF / Library of Congress)

