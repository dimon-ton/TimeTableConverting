# Codex and Claude Code instruction file discovery (AGENTS.md and CLAUDE.md)

## Findings

### Codex CLI (AGENTS.md)

- Codex builds an instruction chain by searching for `AGENTS.override.md` or `AGENTS.md` starting at the project root and walking down to the current working directory; it checks each directory along that path and includes at most one file per directory. This means files outside that path (for example, `docs/AGENTS.md` when you run Codex from the repo root) are not discovered. Source: OpenAI Codex docs, "Custom instructions with AGENTS.md". https://developers.openai.com/codex/guides/agents-md
- You can add alternate *filenames* via `project_doc_fallback_filenames` in `~/.codex/config.toml`, but this still relies on the same directory-walk discovery, not a custom path. Source: OpenAI Codex docs, "Custom instructions with AGENTS.md" ("Customize fallback filenames" and discovery rules). https://developers.openai.com/codex/guides/agents-md

### Claude Code (CLAUDE.md)

- Claude Code documents explicit locations for instruction files: user-level `~/.claude/CLAUDE.md`, project-level `CLAUDE.md` or `.claude/CLAUDE.md`, and local-only `CLAUDE.local.md`. There is no documented setting for arbitrary custom paths like `docs/CLAUDE.md`. Source: Claude Code settings documentation ("CLAUDE.md" in configuration scopes table). https://code.claude.com/docs/en/settings

## Practical implications

- Codex CLI: placing `AGENTS.md` in `docs/` will only be read if you run Codex from within `docs/` (or a descendant) because discovery follows the directory path. If you want it used from the repo root, keep a root `AGENTS.md` (or use a root stub that points to `docs/AGENTS.md`).
- Claude Code: keep `CLAUDE.md` in the repository root or `.claude/CLAUDE.md` to be picked up automatically. A `docs/CLAUDE.md` file is not listed as a supported location in the official settings documentation.

## Notes

- Web search results were not reliable for these specific configuration details; the authoritative guidance comes from the vendor documentation above.
