# AGENTS.md — AI Behavioral Rules & Writing Protocol

> This file guides the behavior of AI assistants and co-authors working on this paper.
> It ensures academic rigor, alignment with specifications, and clean LaTeX structure.

---

## RULE 0 — MANDATORY SPEC READING

Before modifying any `.tex` files, the assistant MUST:
1. Read `doc-spec.md` in the project root.
2. Read the relevant module in `specs/` (`secoes.md`, `referencias.md`, or `arquitetura.md`).
3. Consult the human author if a task is not covered by the specification.

---

## RULE 1 — NO DATA HALLUCINATION

The AI assistant MUST NEVER:
- Invent or estimate numerical metrics (latency, CPU usage, mathematical parameters, etc.).
- Fabricate bibliographic references.
- Add unapproved sections or deviate from IEEE formatting standards.

---

## RULE 2 — LANGUAGE & STYLE

- All paper text inside `secoes/*.tex` and `config/dados.tex` MUST be written in formal **Academic English**.
- Use impersonal passive/third-person voice consistent with IEEE publication guidelines.

---

## RULE 3 — HIERARCHY OF TRUTH

1. `doc-spec.md` and files inside `specs/` (primary source of truth)
2. Direct explicit instructions from the human author in the current chat session
3. Pre-existing AI knowledge base

---

## RULE 4 — FILE EDIT PERMISSIONS

- **Allowed to edit (upon request):** `secoes/*.tex`, `referencias/referencias.bib`, `config/dados.tex`.
- **Do not modify without explicit authorization:** `main.tex`, `IEEEtran.cls`, `doc-spec.md`, `AGENTS.md`.
