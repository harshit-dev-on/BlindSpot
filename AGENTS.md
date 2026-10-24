# BlindSpot Development Directives & Rules

## 1. Primary Rule: Strix Codebase Parity (`d:\Projects\BlindSpot\strix`)
- **Never hallucinate or invent patterns from scratch**: When designing, coding, configuring, or refactoring anything in BlindSpot, **ALWAYS refer directly to the Strix codebase** at [`d:/Projects/BlindSpot/strix`](file:///d:/Projects/BlindSpot/strix) as the gold standard.
- **Port and adapt directly from Strix**:
  - `strix/strix/config/` -> Configuration loading, universal env variables (`STRIX_LLM`, `BLINDSPOT_LLM`, `LLM_API_KEY`, `LLM_API_BASE`), JSON config parsing, and `persist_current()`.
  - `strix/strix/interface/` -> CLI arguments (`-t`, `-u`, `-i`, `-c`, `-m`, `-n`, `--config`), start screens, environment validation panels (`validate_environment()`).
  - `strix/strix/agents/` -> Agent design, worker loops, tool calling, execution prompts.
  - `strix/strix/runtime/` -> Safe session management, context isolation, navigation safety.
  - `strix/strix/report/` -> Report state, models, SARIF generation, structured findings.
- **Zero Docker Requirement**: Maintain native host Playwright browser execution for BlindSpot while preserving 100% of Strix's CLI and configuration ergonomics.
- **Always verify against Strix source**: Before writing new code, search and view the relevant Strix implementation in [`strix/`](file:///d:/Projects/BlindSpot/strix) to mirror function signatures, argument conventions, and design patterns.
