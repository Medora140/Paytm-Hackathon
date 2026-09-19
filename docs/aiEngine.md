# ML / AI Engine — Component Spec

**Role:** This is the "brain" — it turns extracted document chunks into a plain-language summary, a list of red flags with citations, a confidence score, and grounded Q&A answers, a **fine-tuned clause-classification model** is worth doing properly (see §2a) rather than falling back to rules-only — just keep the rule-based detector as a fast, explainable complement/fallback rather than replacing it entirely, since the two catch slightly different things (rules catch known exact patterns instantly; a fine-tuned model generalizes to phrasing it hasn't seen before).
## Redact:

PII is redacted before any document chunk is transmitted to Gemini. The redaction scope includes personal names, DOB, contact information, addresses, policy/customer/account identifiers, and government/financial identifiers. Ordinary financial values and domain terminology such as premium, EMI, rent, loan amount, interest rate, coverage amount, and tenure are retained. Redaction uses field-aware and validated pattern matching rather than substring replacement.

## 1. Plain-language summary generator

**Approach:** Single structured LLM call per document (Gemini), not a custom model.
- Input: full extracted text (or the top N chunks by section importance if the doc is very long) + a strict prompt template requesting a fixed schema: `{coverage: [...], exclusions: [...], key_fees: [...], waiting_periods: [...], notable_terms: [...]}`.
- Output is rendered directly into the Summary card on the frontend.
- Tune prompts per document type (insurance vs. loan vs. mutual fund) — the pitch deck's "perfectly tuned to the specific document type" claim should map to distinct prompt templates, not one generic prompt.
- Support English/Hindi by asking the model to output in the requested language rather than maintaining separate pipelines.

## 2. Red-Flag & Dispute Detector

This is the most defensible, judge-impressing piece — treat it as rules-plus-retrieval, not a black box.

**Data foundation:** a **Red-Flag Knowledge Base** — a curated list of clause *patterns* known to cause disputes, each with:
```
{
  "pattern_id": "...",
  "category": "insurance|lending|fintech",
  "clause_type": "e.g. room_rent_cap, pre_existing_exclusion, prepayment_penalty, exit_load",
  "trigger_keywords": [...],
  "trigger_regex": "optional",
  "plain_explanation": "why this causes disputes",
  "severity_default": "high|medium|low",
  "source": "IRDAI/RBI ombudsman report reference or public dataset"
}
```
- **Seed this from real public sources**: IRDAI annual reports / Insurance Ombudsman case summaries, RBI Banking Ombudsman scheme reports, and consumer-complaint aggregators. This is public data — cite it, don't fabricate statistics.
- **Detection pipeline per document:**
  1. Run keyword/regex matching from the KB against document chunks (fast, deterministic, explainable — this alone gives you a working demo).
  2. For ambiguous matches, use the LLM as a *classifier with the chunk + candidate pattern as input*, asking it to confirm/deny + explain in one sentence, rather than asking it to find red flags unconstrained (constrained classification hallucinates far less than open-ended "find problems in this text").
  3. Attach exact source text + page number to every flagged clause (this is what the citation UI in `01-frontend.md` renders).

## 2a. Fine-tuning a clause-classification model

**Task framing:** don't frame this as "detect red flags" end-to-end in one model — frame it as **multi-label clause classification**: given a chunk of text (one clause), predict which of your `clause_type` categories it belongs to (`room_rent_cap`, `pre_existing_exclusion`, `prepayment_penalty`, `exit_load`, `co_pay`, etc., plus a `none`/benign class). This is a well-understood, tractable fine-tuning task — much more tractable than trying to fine-tune a model to freely generate red-flag explanations.

**Data — this is the actual hard part, budget the most time here:**
1. **Bootstrap labels with your rule-based detector.** Run the keyword/regex detector from §2 across every clause of every document you can get your hands on (real policy wordings you can legally access, sample/specimen policies insurers publish publicly, synthetic clauses you write yourself covering each category). This gives you a first pass of labels for free.
2. **Manually correct a sample.** Have your team review a few hundred of the auto-labeled clauses and fix mislabels — this is what actually makes the fine-tuned model better than the rules it was bootstrapped from.
3. **Augment thin classes.** For clause types you don't have many real examples of, write synthetic paraphrases (varying phrasing, formality, insurer-specific wording) rather than leaving a class with 5 examples.
4. **Aim for at least 50–100 labeled examples per class** as a rough floor for a workable fine-tune; more is better, but see the SetFit option below if you can't reach that.

**Model candidates (all freely available, no license fee):**

| Model | Why it fits | Where to get it |
|---|---|---|
| `microsoft/deberta-v3-base` | Strong general-purpose classification backbone, good accuracy/size tradeoff, the standard choice for this kind of task in 2025–26 | Hugging Face Hub |
| `law-ai/InLegalBERT` | Pretrained specifically on Indian legal text — a strong prior for insurance/loan clause language specifically, likely to need less labeled data than a generic model | Hugging Face Hub |
| `ProsusAI/finbert` | Financial-domain pretraining; more useful if you also want tone/risk-sentiment signals, less directly aimed at clause-type classification than InLegalBERT | Hugging Face Hub |
| `google/muril-base-cased` | Multilingual, strong on Indian languages including Hindi — pick this if you want **one model** that classifies clauses in both English and Hindi documents rather than maintaining two pipelines | Hugging Face Hub |
| `sentence-transformers/all-MiniLM-L6-v2` or `BAAI/bge-base-en-v1.5` | Not a classifier itself, but the backbone for the SetFit approach below, and also your embedding model for RAG (§4) — reusing it for both saves you running two models | Hugging Face Hub |

**Two fine-tuning approaches, pick based on how much labeled data you actually end up with:**

- **Classic fine-tuning (Hugging Face `transformers` `Trainer`)** — if you get to a few hundred+ examples per class. Add a classification head on top of DeBERTa-v3-base or InLegalBERT, fine-tune end-to-end. This is the standard, well-documented path (Hugging Face's own fine-tuning tutorials cover this exact multi-label text classification setup).
- **SetFit (few-shot fine-tuning of sentence-transformers)** — if you're realistically going to have only tens of examples per class, which is likely given the timeline. SetFit is specifically designed for this regime: it fine-tunes a sentence-transformer with contrastive pairs generated from your small labeled set, then trains a lightweight classification head on top. It routinely gets strong accuracy from 8–64 examples per class where classic fine-tuning would underfit or overfit. It's an open-source Hugging Face library (`setfit`) and is the more realistic choice if data collection is your bottleneck.
- **LoRA/PEFT** is not really necessary at this model size (base/large BERT-class models fine-tune fully on modest hardware) — save LoRA for if you later move to a much larger backbone.

**Practical steps:**
1. Export labeled clauses to a simple CSV/JSONL: `{text, labels: [clause_type, ...]}`.
2. Split train/validation/test (e.g., 70/15/15), stratified by class so rare classes appear in all three splits.
3. Fine-tune (Trainer or SetFit as above); track per-class precision/recall/F1, not just overall accuracy — a model that's great on `exit_load` but blind to `pre_existing_exclusion` looks fine on aggregate accuracy and is useless in practice.
4. Export the fine-tuned model (Hugging Face format, optionally converted to ONNX for faster CPU inference if you're not running a GPU in production).
5. **Serve it as its own small inference service** (FastAPI endpoint wrapping the model, or a Hugging Face Inference Endpoint) that the backend's ML analysis service (§2) calls per-chunk, in addition to — not instead of — the keyword/regex rules.
6. Feed the trained model's predictions into the same red-flag output schema as the rule-based detector (`pattern_id`/`clause_type`, `confidence`, source chunk) so the rest of the pipeline (citations, confidence score, frontend) doesn't need to know which detection method fired.

**Retraining loop:** once real usage starts, log cases where the LLM-based confirmation step (§2 step 2) disagrees with the fine-tuned model, or where a user disputes a flagged clause — that disagreement set is your highest-value future training data, and ties naturally into the n8n `re-analyze-on-kb-update` workflow if you also add a `retrain-on-new-labels` variant later.

## 3. Confidence Score

Even with a fine-tuned classifier in place, keep the score itself a **transparent weighted formula** rather than a single opaque model output — the score's job is to be explainable to a user with no ML background, and "the model said 68" is not an explanation.

Suggested formula:
```
score = 100
      - (Σ severity_weight for each red flag: high=15, medium=8, low=3)
      - (benchmark_penalty: points off if key terms are worse than scraped comparables)
      + (transparency_bonus: small bonus if doc has fewer ambiguous/hard-to-parse clauses)
clamp(score, 0, 100)
```
- Feed the fine-tuned model's per-clause outputs into this formula the same way rule-based flags are: each confirmed red flag (regardless of which detector found it) contributes its `severity_weight`. This keeps the formula itself simple and auditable even as the detection layer underneath gets more sophisticated.
- Always return the breakdown (which flags cost how many points) alongside the number — an unexplained score is not trustworthy and won't survive a judge's first question.
- Longer-term roadmap item (matches your own roadmap slide): once you have enough labeled *outcomes* (claim approved/rejected vs. score, not just clause labels), a model that predicts outcome risk directly could inform or replace the formula's weights — that's a distinct, larger effort from the clause-classifier in §2a, since it needs outcome data you likely don't have yet.

## 4. Conversational Q&A (RAG)

**Pipeline:**
1. Embed the user's question (same embedding model used at ingestion).
2. Vector similarity search over the document's own chunks (pgvector) — top 3–5 chunks.
3. Construct an LLM prompt: system instruction to answer *only* from provided chunks, always cite page/clause, and explicitly say "not found in this document" if the answer isn't supported.
4. Return answer + the chunk IDs/pages used, so the frontend can render citation chips.

**Guardrails specific to this feature:**
- Never let the model answer from general knowledge about "typical" insurance policies when the user asks about *their* document — this is the single biggest hallucination risk and directly undermines the product's trust promise.
- Add a lightweight moderation/scope check: if a user asks something unrelated to the document (e.g., general medical advice), redirect rather than answer.

## 5. Models & tools summary

| Task | Tool |
|---|---|
| OCR | Tesseract (open-source) or a hosted OCR API if budget allows |
| Text extraction (native PDFs) | pypdf / pdfplumber |
| Chunking | Custom rule-based splitter on headers/clause numbering + fallback fixed-window chunking |
| Embeddings | `text-embedding-3-small`-class model or an open-source sentence-transformer (keep cost low; embeddings run per chunk at ingest time, which is the highest-volume LLM-adjacent cost) |
| Clause classification | Fine-tuned DeBERTa-v3-base / InLegalBERT / MuRIL, or SetFit on a sentence-transformer backbone — see §2a |
| Reasoning/generation | Gemini API (free tier) |
| Vector search | pgvector inside Postgres |

## 6. Evaluation

Build a proper held-out test set (not just a handful of documents eyeballed at the end): real or realistic sample policies with manually identified red flags, split off *before* fine-tuning and never used in training. Report per-class precision/recall/F1 for the fine-tuned classifier (§2a), not just an aggregate accuracy or a single "recall on our eval set" number — a concrete, class-by-class result is both the right way to catch a model that's silently bad on rare classes, and a far more credible claim to present than an unsubstantiated confidence score.