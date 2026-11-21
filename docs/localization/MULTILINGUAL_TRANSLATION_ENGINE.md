# Multilingual Translation Engine Specification

## 1. Functional Scope
The translation engine ingests source language transcript segments and produces contextually accurate, idiomatic target language translations while strictly enforcing glossary constraints, character persona rules, and length boundaries.

## 2. Pipeline Execution Stages
1. **Glossary Term Identification & Pre-Masking:**
   - Scan source text against active project glossaries (`GlossaryTerm` entities).
   - Extract proper nouns, company names, product brands, and technical terms.
   - Tag glossary entities with protected XML spans (`<preserve id="1">Term</preserve>`).
2. **Context-Enriched Prompt Construction:**
   - Supply narrative context: genre, scene description, speaker personality, emotional state.
   - Supply previous 2 sentences and next 2 sentences to resolve pronoun references and grammatical ambiguity.
3. **Target Language Inference:**
   - Support for LLM frontier models (Gemini 1.5 Flash / Claude) and local offline NMT models (NLLB-200).
   - Strictly penalize hallucinated conversational filler.
4. **Post-Translation Validation:**
   - Verify that all protected glossary terms appear unaltered in the target translation.
   - Verify target character length complies with subtitle or dubbing timing limits.
   - For Indic languages (Hindi, Tamil, Telugu), verify script correctness (Unicode validation).
