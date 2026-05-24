## 1. Goal
Convert project logging in `testframework/` to lazy loguru style by replacing eager interpolation in logger calls, while preserving behavior and message text.

## 2. Approach
The codebase uses `loguru` exclusively, so the refactor will follow loguru-native lazy formatting (`"... {} ...", value` / named fields where appropriate) instead of stdlib `%s` style. Static log messages will remain unchanged because they are already effectively lazy and do not incur interpolation work. `logger.opt(lazy=True)` will be added only where message values rely on clearly non-trivial computations, not for lightweight values like simple attributes or basic constants.

## 3. File Changes
- **Modify** `testframework/guardrails/runner.py` (logging call sites around lines 43-98, 128-143)
  - Replace eager f-string logger messages with lazy placeholders and arguments.
- **Modify** `testframework/guardrails/gcp_model_armor/gcp_model_armor.py` (logging call sites around lines 58-60, 100-102)
  - Convert timeout retry warning messages to lazy placeholders.
- **Modify** `testframework/util/ollama_handler.py` (lines 56-57, 71, 100-111, 126)
  - Convert interpolated messages to lazy placeholders.
- **Modify** `testframework/tests/base_test.py` (lines 41-44, 48, 51, 60, 67, 70, 75-78, 83)
  - Convert test-run orchestration logs to lazy style.
- **Audit (no expected code change)** `testframework/tests/default_test.py` (lines 32, 53)
  - Static messages only; keep unchanged.
- **Modify** `testframework/cli.py` (lines 42, 57, 61, 69-73, 86, 88, 91, 94-96, 106)
  - Convert eager interpolation to lazy placeholders; preserve CLI message content.
- **Modify** `testframework/storage.py` (lines 27, 30, 42, 45)
  - Convert path interpolation logs to lazy placeholders.
- **Modify** `testframework/chatbots/store.py` (lines 22, 28)
  - Convert chatbot name interpolation to lazy placeholders.
- **Modify** `testframework/chatbots/dummy_chatbot.py` (line 18)
  - Normalize unnecessary f-string logger call.
- **Modify** `testframework/chatbots/rag/vector_store.py` (lines 45-52, 66-72, 78)
  - Convert interpolated log messages; apply `opt(lazy=True)` only where non-trivial computed values are deferred.
- **Modify** `testframework/chatbots/rag/document_loader.py` (lines 44-47, 57-59, 66, 68, 80-82, 85, 96, 98-100)
  - Convert eager interpolation in loader/splitter logs.
- **Modify** `testframework/chatbots/langchain_base_chatbot.py` (lines 64-68, 142, 195-198, 207-212, 216-220, 224-228, 251-266, 274-282)
  - Convert high-frequency chatbot lifecycle logs to lazy placeholders.
- **Modify** `testframework/custom_attack_techniques/emotional_manipulation/emotional_manipulation.py` (line 49)
  - Convert enhancement log message.
- **Modify** `testframework/custom_attack_techniques/cipher_code_expert/cipher_code_expert.py` (line 23)
  - Convert enhancement log message.
- **Modify** `testframework/custom_attack_techniques/attack_list_enhancer.py` (lines 42-46, 74, 103, 118-121, 129-133, 141, 150, 169-170, 177-180, 195-198, 202-204, 207-209, 224-227, 231-233)
  - Convert attack enhancement lifecycle and retry logs to lazy style.
- **Modify** `testframework/custom_attack_techniques/synthetic_context_injection/synthetic_context_injection.py` (line 44)
  - Convert enhancement log message.
- **Modify** `testframework/testcases/base.py` (lines 92-95, 100-105, 113-115, 118-121, 141-144, 158-161, 174-177, 191-200, 207, 210-222, 244-247, 254-257, 278, 284-287, 290-293, 297-299, 311-314, 324-327, 357-359)
  - Convert the core test-case execution logs, including retries and durations.

## 4. Implementation Steps
### Task 1: Define and apply conversion rules
1. In all listed files, replace `logger.<level>(f"...")` and multi-line f-string message construction with loguru lazy templates and arguments.
2. Keep surrounding logger level (`info`, `warning`, `error`, `exception`, `debug`) unchanged.
3. Preserve message text semantics and punctuation to avoid breaking downstream log parsing assumptions.

### Task 2: Apply `opt(lazy=True)` only where justified
1. Identify logger call sites where message arguments involve non-trivial computed expressions (method calls or heavier composition beyond lightweight attribute reads).
2. Convert those call sites to `logger.opt(lazy=True).<level>("...", arg=lambda: ...)` with explicit lambda capture where needed.
3. Do not apply `lazy=True` for trivial values (simple variables, constants, direct attributes, lightweight counters).

### Task 3: Repository-wide consistency pass
1. Re-scan `testframework/` for logger calls to ensure no eager interpolated logger messages remain.
2. Confirm static logger strings are untouched unless needed for placeholder conversion consistency near edited call blocks.
3. Ensure no accidental behavior changes in control flow, exception handling, or return values.

### Task 4: Verification and regression checks
1. Run grep checks for eager logger interpolation patterns.
2. Execute focused and full tests according to repo guidance (`uv` + pytest).
3. If failures occur, adjust only logging syntax issues, not functional logic.

## 5. Acceptance Criteria
1. No logger call in `testframework/` uses eager interpolation forms in the logger argument (`f"..."`, `f'...'`, or `.format(...)` directly in logger message argument).
2. All previously interpolated logger messages in the listed files use loguru lazy template arguments.
3. Static logger messages remain unchanged unless needed for local consistency, and no log level is changed.
4. `logger.opt(lazy=True)` appears only at call sites with clearly non-trivial computed values.
5. `uv run pytest tests/ -v` passes after refactor.
6. `uv run llm-test-baseline --help` runs without logging-related runtime errors.

## 6. Verification Steps
1. Search checks:
   - `grep -RInE "logger\.(debug|info|warning|error|exception|critical)\(f\"|logger\.(debug|info|warning|error|exception|critical)\(f'" testframework`
   - `grep -RInE "logger\.(debug|info|warning|error|exception|critical)\(.*\.format\(" testframework`
2. Run project tests:
   - `uv run pytest tests/ -v`
3. CLI sanity check:
   - `uv run llm-test-baseline --help`
4. Optional targeted smoke check for ingestion path logs:
   - `uv run llm-test-baseline populate-db --help`

## 7. Risks & Mitigations
- **Risk:** Placeholder/argument mismatch in converted log templates causing malformed logs.
  - **Mitigation:** Keep one-to-one mapping between template placeholders and arguments; run grep and pytest verification.
- **Risk:** Incorrect lambda capture with `opt(lazy=True)` in loops or mutable values.
  - **Mitigation:** Use explicit lambda default capture for loop variables where applicable.
- **Risk:** Subtle message drift affecting any ad-hoc log consumers.
  - **Mitigation:** Preserve original message wording and key fields; change only interpolation mechanics.
- **Risk:** Over-application of `lazy=True` reducing readability without performance gain.
  - **Mitigation:** Restrict `lazy=True` to clearly non-trivial computed values per agreed scope.