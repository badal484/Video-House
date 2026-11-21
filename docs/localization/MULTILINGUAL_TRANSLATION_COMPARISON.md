# Multilingual Translation & Cultural Adaptation Comparison

## 1. The Translation Challenge in Audiovisual Media
Subtitling and dubbing translation fundamentally differ from general text translation:
- **Spatial Constraints:** Subtitles must not exceed 37–42 characters per line and 2 lines per screen.
- **Temporal / Reading Speed Constraints:** Average audience reading speed is 15–17 characters per second (CPS) for adults, and 12 CPS for children.
- **Phonetic / Isochronic Constraints:** In dubbing, the translated speech duration must match the original speech window within $\pm 0.25$ seconds to avoid unnatural silence or rush.
- **Cultural Register & Humor:** Idiomatic expressions, sarcasm, puns, and cultural references require transcreation rather than literal word-for-word translation.

## 2. Evaluation of Translation Engines

| Engine | Type | Strengths | Weaknesses | Indic Nuance & Hinglish | Commercial License |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Meta NLLB-200** | Neural Machine Translation (Seq2Seq) | Fast, supports 200+ languages, runs locally | Lacks cinematic context, struggles with character personality and subtext | Good tokenization for Indic scripts, poor on colloquial Hinglish | CC-BY-NC 4.0 (Base) / Apache 2.0 (Distilled variants) |
| **Gemini 1.5 Flash / Pro** | Frontier Multimodal LLM | Understands full script context, speaker personas, slang, and subtitle length bounds | API latency, cost per token | **Exceptional** understanding of Hinglish, code-switching, and cultural idioms | Commercial API |
| **Claude 3.5 Sonnet / Haiku** | Frontier LLM | State-of-the-art nuanced literary and dialogue adaptation | API latency | Strong semantic and stylistic control | Commercial API |
| **DeepL Pro API** | Specialized MT | High grammatical fluency in European & East Asian languages | Limited Indic language coverage (no Hindi/Tamil), weak length constraint enforcement | Very low | Commercial API |
| **OpenNMT / MarianMT** | Local Rule + NMT | Offline, predictable latency, zero API costs | Rigid output, requires custom domain fine-tuning | Moderate | MIT |

## 3. The Studio Hybrid Translation Architecture
To deliver studio-grade localization across all tiers, Department 17 deploys a dual-mode translation strategy:
1. **Terminology & Glossary Enforcement:**
   - Pre-translation entity extraction identifies proper nouns, character names, branded terms, and technical keywords.
   - Constrained decoding or LLM system prompts strictly enforce preservation of glossary entries (e.g., ensuring "OpenUSD" is not translated to "Open American Dollars").
2. **Contextual Dialogue Transcreation:**
   - LLM-based prompting supplies context: previous 3 utterances, next 3 utterances, speaker personality, target emotion, and target duration limit.
3. **Indic Code-Switching Handling:**
   - Detects code-switched phrases and preserves intentional English vocabulary commonly spoken in modern urban India, rather than replacing them with archaic formal equivalents.
