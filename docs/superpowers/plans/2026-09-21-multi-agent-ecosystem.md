# Multi-Agent Ecosystem Implementation Plan: Google Flow

Transformar o repositório `google-flow-api` em um ecossistema universal de automação de mídia (Nano Banana 2, Pro e Gemini Omni Flash 1.1) plugável nativamente em qualquer agente de IA do mercado (**Claude Code, OpenAI Codex, OpenClaw, Hermes Agent, OpenCode, Antigravity**), espelhando o padrão de excelência arquitetural do `notebooklm-py`.

## User Review Required
> [!NOTE]
> O usuário aprovou a execução direta de ponta a ponta sem interrupções intermediárias. Todas as etapas serão executadas, testadas e validadas em loop.

---

## Proposed Changes

### Configuration & Dev Dependencies

#### [MODIFY] [pyproject.toml](file:///C:/Users/FALA%20MUITO/Downloads/google-flow-api/pyproject.toml)
- Adicionar `pytest>=7.0.0` nas dependências opcionais de desenvolvimento (`[project.optional-dependencies] dev = ["pytest>=7.0.0"]`).
- Garantir que qualquer usuário ou agente consiga rodar `uv run pytest` imediatamente.

---

### Security & Compliance

#### [NEW] [SECURITY.md](file:///C:/Users/FALA%20MUITO/Downloads/google-flow-api/SECURITY.md)
- Threat Model de credenciais do Google Chrome local.
- Mapeamento de pastas de perfis (`~/.google-flow/profiles/<session>/`).
- Políticas de permissão (`0o600`), aviso sobre tokens de sessão bearer.
- Diretrizes de CI/CD (uso de env vars, nunca commitar pastas de perfil).
- Declaração "What This Library Does NOT Do" (sem telemetria, sem envio de credenciais a terceiros, sem armazenamento de senhas).

---

### Claude Code Integration

#### [NEW] [CLAUDE.md](file:///C:/Users/FALA%20MUITO/Downloads/google-flow-api/CLAUDE.md)
- Arquivo nativo consumido pelo Claude Code.
- Guia de setup do ambiente com `uv`.
- Comandos padrão para rodar testes, CLI e MCP.
- Regras de desenvolvimento: foco em headless, Playwright CDP sessions, dual-detection downloader, códigos de saída e convenções async.

---

### Universal Agent Guidelines

#### [NEW] [AGENTS.md](file:///C:/Users/FALA%20MUITO/Downloads/google-flow-api/AGENTS.md)
- Guia de desenvolvimento universal para OpenAI Codex, OpenClaw, Hermes Agent, OpenCode, Amp, Devin.
- Diagrama arquitetural dos motores (`FlowClient`, `AuthManager`, `ImageGenerator`, `Downloader`).
- Contrato da CLI (`--json` first, exit codes 0 e 1).
- Regras de isolamento concorrente via `--session`.

---

### Universal Skill Manifest

#### [NEW] [SKILL.md](file:///C:/Users/FALA%20MUITO/Downloads/google-flow-api/SKILL.md)
- Manifest compatível com `npx skills add`, OpenClaw, Antigravity e runners de skills.
- YAML frontmatter com nome, descrição agentic para trigger autônomo.
- Preflight obrigatório: `google-flow auth-check --test --json`.
- Receitas cópia-e-cola para geração de Imagens, Edição I2I, Vídeos Veo/Omni Flash e Lotes (Batch).
- Especificação exata dos envelopes JSON retornados.

---

### Public Repository Showcase & Marketing

#### [MODIFY] [README.md](file:///C:/Users/FALA%20MUITO/Downloads/google-flow-api/README.md)
- Reposicionamento de alto nível: *"Google Flow for AI Agents: The Unofficial CLI, Skill & Python SDK"*.
- Quickstart Recipes dedicados para cada IA:
  - Claude Code (`CLAUDE.md` + CLI)
  - OpenAI Codex & OpenClaw (`SKILL.md` + `--json`)
  - Cursor / Windsurf / Claude Desktop (Servidor MCP `flow_api.mcp_server`)
  - Antigravity (Skill nativa)
- Cheat sheet completo da CLI e exemplos de Python SDK.

---

## Verification Plan

### Automated Tests
- Executar `uv run pytest` para garantir 100% de aprovação nos testes existentes.
- Testar execução do comando `uv run google-flow auth-check --json` para verificar a integração com a CLI.

### Manual / Structural Verification
- Validar conformidade de sintaxe do `SKILL.md` (YAML frontmatter).
- Verificar que todos os arquivos estão criados na raiz do repositório `google-flow-api`.
- Verificar status do git para garantir commit limpo e pronto para publicação.
