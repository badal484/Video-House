# Ingestion REST API Documentation
**Project:** Universal AI Video Production Studio  
**Phase:** Part 02 API Reference  
**Base URL:** `http://localhost:8000/api/v1`  
**Protocol:** HTTP/1.1 & HTTP/2 with JSON payloads and Multipart File Streaming  

---

## 1. Project Management

### Create Project
- **Method:** `POST /api/v1/projects`
- **Request Body:**
  ```json
  {
    "name": "Cyberpunk Short Film",
    "settings": {
      "timeline_fps": 24.0,
      "canvas_width": 3840,
      "canvas_height": 2160,
      "color_space": "ACEScg"
    }
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "project_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "name": "Cyberpunk Short Film",
    "created_at": "2026-11-21T16:30:00Z",
    "updated_at": "2026-11-21T16:30:00Z",
    "settings": { ... }
  }
  ```

---

## 2. Media Upload & Ingestion

### Multipart Stream Upload
- **Method:** `POST /api/v1/projects/{project_id}/assets/upload`
- **Content-Type:** `multipart/form-data`
- **Form Parameters:**
  - `file`: Binary file stream (Required)
  - `display_name`: String (Optional)
  - `role`: String enum (Optional, default `SOURCE_FOOTAGE`)
- **Response:** `202 Accepted`
  ```json
  {
    "success": true,
    "message": "Asset uploaded and queued for processing.",
    "asset_id": "98765432-abcd-ef01-2345-6789abcdef01",
    "status": "QUEUED"
  }
  ```

### Local Path Import
- **Method:** `POST /api/v1/projects/{project_id}/assets/import-local`
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "file_path": "/Volumes/MediaDrive/Rushes/take_01.mov",
    "display_name": "Take 01 Main Camera",
    "roles": ["SOURCE_FOOTAGE", "REFERENCE_VIDEO"]
  }
  ```
- **Response:** `202 Accepted`
  ```json
  {
    "success": true,
    "message": "Local file imported and queued for processing.",
    "asset_id": "11223344-5566-7788-99aa-bbccddeeff00",
    "status": "QUEUED"
  }
  ```

---

## 3. Asset Query & Retrieval

### List Project Assets
- **Method:** `GET /api/v1/projects/{project_id}/assets`
- **Query Parameters:**
  - `media_type`: `VIDEO`, `AUDIO`, `IMAGE`, `SUBTITLE`, `ANIMATION`, `THREE_D` (Optional)
  - `role`: Asset role filter (Optional)
  - `status`: `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED` (Optional)
  - `limit`: Integer (Default 50, Max 200)
  - `offset`: Integer (Default 0)
- **Response:** `200 OK`
  ```json
  {
    "project_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "count": 1,
    "limit": 50,
    "offset": 0,
    "assets": [ ... ]
  }
  ```

### Get Asset Details & Technical Metadata
- **Method:** `GET /api/v1/projects/{project_id}/assets/{asset_id}`
- **Response:** `200 OK`
  ```json
  {
    "asset_id": "98765432-abcd-ef01-2345-6789abcdef01",
    "project_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "original_filename": "take_01.mov",
    "display_name": "Take 01 Main Camera",
    "media_type": "VIDEO",
    "detected_format": "mov",
    "mime_type": "video/quicktime",
    "byte_size": 48291040,
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "processing_status": "COMPLETED",
    "roles": ["SOURCE_FOOTAGE"],
    "technical_metadata": {
      "width": 3840,
      "height": 2160,
      "duration_seconds": 12.5,
      "frame_rate": 24.0,
      "video_codec": "prores",
      "audio_codec": "pcm_s24le",
      "pixel_format": "yuv422p10le",
      "bit_depth": 10,
      "is_hdr": false,
      "timecode": "01:00:00:00"
    },
    "derivatives": [
      {
        "derivative_type": "THUMBNAIL",
        "storage_path": "assets/.../thumbnail.jpg",
        "mime_type": "image/jpeg"
      },
      {
        "derivative_type": "PROXY_VIDEO",
        "storage_path": "assets/.../proxy_prores.mov",
        "mime_type": "video/quicktime"
      }
    ]
  }
  ```

---

## 4. Asset Modification & Safe Deletion

### Update Display Name & Roles
- **Method:** `PATCH /api/v1/projects/{project_id}/assets/{asset_id}`
- **Request Body:**
  ```json
  {
    "display_name": "Updated Scene Name",
    "add_roles": ["REFERENCE_VIDEO"],
    "remove_roles": ["SOURCE_FOOTAGE"]
  }
  ```

### Safe Asset Deletion
- **Method:** `DELETE /api/v1/projects/{project_id}/assets/{asset_id}`
- **Response:**
  - `200 OK`: Asset and physical files deleted.
  - `409 Conflict`: Deletion blocked because another timeline clip or dependent asset references it.

### Retry Failed Processing
- **Method:** `POST /api/v1/projects/{project_id}/assets/{asset_id}/retry`
- **Response:** `200 OK` with new `job_id`.

