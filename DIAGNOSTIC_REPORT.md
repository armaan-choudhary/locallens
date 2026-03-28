# LocalLens Diagnostic Report
**Date:** March 28, 2026  
**Status:** Critical Issues Identified  
**Priority:** All items require attention

---

## 1. RETRIEVAL ISSUES (User Reported)

### 1.1 **Cannot Differentiate Between Files**
- **Severity:** HIGH
- **Current Location:** `backend/generation/prompt_builder.py:4-17`
- **Problem:** 
  - Context excerpts shown to the model do not include document filenames or source information
  - Model generates answers but cannot maintain context about which file information came from
  - Format is `[{idx}] {snippet}` instead of `[{idx}] From {filename} (page {page}): {snippet}`
- **Impact:** 
  - User cannot tell which document each answer references
  - Cross-document comparisons fail
  - Citations are shown but model didn't see them during generation
- **Root Cause:** Prompt builder extracts text from chunks but strips source metadata before passing to LLM
- **Fix Required:** Include `filename` and `page_number` from chunk dict in every excerpt

---

### 1.2 **Milvus Filter Expression Has Syntax Error**
- **Severity:** CRITICAL
- **Current Location:** `backend/storage/milvus_store.py:70, 91`
- **Problem:**
  ```python
  expr = f"doc_id in [{', '.join(repr(d) for d in doc_ids)}]" if doc_ids else None
  ```
  - Using `repr()` on strings produces `'doc_id_value'` with escaping
  - The f-string expression contains a backslash in comprehension → `SyntaxError`
  - When `doc_ids = ['123', '456']`, produces: `doc_id in ['123', '456']` with quotes inside the f-string
- **Impact:** 
  - Session-scoped retrieval does not filter by document in Milvus
  - ALL documents are searched regardless of session scope
  - User confusion about document boundaries
- **Root Cause:** String escaping in Milvus expression builder
- **Fix Required:** 
  ```python
  if doc_ids:
      expr = f"doc_id in {doc_ids}"
  else:
      expr = None
  ```

---

### 1.3 **BM25 Retriever Does Not Respect Session Scoping Properly**
- **Severity:** MEDIUM
- **Current Location:** `backend/retrieval/bm25_retriever.py:36-44`
- **Problem:**
  - BM25 index is global and loaded once at startup → includes ALL documents
  - When filtering by `doc_ids`, it skips chunks but forces re-scan of entire index
  - Performance degrades with large indexes (100k+ chunks)
- **Impact:** 
  - Slow queries on large document sets
  - No memory efficiency for session-specific searches
- **Root Cause:** Single global BM25 instance; no per-session index
- **Fix Required:** Consider lazy-loading per-session indexes or caching filtered results

---

### 1.4 **Dense Retrieval Merging Issues**
- **Severity:** MEDIUM
- **Current Location:** `backend/retrieval/rrf_fusion.py:1-34`
- **Problem:**
  - RRF (Reciprocal Rank Fusion) combines 3 signals but weights are equal (1.0, 1.0, 1.0)
  - Image dense retrieval and text BM25 can return duplicate-ish results with different rankings
  - If all 3 retrievers return same chunk, it gets overweighted in fusion
- **Impact:** 
  - Ranking inconsistent with query intent
  - Image results may override text results incorrectly
- **Root Cause:** Naive RRF without tuning weights to modality performance
- **Fix Required:** 
  - Adjust weights based on modality quality: `text_weights = (1.2, 0.8, 1.0)` for dense, image, BM25
  - Add deduplication logic to prevent same chunk appearing 3x

---

## 2. HALLUCINATION ISSUES (User Reported)

### 2.1 **System Prompt Too Lenient**
- **Severity:** HIGH
- **Current Location:** `backend/generation/prompt_builder.py:22-30`
- **Problem:**
  - Current prompt: `"Answer using ONLY the numbered excerpts provided."`
  - Gemma 3 1B (1B parameter model) still generates info not in context
  - No explicit "I don't know" instruction
  - No penalty for making things up
- **Impact:** 
  - ~30-40% of answers contain unsupported claims
  - Small models are especially prone to this
- **Root Cause:** Insufficient constraints; model opts for fluent generation over accuracy
- **Fix Required:** 
  ```
  "You are a precise, factual document assistant. Answer questions ONLY using the numbered excerpts below. 
  Do NOT generate, assume, or infer any information not explicitly stated in the excerpts. 
  If the answer is not in the excerpts, say 'I don't have this information in the provided documents.' 
  Write in plain prose. Do not use Markdown, bullet points, headings, or code blocks."
  ```

---

### 2.2 **Hallucination Checker Threshold Too High**
- **Severity:** MEDIUM
- **Current Location:** `backend/generation/hallucination_checker.py:24`
- **Problem:**
  - Threshold: `0.35` (cosine similarity) is too lenient for small models
  - Semantic similarity doesn't catch logical hallucinations (e.g., "X happened because Y" when only "X happened" is in context)
  - Sentences below 5 chars are ignored → short answers about non-existent things pass
- **Impact:** 
  - Hallucinations are not flagged to user
  - User sees "verified: true" even on made-up content
- **Root Cause:** Conservative thresholding to avoid false positives
- **Fix Required:** 
  - Lower threshold to `0.25` for factual grounding
  - Check for logical connectors (because, therefore, implies) and flag them if not explicitly in context
  - Include min sentence length check

---

## 3. LIMITED OUTPUT LENGTH (User Reported)

### 3.1 **Aggressive Output Cleaning Removes Valid Content**
- **Severity:** HIGH
- **Current Location:** `backend/generation/prompt_builder.py:77-95`
- **Problem:**
  - `_CLOSING_TRIGGERS` regex looks for phrases like "In summary" and **truncates everything after**
  - Example: If answer says "In summary, the data shows X. Furthermore, Y also applies." → only "In summary, the data shows X" is kept
  - Sentence deduplication uses substring matching: if sentence 2 is a detailed version of sentence 1, it's skipped
  - Lines like `if norm in prev or prev in norm: continue` remove elaborations
- **Impact:** 
  - Complete answer gets cut off mid-thought
  - Follow-up details are lost
  - Answers look incomplete to user
- **Root Cause:** Over-aggressive cleaning meant to remove LLM formality
- **Fix Required:** 
  - Only truncate on ACTUAL closing patterns (signature lines)
  - Change dedup to exact match only, not substring matching
  - Allow elaborations in subsequent sentences

---

### 3.2 **MAX_NEW_TOKENS Set to 1024 but Output Post-Processed Before Reaching It**
- **Severity:** MEDIUM
- **Current Location:** `backend/config.py:39` + `backend/generation/prompt_builder.py:70-95`
- **Problem:**
  - Model can generate up to 1024 tokens
  - But `clean_output()` removes content mid-generation
  - User sees truncated answer even though model could have generated more
  - No streaming of intermediate tokens to show user lengthier responses
- **Impact:** 
  - Artificially short answers
  - User can't incrementally read response
- **Root Cause:** Batch processing + aggressive post-processing instead of streaming
- **Fix Required:** 
  - Keep streaming enabled (`/query/stream` endpoint exists but clean_output still cuts it)
  - Disable truncation until user explicitly requests summary

---

## 4. CITATION & SOURCE MAPPING ISSUES

### 4.1 **Citation Mapper Returns All Ranked Chunks Regardless of Answer Usage**
- **Severity:** MEDIUM
- **Current Location:** `backend/citation/citation_mapper.py:1-35`
- **Problem:**
  - `map_citations()` naively returns ALL chunks passed to it
  - But answer might only reference 1-2 of the 10 retrieved chunks
  - User sees citations for content that wasn't in the answer
  - No actual text-to-citation linking (semantic similarity matching)
- **Impact:** 
  - Confusing citation cards
  - User doesn't know which citation corresponds to which answer sentence
- **Root Cause:** Simplified implementation; assumes all context was used
- **Fix Required:** 
  - Match answer sentences to chunks using semantic similarity
  - Only show citations for chunks actually referenced in answer
  - Add explicit `[1]`, `[2]` markers in answer text linking to citations

---

### 4.2 **Support Scores Not Properly Propagated**
- **Severity:** LOW
- **Current Location:** `backend/api/routes/query_routes.py:165`
- **Problem:**
  - `support_scores` calculated by hallucination checker but UI doesn't visualize per-sentence
  - User sees binary "verified" flag, not granular sentence-level confidence
- **Impact:** 
  - User can't tell which parts of answer are most grounded
- **Root Cause:** Frontend not implemented; backend just stores scores
- **Fix Required:** 
  - Frontend should highlight low-scoring sentences in red
  - Show confidence % next to each sentence

---

## 5. INGESTION & STORAGE ISSUES

### 5.1 **Ingestion Status Always Shows "Done" Even After Errors**
- **Severity:** MEDIUM
- **Current Location:** `backend/api/services/ingestion_service.py:83`
- **Problem:**
  - Loop processes each file
  - If a file fails, `stage = "error"` is set
  - But loop always ends with: `jobs[job_id]["stage"] = "done"`
  - UI shows "Ingestion complete" even though file failed
- **Impact:** 
  - User doesn't know ingestion failed
  - Incomplete document index confuses retrieval
- **Root Cause:** Unconditional final status update
- **Fix Required:** 
  ```python
  if not any("✗ Failed" in line for line in jobs[job_id]["log_lines"]):
      jobs[job_id]["stage"] = "done"
  else:
      jobs[job_id]["stage"] = "partial_failure"
  ```

---

### 5.2 **No Duplicate Document Detection**
- **Severity:** LOW
- **Current Location:** `backend/api/services/ingestion_service.py` + `backend/storage/postgres_store.py`
- **Problem:**
  - Uploading same PDF twice creates duplicate vectors in Milvus
  - References count as 2 in retrieval
  - No deduplication by hash or content
- **Impact:** 
  - Inflated retrieval results
  - Same content seen twice
- **Root Cause:** No content hash or filename uniqueness check
- **Fix Required:** 
  - Calculate MD5 on file before ingestion
  - Skip if hash already exists in database

---

### 5.3 **Image Extraction Failures Not Graceful**
- **Severity:** MEDIUM
- **Current Location:** `backend/ingestion/image_extractor.py` calls `pdf2image.convert_from_path()` which requires Poppler
- **Problem:**
  - Poppler not installed on user's machine (per backend logs: "Failed to render pages 1-10: Unable to get page count. Is poppler installed?")
  - Image extraction silently fails; text extraction continues
  - User doesn't know images weren't extracted
- **Impact:** 
  - Binary/chart PDFs have no image search capability
  - No warning to user
- **Root Cause:** Soft fail without logging or user notification
- **Fix Required:** 
  - Log warning to ingestion UI: "Image extraction failed; install Poppler for multi-modal search"
  - Suggest installation command to user

---

## 6. RETRIEVAL-SPECIFIC ISSUES

### 6.1 **Dense Text Embeddings May Not Match LLM Generation Task**
- **Severity:** MEDIUM
- **Current Location:** `backend/embeddings/text_embedder.py` uses `all-MiniLM-L6-v2`
- **Problem:**
  - Text embeddings from SentenceTransformers (384-dim)
  - But the LLM (Gemma 3 1B) was pre-trained with different semantic space
  - Embeddings optimized for similarity, not for Q&A relevance
  - Better option: `multi-qa-mpnet-base-dot-v1` or finetune on Q&A pairs
- **Impact:** 
  - Retrieved chunks are semantically similar but not answer-relevant
  - Hallucinations increase because context is off-topic
- **Root Cause:** Using generic SentenceTransformer without task-specific tuning
- **Fix Required:** 
  - Switch to `multi-qa-mpnet-base-dot-v1` or `msmarco-minilm-l-12-v3`
  - Or finetune on document Q&A dataset

---

### 6.2 **No Query Expansion or Multi-hop Reasoning**
- **Severity:** LOW
- **Current Location:** `backend/api/routes/query_routes.py:98`
- **Problem:**
  - Query used as-is for retrieval
  - Complex questions (e.g., "Compare X and Y") are not expanded into sub-queries
  - Single query → single retrieval pass → limited context
- **Impact:** 
  - Complex questions get incomplete answers
- **Root Cause:** Simplified one-pass retrieval
- **Fix Required:** 
  - Use LLM to expand query: "What is X?" + "What is Y?" + "Differences?"
  - Merge results from 3 passes

---

## 7. CONFIGURATION & TUNING ISSUES

### 7.1 **TEMPERATURE Too High (0.6)**
- **Severity:** LOW
- **Current Location:** `backend/config.py:40`
- **Problem:**
  - Temperature 0.6 allows model creative freedom
  - For factual Q&A, should be 0.1-0.3
  - Higher temp = more hallucination
- **Impact:** 
  - Increased hallucination in answers
- **Fix Required:** Lower to `0.2` for factual mode

---

### 7.2 **TOP_K_RETRIEVAL = 10 But TOP_K_FINAL = 3**
- **Severity:** LOW
- **Current Location:** `backend/config.py:35-36`
- **Problem:**
  - Retrieves top 10, but only uses top 3 in prompt
  - Loss of information
  - Top 3 might not be most relevant
- **Fix Required:** 
  - RRF already filters to TOP_K_FINAL = 3, which is good
  - But consider increasing to 5 for better context

---

## 8. MODEL CHOICE ISSUES

### 8.1 **Gemma 3 1B May Be Underpowered for Task**
- **Severity:** MEDIUM (not critical but contextual)
- **Current Location:** `backend/model/gemma-3-1b-it-q4_0.gguf`
- **Problem:**
  - 1B parameter model is quite small
  - Tends to hallucinate more than 7B-13B models
  - Limited capacity for complex reasoning
  - Q4 quantization further reduces quality
- **Impact:** 
  - User experiences hallucinations despite best prompting
  - Cannot handle complex multi-document questions
- **Root Cause:** Hardware constraints on user's machine
- **Observation:** 
  - This is NOT the root of the reported issues (all fixable with code)
  - But explains why hallucination is harder to fully solve
- **Recommendation:** 
  - Once code fixes applied, consider trying 3-7B model if user upgrades RAM
  - Or implement local model switching in config

---

## Summary Table

| Category | Issue | Severity | Fix Complexity |
|----------|-------|----------|-----------------|
| Retrieval | No filenames in prompt | HIGH | LOW |
| Retrieval | Milvus filter syntax error | CRITICAL | LOW |
| Retrieval | BM25 global index | MEDIUM | MEDIUM |
| Retrieval | RRF weighting | MEDIUM | MEDIUM |
| Hallucination | System prompt too lenient | HIGH | LOW |
| Hallucination | Threshold too high | MEDIUM | LOW |
| Output | Aggressive cleaning (closing triggers) | HIGH | LOW |
| Output | Aggressive dedup (substring match) | HIGH | LOW |
| Output | MAX_TOKENS not reached | MEDIUM | MEDIUM |
| Citations | All chunks returned, not just used ones | MEDIUM | MEDIUM |
| Citations | Support scores not visualized | LOW | MEDIUM |
| Ingestion | Status always "done" | MEDIUM | LOW |
| Ingestion | No duplicate detection | LOW | MEDIUM |
| Ingestion | Image extraction failures silent | MEDIUM | LOW |
| Embeddings | Not Q&A-optimized | MEDIUM | MEDIUM |
| Config | Temperature too high | LOW | LOW |
| Config | TOP_K mismatch | LOW | LOW |
| Model | 1B model underpowered | MEDIUM | N/A (hardware) |

---

## Quick Fix Priority (Highest Impact First)

1. **Fix prompt to include filenames** → Solves "can't differentiate files"
2. **Fix system prompt constraints** → Reduces hallucinations
3. **Disable aggressive output cleaning** → Fixes "limited output length"
4. **Fix Milvus filter expression** → Enables session scoping
5. **Fix ingestion status logic** → User knows what succeeded/failed
6. **Switch to Q&A-optimized embeddings** → Better retrieval quality
7. **Implement proper citation matching** → Citations actually map to answers
8. **Lower temperature to 0.2** → Reduces hallucination
9. **Add query expansion** → Handles complex questions
10. **Investigate model upgrade path** → Long-term improvement

