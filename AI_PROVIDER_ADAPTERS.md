# AI Multimodal Provider Adapters & Routing Architecture

**Document Version:** 1.0.0  
**Status:** Approved & Implemented  
**Department:** `departments/05_multimodal_providers`  

---

## 1. Adapter Abstraction & Interface Contracts

To prevent vendor lock-in and enable transparent switching between cloud foundation models (Gemini 2.0 Flash, TwelveLabs Pegasus) and local machine processing (OpenCV, faster-whisper, SciPy), Department 05 defines unified interface contracts (`departments/05_multimodal_providers/interface.py`).

### Standard Contracts:
- `IVideoUnderstandingProvider`:
  - `async def analyze_video(video_path: Path, prompt: str, ...) -> VideoAnalysisResult`
  - `async def compare_videos(video_a: Path, video_b: Path, comparison_prompt: str) -> Dict[str, Any]`
  - `def health_check() -> bool`
- `ISpeechProvider`:
  - `async def transcribe(audio_path: Path, language: Optional[str]) -> Dict[str, Any]`
- `IEmbeddingProvider`:
  - `async def embed_text(text: str) -> List[float]`
  - `async def embed_video(video_path: Path) -> List[float]`
- `IMultimodalProviders`:
  - `async def execute(request: MultimodalProvidersRequest) -> MultimodalProvidersResponse`

---

## 2. Implemented Provider Adapters

### 1. `GeminiProvider` (`gemini_provider.py`)
- **Cloud Models:** `gemini-2.0-flash` (default), `gemini-1.5-pro`.
- **Protocol:** Asynchronous REST client via `httpx.AsyncClient` targeting Google Generative Language API.
- **Offline Simulation Mode:** Automatically engages when `GEMINI_API_KEY` is absent or offline testing is requested. Emits structured temporal events, summary, and token accounting without throwing errors.
- **Cost Accounting:** Tracks input/output tokens and writes cost USD to responses.

### 2. `TwelveLabsProvider` (`twelvelabs_provider.py`)
- **Cloud Models:** `marengo-2.6` (semantic search and 512-dim video embeddings), `pegasus-1.1` (video-to-text and reasoning).
- **Protocol:** Asynchronous REST client via `httpx` to `https://api.twelvelabs.io/v1.2/`.
- **Embeddings:** Generates normalized 512-dimensional vector representations.
- **Offline Simulation:** Includes SHA-256 pseudo-embedding vector generation for unit tests.

### 3. `LocalMultimodalProvider` (`local_provider.py`)
- **On-Device Toolchain:** PySceneDetect cuts, Farneback optical flow, OpenCV MOG2 object tracking, SciPy audio onset envelopes, and faster-whisper speech recognition.
- **Privacy & Cost:** 100% on-device (Apple Silicon M4 CPU), zero cloud data egress, $0.00 API cost.

### 4. `MultimodalProviderRouter` (`router.py`)
- Implements `ProviderRoutingMode`:
  - `LOCAL_FIRST`: Dispatches deterministic extraction to local engine, reserving cloud calls for deep reasoning.
  - `LOCAL_ONLY`: Strictly prohibits external network requests (high privacy/offline work).
  - `CLOUD_ONLY`: Directs queries exclusively to Gemini or TwelveLabs.
  - `COST_OPTIMIZED`: Minimizes API expenditures.
