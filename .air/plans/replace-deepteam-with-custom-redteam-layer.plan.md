## 1. Goal
Replace all runtime and test dependencies on DeepTeam with project-owned modules/classes while preserving full functional parity, continuing to use DeepEval wherever possible, and streamlining the current integration architecture.

## 2. Approach
Use a staged adapter migration: introduce internal red-team contracts first, route existing code through adapters, then progressively replace DeepTeam-backed implementations with custom DeepEval-backed generators/metrics and finally remove DeepTeam from dependencies. This avoids a risky “big bang” and keeps behavior testable after each major change. The streamlined target is a single internal red-team layer (typed test case model + metric protocol + attack/technique registry) so testcases no longer directly depend on third-party class hierarchies or protected methods.

## Implementation Progress

- [x] **Major Step 1 completed (2026-05-23): Introduce internal contracts and wire core runtime types**
  - Added:
    - `testframework/redteam/__init__.py`
    - `testframework/redteam/test_case.py`
    - `testframework/redteam/metric_protocol.py`
  - Updated core type wiring:
    - `testframework/models.py`
    - `testframework/testcases/base.py`
    - `testframework/guardrails/runner.py`
    - `testframework/guardrails/prompt_hardening/prompt_hardening.py`
    - `testframework/metrics/privacy_violations.py`
    - `testframework/metrics/tool_call_code_injection.py`
    - `testframework/custom_attack_techniques/attack_list_enhancer.py`
  - Verification:
    - `uv run pytest tests/core/test_models.py -v` ✅
    - `uv run pytest tests/core/test_base_test_case.py -v` ✅
    - `uv run pytest tests/chatbots/test_ollama_chatbot_lifecycle.py -v` ✅
  - Notes:
    - Initial command form with `-k "LifecycleTestCase or ExcessiveAgency"` selected no tests; reran full file.

- [x] **Major Step 2 completed (2026-05-23): Replace metric base dependency and migrate metric typing**
  - Added:
    - `testframework/redteam/metric_adapters.py`
  - Updated metric contracts:
    - `testframework/redteam/metric_protocol.py` (added `RedTeamingMetricBase`)
    - `testframework/redteam/__init__.py`
    - `testframework/metrics/base_metric.py` (removed DeepTeam base class dependency)
    - `testframework/metrics/privacy_violations.py` (explicit threshold assignment)
    - `testframework/metrics/tool_call_code_injection.py` (explicit threshold assignment)
  - Updated typing imports/signatures across testcase builders/wrappers to internal protocol:
    - `testframework/testcases/*/builder.py`
    - `testframework/testcases/*/test_case.py`
  - Verification:
    - `uv run pytest tests/core/test_tool_call_metric.py -v` ✅
    - `uv run pytest tests/core/test_models.py -v` ✅
    - `uv run pytest tests/chatbots/test_langchain_chatbot_timeout_retry.py -v` ✅
    - `uv run pytest tests/core/test_base_test_case.py -v` ✅ (additional regression)
  - Notes:
    - Initial `-k "AttackEnhancementResult or TestCaseResult"` filter selected no tests; reran full file.

- [x] **Major Step 3 completed (2026-05-23): Replace technique framework and streamline enhancer retry flow**
  - [x] **Step 3A completed (2026-05-23): Config-driven retry flow in enhancer**
    - Updated:
      - `testframework/custom_attack_techniques/attack_list_enhancer.py`
        - Removed interactive `input()` retry loop.
        - Added env-driven retry config via `ENHANCEMENT_RETRY_ATTEMPTS`.
        - Kept cooldown and threshold behavior.
    - Updated tests:
      - `tests/core/test_attack_list_enhancer.py`
        - Replaced prompt-based retry tests with config-driven retry tests.
        - Added coverage for retry env parsing and retry exhaustion/success.
    - Verification:
      - `uv run pytest tests/core/test_attack_list_enhancer.py -v` ✅
      - `uv run pytest tests/core/test_custom_attack_techniques.py -v` ✅
  - [x] **Step 3B completed (2026-05-23): Replace DeepTeam technique base/progress/generation dependencies with internal modules**
    - Added local technique/generation modules and migrated custom techniques:
      - `testframework/redteam/techniques/base.py`
      - `testframework/redteam/techniques/library.py`
      - `testframework/redteam/generation/model_generator.py`
      - `testframework/redteam/generation/progress.py`
      - `testframework/custom_attack_techniques/techniques.py`
      - `testframework/custom_attack_techniques/cipher_code_expert/cipher_code_expert.py`
      - `testframework/custom_attack_techniques/emotional_manipulation/emotional_manipulation.py`
      - `testframework/custom_attack_techniques/synthetic_context_injection/synthetic_context_injection.py`
    - Verification:
      - `uv run pytest tests/core/test_custom_attack_techniques.py -v` ✅
      - `uv run pytest tests/core/test_redteam_technique_library.py -v` ✅

- [x] **Major Step 4 completed (2026-05-23): Replace DeepTeam vulnerability builders with internal builders/registry**
  - Added:
    - `testframework/redteam/builders/base_builder.py`
    - `testframework/redteam/builders/deepeval_attack_builders.py`
    - `testframework/redteam/registry.py`
  - Updated category builders/testcases to internal builder + metric factories, including competition/robustness wrappers.
  - Verification:
    - `uv run pytest tests/core/test_testcase_categories.py -v` ✅

- [x] **Major Step 5 completed (2026-05-23): Final cleanup and post-review fixes**
  - Completed:
    - Removed `deepteam` dependency from `pyproject.toml`.
    - Removed runtime/test `deepteam` imports (`grep -RIn "from deepteam\\|import deepteam" testframework tests` returns no hits).
    - Updated docs for internal red-team ownership wording:
      - `README.md`
      - `_extras/doc/development.md`
    - Addressed review-session findings:
      - Kept explicit empty-subcategory behavior (`[]` => defaults) intentionally and locked it with tests.
      - Fixed illegal-activity crime subtype routing:
        - always includes `illegal-activity_crime` baseline attacks on every IllegalActivity execution
        - baseline `illegal-activity_crime` attacks are tagged as `IllegalActivitySubcategory.VIOLENT_CRIME`
        - additionally probes subtype-specific categories for future CSV expansion
      - Added focused regression tests:
        - `tests/core/test_redteam_builder_routing.py`
      - Verification:
        - `uv run pytest tests/core/test_redteam_builder_routing.py -v` ✅
        - `uv run pytest tests/core/test_testcase_categories.py -v` ✅
  - Verification:
    - `uv run pytest tests/ -v -p no:cacheprovider` ✅ (with `PYTHONDONTWRITEBYTECODE=1` in read-only environment)

### Current DeepTeam Usage Map (historical snapshot before migration)

This section is retained as migration context. It no longer reflects current code state.

Current audit status (2026-05-23):
- Runtime/test import audit: no `from deepteam` or `import deepteam` hits in `testframework/` and `tests/`.
- Dependency audit: `deepteam` removed from `pyproject.toml`.

**Dependency and docs references**
- `pyproject.toml:4,11` (description + dependency)
- `README.md:14-15,20,27,108`
- `_extras/doc/development.md:48,100,102`

**Core runtime contracts**
- `testframework/testcases/base.py:15-17,49,53,210,274,331,338,370`
- `testframework/guardrails/runner.py:9-10,37,39`
- `testframework/guardrails/prompt_hardening/prompt_hardening.py:8,51`
- `testframework/models.py:15,47,217`

**Custom metrics path**
- `testframework/metrics/base_metric.py:8,11`
- `testframework/metrics/privacy_violations.py:12,56`
- `testframework/metrics/tool_call_code_injection.py:11,61`

**Attack enhancement / technique path**
- `testframework/custom_attack_techniques/attack_list_enhancer.py:13,36,67,73,163-165`
- `testframework/custom_attack_techniques/techniques.py:11,25-56`
- `testframework/custom_attack_techniques/cipher_code_expert/cipher_code_expert.py:7-9,16`
- `testframework/custom_attack_techniques/emotional_manipulation/emotional_manipulation.py:12-18,28`
- `testframework/custom_attack_techniques/synthetic_context_injection/synthetic_context_injection.py:10-16,25`

**Category builders and testcase wrappers**
- Builders:
  - `testframework/testcases/benign/builder.py:8-12,18,37,45,70`
  - `testframework/testcases/bias/builder.py:9-13,17,46,63`
  - `testframework/testcases/ethics/builder.py:9-13,18,45,80`
  - `testframework/testcases/fairness/builder.py:7-10,15,39,59`
  - `testframework/testcases/illegal_activity/builder.py:9-13,18,50,116`
  - `testframework/testcases/indirect_instruction/builder.py:8-13,18,36,70`
  - `testframework/testcases/privacy_violations/builder.py:8-11,17,35,52`
  - `testframework/testcases/system_prompt_leakage/builder.py:10-14,20,50,85`
  - `testframework/testcases/toxicity/builder.py:9-14,19,49,81`
  - `testframework/testcases/excessive_agency/builder.py:8-12,18,36,53`
- Direct DeepTeam vulnerability usage in testcase wrappers:
  - `testframework/testcases/competition/test_case.py:10-11,31,33,38`
  - `testframework/testcases/robustness/test_case.py:10-11,30,36,41`
- Base metric types in wrappers:
  - `testframework/testcases/*/test_case.py` imports at lines listed in `tests/core/test_testcase_categories.py` monkeypatch targets (`:62,87,111,136,161,186,212,239,265,290,315,341`)

**Tests coupled to current DeepTeam integration shape**
- `tests/core/test_attack_list_enhancer.py:8,39-176`
- `tests/core/test_custom_attack_techniques.py:12-25,88-173`
- `tests/core/test_base_test_case.py:15-17,160-176`
- `tests/core/test_tool_call_metric.py:8,31-76`
- `tests/core/test_testcase_categories.py:9-25,60-344`
- `tests/chatbots/test_langchain_chatbot_timeout_retry.py:152-157`

## 3. File Changes

### Create
- `testframework/redteam/__init__.py`  
  Internal package entrypoint for custom red-team layer.
- `testframework/redteam/test_case.py`  
  Project-owned replacement for DeepTeam `RTTestCase` (fields used today: `vulnerability`, `vulnerability_type`, `input`, `actual_output`, `metadata`, `retrieval_context`).
- `testframework/redteam/metric_protocol.py`  
  Local metric contract replacing `BaseRedTeamingMetric` type dependency.
- `testframework/redteam/metric_adapters.py`  
  DeepEval-backed metric implementations (Harm/Fairness/IndirectInstruction/PromptExtraction equivalents + existing custom metrics adapter bridge).
- `testframework/redteam/generation/__init__.py`  
  Generation package.
- `testframework/redteam/generation/model_generator.py`  
  Shared structured generation helper using DeepEval model APIs (replacing `deepteam.attacks.attack_simulator.utils.generate/a_generate`).
- `testframework/redteam/generation/progress.py`  
  Local no-deepteam progress helpers replacing `deepteam.utils` calls.
- `testframework/redteam/techniques/base.py`  
  Local technique base class and metadata (replacing `BaseSingleTurnAttack`/`Exploitability` dependency).
- `testframework/redteam/techniques/library.py`  
  Local implementations for currently used DeepTeam techniques: `AdversarialPoetry`, `Roleplay`, `MathProblem`, `Base64`, `PromptInjection` chain semantics.
- `testframework/redteam/builders/base_builder.py`  
  Common builder abstraction to remove duplication across category builders.
- `testframework/redteam/builders/deepeval_attack_builders.py`  
  Category generation implementations using DeepEval + local prompt templates.
- `testframework/redteam/registry.py`  
  Streamlined central registry mapping category/subcategory to generator + metric strategy.
- `tests/core/test_redteam_test_case_contract.py`  
  Contract tests for replacement test-case model.
- `tests/core/test_redteam_metric_protocol.py`  
  Metric protocol behavior tests.
- `tests/core/test_redteam_technique_library.py`  
  Parity tests for recreated technique outputs and chaining behavior.

### Modify
- `testframework/testcases/base.py:14-17,49,53,210,274,331,338,370`  
  Replace DeepTeam type imports/usages with internal red-team contracts.
- `testframework/models.py:15,47,217`  
  Replace `RTTestCase` type; remove `deepteam` module-based error classification.
- `testframework/guardrails/runner.py:9-10,37,39`  
  Type contract switch to internal test-case/metric protocol.
- `testframework/guardrails/prompt_hardening/prompt_hardening.py:8,51`  
  Construct internal test-case object instead of DeepTeam `RTTestCase`.
- `testframework/metrics/base_metric.py:8,11`  
  Inherit from local metric protocol base.
- `testframework/metrics/privacy_violations.py:12,56` and `testframework/metrics/tool_call_code_injection.py:11,61`  
  Accept internal test-case contract.
- `testframework/custom_attack_techniques/attack_list_enhancer.py:13,36,67,73,152-208`  
  Use internal test-case type; replace interactive retry prompt with config-driven retry policy.
- `testframework/custom_attack_techniques/techniques.py:11,25-56`  
  Swap DeepTeam-provided techniques for local equivalents in new library.
- `testframework/custom_attack_techniques/cipher_code_expert/cipher_code_expert.py:7-9,16`  
  Move to internal technique base/progress helper.
- `testframework/custom_attack_techniques/emotional_manipulation/emotional_manipulation.py:12-18,28`  
  Replace DeepTeam base/progress/generate dependencies with local red-team modules (still DeepEval-backed).
- `testframework/custom_attack_techniques/synthetic_context_injection/synthetic_context_injection.py:10-16,25`  
  Same as emotional manipulation.
- All category builders and wrappers currently importing DeepTeam:
  - `testframework/testcases/benign/builder.py`
  - `testframework/testcases/bias/builder.py`
  - `testframework/testcases/competition/test_case.py`
  - `testframework/testcases/ethics/builder.py`
  - `testframework/testcases/excessive_agency/builder.py`
  - `testframework/testcases/fairness/builder.py`
  - `testframework/testcases/illegal_activity/builder.py`
  - `testframework/testcases/indirect_instruction/builder.py`
  - `testframework/testcases/privacy_violations/builder.py`
  - `testframework/testcases/robustness/test_case.py`
  - `testframework/testcases/system_prompt_leakage/builder.py`
  - `testframework/testcases/toxicity/builder.py`
  - `testframework/testcases/*/test_case.py` wrappers that currently type against `RTTestCase`/`BaseRedTeamingMetric`.
- `tests/core/test_attack_list_enhancer.py`  
  Update for config-driven retry behavior (no `input()` prompt assertions).
- `tests/core/test_custom_attack_techniques.py`  
  Patch new local generator/progress modules instead of DeepTeam utility symbols.
- `tests/core/test_testcase_categories.py`  
  Monkeypatch targets updated to custom builder/registry classes.
- `tests/chatbots/test_langchain_chatbot_timeout_retry.py:152-157`  
  Update generation-error classifier test to new module namespace rules.
- `pyproject.toml:4,11`  
  Remove DeepTeam dependency and description mention.
- `README.md:14-15,20,27,108` and `_extras/doc/development.md:48,100,102`  
  Update architecture/development docs to custom red-team layer + DeepEval usage.

### Delete
- No immediate deletions in early stages; perform final cleanup deletion only after all imports removed and tests pass:
  - Remove any now-obsolete compatibility shim modules introduced during migration (to be identified during implementation).

## 4. Implementation Steps

### Task 1: Introduce Internal Contracts and Adapters (no behavior change)
1. Add `testframework/redteam/test_case.py` with a dataclass matching the runtime fields currently accessed in `testframework/testcases/base.py:235-238,296,306,374-378` and `testframework/guardrails/prompt_hardening/prompt_hardening.py:51`.
2. Add `testframework/redteam/metric_protocol.py` capturing current metric surface used in `testframework/testcases/base.py:307-321` and `testframework/guardrails/prompt_hardening/prompt_hardening.py:53-63`.
3. Switch type imports in `testframework/models.py:15,217`, `testframework/testcases/base.py:15-17,53,331,338,370`, `testframework/guardrails/runner.py:9-10,37,39`, and `testframework/guardrails/prompt_hardening/prompt_hardening.py:8,51`.
4. Add compatibility adapters so old builders/metrics still run while callers no longer import DeepTeam types directly.

**Major-change test gate A**
- `uv run pytest tests/core/test_models.py -v`
- `uv run pytest tests/core/test_base_test_case.py -v`
- `uv run pytest tests/chatbots/test_ollama_chatbot_lifecycle.py -v -k "LifecycleTestCase or ExcessiveAgency"`

### Task 2: Replace Metric Base and DeepTeam Metric Type Dependency
1. Refactor `testframework/metrics/base_metric.py:8-26` to inherit from local metric base/protocol instead of `deepteam.metrics.BaseRedTeamingMetric`.
2. Update `testframework/metrics/privacy_violations.py:53-73` and `testframework/metrics/tool_call_code_injection.py:58-108` to consume internal test-case type.
3. Implement `testframework/redteam/metric_adapters.py` for Harm/Fairness/IndirectInstruction/PromptExtraction equivalents using DeepEval (GEval + explicit criteria templates), replacing direct DeepTeam metric class construction in builders.

**Major-change test gate B**
- `uv run pytest tests/core/test_tool_call_metric.py -v`
- `uv run pytest tests/core/test_models.py -v -k "AttackEnhancementResult or TestCaseResult"`
- `uv run pytest tests/chatbots/test_langchain_chatbot_timeout_retry.py -v`

### Task 3: Replace Technique Framework and Streamline Enhancer
1. Create local technique base + exploitability enum + progress helper (`testframework/redteam/techniques/base.py`, `testframework/redteam/generation/progress.py`) to replace DeepTeam utility imports in:
   - `testframework/custom_attack_techniques/cipher_code_expert/cipher_code_expert.py:7-9`
   - `testframework/custom_attack_techniques/emotional_manipulation/emotional_manipulation.py:12-18`
   - `testframework/custom_attack_techniques/synthetic_context_injection/synthetic_context_injection.py:10-16`
2. Implement local structured generation helper (`testframework/redteam/generation/model_generator.py`) and migrate emotional/synthetic techniques to it.
3. Recreate DeepTeam techniques currently configured in `testframework/custom_attack_techniques/techniques.py:31-55` as local classes in `testframework/redteam/techniques/library.py`.
4. Refactor `testframework/custom_attack_techniques/attack_list_enhancer.py:152-208` to config-driven retries (remove interactive `input()` decisions), and keep threshold/cooldown behavior.
5. Update ENHANCEMENTS registry to use only local techniques while preserving names and chaining semantics.

**Major-change test gate C**
- `uv run pytest tests/core/test_attack_list_enhancer.py -v`
- `uv run pytest tests/core/test_custom_attack_techniques.py -v`
- `uv run pytest tests/core/test_models.py -v -k "EnhancedAttack or AttackEnhancementResult"`

### Task 4: Replace DeepTeam Vulnerability Builders with Custom DeepEval-backed Builders
1. Implement shared builder abstractions (`testframework/redteam/builders/base_builder.py`) and registry (`testframework/redteam/registry.py`) to streamline category mapping and reduce duplicated logic now spread across builders.
2. Replace DeepTeam class instantiations and protected `_get_metric` usage in:
   - `testframework/testcases/bias/builder.py:52-66`
   - `testframework/testcases/ethics/builder.py:69-85`
   - `testframework/testcases/illegal_activity/builder.py:105-119`
   - `testframework/testcases/system_prompt_leakage/builder.py:72-90`
   - `testframework/testcases/toxicity/builder.py:56-84`
   - `testframework/testcases/competition/test_case.py:31-40`
   - `testframework/testcases/robustness/test_case.py:30-44`
3. Keep CSV-derived flows intact in existing builders while swapping types/metric factories to internal contracts.
4. Update testcase wrappers in `testframework/testcases/*/test_case.py` to reference custom builders/registry and internal metric type.

**Major-change test gate D**
- `uv run pytest tests/core/test_testcase_categories.py -v`
- `uv run pytest tests/chatbots/test_ollama_chatbot_lifecycle.py -v`
- `uv run pytest tests/core/test_base_test_case.py -v -k "find_metric or select_chatbots"`

### Task 5: Remove DeepTeam from Dependency Surface and Final Cleanup
1. Remove remaining DeepTeam imports from runtime via `grep` validation over `testframework/` and `tests/`.
2. Update docs and package metadata:
   - `pyproject.toml:4,11`
   - `README.md:14-15,20,27,108`
   - `_extras/doc/development.md:48,100,102`
3. Update tests tied to old import paths:
   - `tests/core/test_testcase_categories.py`
   - `tests/core/test_custom_attack_techniques.py`
   - `tests/chatbots/test_langchain_chatbot_timeout_retry.py:152-157`
4. Remove temporary compatibility shims introduced in Task 1.

**Major-change test gate E (full regression)**
- `uv run pytest tests/ -v`

## 5. Acceptance Criteria
1. `deepteam` is no longer present in runtime/test imports under `testframework/` and `tests/` (verifiable by `grep -RIn "deepteam" testframework tests` returning no code import hits).
2. `pyproject.toml` no longer declares `deepteam` in dependencies.
3. Baseline test case execution path still constructs, enhances, evaluates, and stores attacks without DeepTeam types (validated by passing unit tests in gates A–E).
4. ENHANCEMENTS still includes baseline + all previously active technique names (`Baseline Prompt (no Technique)`, `AdversarialPoetry`, `Roleplay`, `MathProblem`, `Cipher Code Expert`, `Base64/PromptInjection` semantics), now from internal modules.
5. Attack enhancement retry behavior is non-interactive/config-driven; no runtime `input()` calls remain in enhancer flow.
6. Category testcases covered by `tests/core/test_testcase_categories.py` still initialize builders and preserve category/subcategory behavior.
7. Full test suite passes: `uv run pytest tests/ -v`.

## 6. Verification Steps
1. Contract and unit gates after each major task (A–E commands above).
2. DeepTeam removal audit:
   - `grep -RIn --exclude-dir=__pycache__ "from deepteam\|import deepteam" testframework tests`
3. Dependency audit:
   - verify `pyproject.toml` dependency list excludes DeepTeam.
4. Optional CLI smoke (after code implementation, if environment configured):
   - `uv run llm-test-baseline run-baseline`
   - validate run artifact schema unchanged for required fields.
5. Edge-case checks:
   - document-embedded instruction handling remains non-re-enhanced behavior (`attack_list_enhancer` tests).
   - tool-call metric path remains intact for tool invocation/no-tool invocation cases.
   - error classification still maps DeepEval/OpenAI failures to `GENERATION_ERROR`/`TIMEOUT` correctly.

## 7. Risks & Mitigations
1. **Risk: Full parity drift for DeepTeam-generated vulnerabilities** (DeepTeam prompt-generation internals are not fully visible).  
   **Mitigation:** add golden fixtures from current behavior for representative categories and enforce parity in new tests before removing adapters.
2. **Risk: Recreated technique behavior diverges from existing bypass style**.  
   **Mitigation:** snapshot current outputs for deterministic seeds/prompts and assert structural equivalence (prefix/suffix/chaining invariants) rather than brittle exact text.
3. **Risk: Replacing DeepTeam metric classes may alter scoring thresholds**.  
   **Mitigation:** centralize thresholds/criteria in `metric_adapters.py`, add explicit threshold tests per metric path, and keep default thresholds equal to current values where known.
4. **Risk: Large cross-cutting refactor can break many monkeypatch-based tests**.  
   **Mitigation:** keep adapter phase (Task 1) and update tests incrementally per gate; avoid simultaneously changing all import paths without passing intermediate gates.
5. **Risk: CLI/runtime lockups from interactive retry prompts** (current behavior in `attack_list_enhancer.py:183-208`).  
   **Mitigation:** move to config-driven retries with bounded attempts and cooldown policy, plus explicit tests for retry stop conditions.
