# Codex Review - Gemini Notebook MCP Server & CLI

**Ngay:** 2026-10-02
**Thuc hien boi:** Codex (qua codex-rescue subagent), phan tich doc-hieu repo `E:\project\my-project\gemini-notebook-mcp-cli`

---

## 1. TINH NANG

- MCP server dang ky tool qua `register_all_tools(mcp)`, chay stdio/http/sse, co health endpoint, va chan bind HTTP/SSE ra non-loopback neu khong set `NOTEBOOKLM_ALLOW_EXTERNAL_BIND=1`: `src/notebooklm_tools/mcp/server.py:91`, `src/notebooklm_tools/mcp/server.py:120`, `src/notebooklm_tools/mcp/server.py:268`.
- Notebook CRUD + mo ta AI: list/get/describe/create/rename/delete trong service va MCP wrapper: `src/notebooklm_tools/services/notebooks.py:92`, `src/notebooklm_tools/services/notebooks.py:218`, `src/notebooklm_tools/mcp/tools/notebooks.py:9`.
- Source management: them URL/text/file/Drive, bulk add, list Drive freshness, sync Drive, rename/delete, describe/get raw content: `src/notebooklm_tools/services/sources.py:135`, `src/notebooklm_tools/services/sources.py:408`, `src/notebooklm_tools/services/sources.py:502`, `src/notebooklm_tools/mcp/tools/sources.py:16`.
- Chat/query: query notebook, configure chat, async query start/status, chat history list/get/export/save-to-note: `src/notebooklm_tools/services/chat.py:215`, `src/notebooklm_tools/services/chat.py:483`, `src/notebooklm_tools/services/chats.py:105`, `src/notebooklm_tools/mcp/tools/chat.py:21`.
- Studio/artifacts: tao audio/video/report/infographic/slides/quiz/flashcards/data table/mind map, status/rename/delete/revise, downloads/export: `src/notebooklm_tools/services/studio.py:302`, `src/notebooklm_tools/services/studio.py:681`, `src/notebooklm_tools/services/downloads.py:327`, `src/notebooklm_tools/mcp/tools/downloads.py:11`.
- Research, sharing, notes, labels, collections, aliases, profiles, batch/pipeline/cross-notebook query deu co service + CLI/MCP be mat rieng: `src/notebooklm_tools/services/research.py:197`, `src/notebooklm_tools/services/sharing.py:92`, `src/notebooklm_tools/services/notes.py:48`, `src/notebooklm_tools/services/batch.py:98`, `src/notebooklm_tools/services/pipeline.py:196`.

## 2. BAO MAT

- Base URL bi allowlist Google-only va bat buoc HTTPS khi override bang `NOTEBOOKLM_BASE_URL`: `src/notebooklm_tools/utils/config.py:68`, `:92`, `:96`.
- File mode luu plaintext cookies/token vao `auth.json` mirror va `cookies.json`; ghi atomic voi mode `0600`: `src/notebooklm_tools/core/auth.py:237`, `:253`, `:172`, `:180`.
- Protected mode dung `credentials.enc`, OS keyring/key store, va khong fallback lang sang plaintext khi protected load loi: `src/notebooklm_tools/core/auth.py:129`, `:131`, `:524`, `:502`.
- Storage mode marker ghi `storage-mode.json` voi `0600`; env override sai thi fail closed bang `ValueError`: `src/notebooklm_tools/utils/config.py:628`, `:630`, `:656`, `:685`.
- CSRF/session/build label duoc tu trich tu page HTML hoac request URL/body, roi dua vao batchexecute request qua `at`, `f.sid`, `bl`: `src/notebooklm_tools/core/auth.py:298`, `:320`, `src/notebooklm_tools/core/base.py:715`, `:727`.
- MCP HTTP/SSE khong co auth rieng, nhung mac dinh bind loopback va canh bao/chan external bind: `src/notebooklm_tools/mcp/server.py:269`, `:273`, `:282`.
- Khong thay `shell=True`, `os.system`, `eval(`, `exec(` trong grep repo; subprocess deu dang argv list o cac call site duoc grep: `src/notebooklm_tools/cli/commands/setup.py:794`, `src/notebooklm_tools/cli/commands/setup_wizard.py:101`, `desktop-extension/run_server.py:87`.
- Dependency co be mat rui ro hop ly can audit dinh ky: `httpx[socks]`, `websocket-client`, `fastmcp`, `pyyaml`, `keyring`, `cryptography`: `pyproject.toml:27`.

## 3. EXFILTRATION / NETWORK CALLS

Khong tim thay call network runtime nao gui cookies/credentials/notebook content toi domain non-Google trong code da grep. Co 2 domain non-Google hard-coded lien quan update/install metadata: `pypi.org` va `astral.sh`; khong thay cookies/notebook content duoc gui toi chung.

| Domain/host dich | Google? | Vi tri | Du lieu gui/nhan theo code |
|---|---:|---|---|
| `notebooklm.google.com` | Co | `core/base.py:233`, `utils/config.py:105` | RPC NotebookLM, upload, headers/cookies Google qua `httpx.Client(cookies=...)`: `core/base.py:644`, `:1089`. |
| `notebook.google.com` | Co | `utils/config.py:70`, `core/auth.py:906` | Host rebrand/login, cung loai auth/cookies Google. |
| `notebooklm.cloud.google.com`, `notebook.cloud.google.com`, `vertexaisearch.cloud.google.com` | Co | `utils/config.py:71,73`, `core/base.py:210` | Enterprise NotebookLM RPC/upload; can project/location: `core/base.py:216`. |
| `accounts.google.com` | Co | `core/cookie_rotation.py:27` | POST RotateCookies voi Google cookie jar cua client, body co dinh `ROTATE_COOKIES_BODY`: `core/cookie_rotation.py:120`. |
| `*.googleusercontent.com`, `lh3.google.com`, `drum.usercontent.google.com` | Co | `core/download.py:49`, `:1157` | Download artifact/media; gui Google cookies nhung drop OSID truoc request: `core/download.py:182,189`. |
| `127.0.0.1`, `localhost`, user-provided CDP URL | Local/dynamic | `utils/cdp.py:1119,1141,1275` | CDP control channel; co the chay in-page `fetch(... credentials:"include")` toi URL NotebookLM da build: `core/cdp_transport.py:204`. |
| `pypi.org` | Khong | `mcp/tools/server.py:19`, `cli/utils.py:186` | Version check GET JSON voi `User-Agent: notebooklm-mcp-cli`; khong thay cookies/credentials/notebook data duoc gui: `cli/utils.py:187`. |
| `astral.sh` | Khong | `desktop-extension/run_server.py:76` | Chi la text huong dan cai `uv`; code khong tu goi curl toi domain nay. |
| package index do `uvx --from notebooklm-mcp-cli` | Khong hard-coded | `desktop-extension/run_server.py:85,87` | Launcher chay `uvx`; domain phu thuoc cau hinh uv/PyPI, khong thay cookies/notebook content truyen qua argv. |

Cac pattern da grep de xac nhan: `httpx`, `requests`, `urllib.request`, `aiohttp`, `fetch`, `axios`, `websocket.create_connection`, `socket`, `subprocess`, `curl`, `wget`, `nc`, `telemetry`, `analytics`, `sentry`, `posthog`. Khong thay telemetry/analytics exfiltration rieng.

---

**Tom lai:** khong phat hien source code am tham gui du lieu nhay cam (cookies, credentials, noi dung notebook) ra ngoai he Google. Hai ngoai le non-Google (`pypi.org`, `astral.sh`) chi lien quan kiem tra phien ban/huong dan cai `uv`, khong mang theo du lieu nguoi dung.
