# Huong Dan Su Dung (Tieng Viet)

Tai lieu nay danh cho nguoi dung moi: cach **cai dat**, **dang nhap/cau hinh**,
**chay MCP server**, va **ket noi cac AI assistant** (Claude Code, Claude
Desktop, Gemini CLI, Cursor...) voi Gemini Notebook (ten cu: Google
NotebookLM) thong qua du an nay.

Day la ban dich/tom tat thuc hanh tu cac tai lieu tieng Anh chi tiet hon:
[README](../README.md), [Getting Started](GETTING_STARTED.md),
[CLI Guide](CLI_GUIDE.md), [MCP Guide](MCP_GUIDE.md),
[Authentication Guide](AUTHENTICATION.md). Khi can tra cuu sau (tat ca flag,
tat ca tool), xem cac file do — tai lieu nay chi di qua luong su dung chinh.

## Muc luc

- [1. Du an nay la gi](#1-du-an-nay-la-gi)
- [2. Cai dat](#2-cai-dat)
- [3. Dang nhap va cau hinh luu tru](#3-dang-nhap-va-cau-hinh-luu-tru)
- [4. Ket noi voi mot AI assistant](#4-ket-noi-voi-mot-ai-assistant)
- [5. Tu chay MCP server thu cong](#5-tu-chay-mcp-server-thu-cong)
- [6. Xac minh moi thu hoat dong](#6-xac-minh-moi-thu-hoat-dong)
- [7. Cac lenh kiem tra/chan doan huu ich](#7-cac-lenh-kiem-trachan-doan-huu-ich)
- [8. Xu ly su co thuong gap](#8-xu-ly-su-co-thuong-gap)

---

## 1. Du an nay la gi

Du an gom 2 thu dung chung 1 package:

- `nlm` — cong cu dong lenh (CLI) de ban tu tay goi Gemini Notebook tu
  terminal (vi du `nlm notebook list`).
- `notebooklm-mcp` — MCP server, de cac AI assistant (Claude Code, Claude
  Desktop, Gemini CLI, Cursor, v.v.) tu goi Gemini Notebook thay ban qua giao
  thuc MCP (Model Context Protocol).

Ca 2 deu dung chung 1 tai khoan Google da dang nhap qua `nlm login` — khong
can API key rieng, vi Google khong co public API cho NotebookLM.

## 2. Cai dat

Cach khuyen nghi (dung [uv](https://docs.astral.sh/uv/)):

```bash
uv tool install notebooklm-mcp-cli
```

Lenh nay cai ca 2 executable `nlm` va `notebooklm-mcp` vao PATH.

Cac cach khac (xem [README → Installation](../README.md#installation) de
biet day du):

```bash
pip install notebooklm-mcp-cli      # dung pip
pipx install notebooklm-mcp-cli     # dung pipx
uvx --from notebooklm-mcp-cli nlm --help   # chay thu khong can cai, uvx tu tai ban moi nhat moi lan
```

> Yeu cau Python >= 3.11.

## 3. Dang nhap va cau hinh luu tru

```bash
nlm login
```

Lenh nay mo mot trinh duyet Chrome/Edge rieng (quan ly boi `nlm`, khong phai
trinh duyet hang ngay cua ban), dieu huong toi `notebook.google.com`, va cho
ban dang nhap Google. Sau khi dang nhap xong, cookie dang nhap duoc trich
xuat va luu lai tu dong — ban khong can lam lai buoc nay moi lan dung.

**Luc dang nhap profile MOI lan dau**, CLI se hoi ban muon luu login kieu
nao (chi hoi tren may ban, khong hoi khi chay tren server/cron):

- **Protected (khuyen nghi cho may ca nhan)** — ma hoa, khoa luu trong OS
  keystore (Keychain tren macOS, Credential Manager tren Windows,
  SecretService/KWallet tren Linux).
- **File (mac dinh, hop ly cho server/cron/Docker)** — luu file plaintext,
  quyen file `0600` (chi chu tien trinh doc duoc).

Chon truoc bang flag neu khong muon bi hoi:

```bash
nlm login --storage protected
nlm login --storage file
```

Doi sau nay:

```bash
nlm auth storage set protected
nlm auth storage set file
nlm auth storage status          # xem dang o che do nao
```

**Nhieu tai khoan Google (profile):**

```bash
nlm login --profile work         # tao/dang nhap profile ten "work"
nlm login switch work            # doi profile mac dinh sang "work"
nlm login profile list           # liet ke tat ca profile + email
nlm login profile rename work main
nlm login profile delete work
```

**Kiem tra da dang nhap dung chua:**

```bash
nlm login --check
```

Chi tiet day du (ca che do Protected/File, cach hoat dong, troubleshooting)
xem [Authentication Guide](AUTHENTICATION.md).

## 4. Ket noi voi mot AI assistant

### Cach de nhat: wizard tu dong

```bash
nlm setup
```

Chon **"Add the MCP to my tools/agents"**, tick (phim Space) cac app ban
muon ket noi, roi Enter. Wizard tu dong:

- Phat hien app nao da cai tren may (khong tu tao app chua co).
- Ghi config MCP vao dung file/scope cua app do.
- Hoi co muon cai them "skill" (huong dan dung cho AI) khong — chon pham
  vi "tat ca project" hoac "chi thu muc hien tai".

Dung **"Show my tools' status"** trong wizard de xem app nao da duoc ket
noi. Dung **"Copy MCP setup for a tool not listed"** neu app cua ban chua
co trong danh sach ho tro san — wizard se in ra doan JSON de ban tu dan
vao config cua app do (tuong duong `nlm setup add json`, xem ben duoi).

### Cach nhanh: lenh truc tiep cho tung app

Neu ban biet ro muon ket noi app nao, co the goi thang (khong can qua
wizard):

```bash
nlm setup add claude-code       # Claude Code
nlm setup add claude-desktop    # Claude Desktop (tu phat hien profile regular/3p)
nlm setup add claude-desktop --profile 3p   # chi định ro profile Relay AI/3p
nlm setup add gemini            # Gemini CLI
nlm setup add cursor            # Cursor
nlm setup add windsurf          # Windsurf
nlm setup add cline             # Cline
nlm setup add github-copilot    # GitHub Copilot (--scope user|project)
nlm setup add antigravity       # Antigravity
nlm setup add codex             # Codex CLI
nlm setup add opencode          # OpenCode
nlm setup add all               # Quet va cau hinh tat ca app phat hien duoc, hoi xac nhan tung cai
```

App khong nam trong danh sach tren (vi du mot MCP client tuy chinh)? Lay
doan JSON de tu dan vao config cua no:

```bash
nlm setup add json
```

> **Ten server khuyen dung:** `gemini-notebook-mcp` (executable van la
> `notebooklm-mcp`). Neu truoc do ban co cai 1 server Gemini Notebook/NotebookLM
> khac (vi du ten cu `notebooklm`), go bo truoc — nhieu agent (Hermes, v.v.)
> se bi lan ten tool neu 2 server cung dang ky `notebook_create`,
> `source_add`,... Xem [huong dan migrate day du](GETTING_STARTED.md#migrating-from-another-notebooklm-mcp).

Sau khi cau hinh xong, **khoi dong lai app** (dong han va mo lai, khong
chi reload) de app nhan config MCP moi.

## 5. Tu chay MCP server thu cong

Trong da so truong hop, **ban khong can tu chay `notebooklm-mcp` thu
cong** — app AI (Claude Code, Claude Desktop...) tu khoi dong no ngam khi
can, theo config da ghi o buoc 4 (transport mac dinh la `stdio`, giao
tiep qua stdin/stdout, khong mo port mang nao ca).

Chi can tu chay thu cong khi: ban dang debug, hoac muon dung transport
HTTP de 1 client mang ket noi toi (vi du MCP Inspector, hoac client tu
viet).

```bash
# Mac dinh: stdio (dung cho hau het AI client)
notebooklm-mcp

# Bat debug log (huu ich khi co loi)
notebooklm-mcp --debug

# Chay nhu HTTP server, chi lang nghe tren may minh (an toan)
notebooklm-mcp --transport http --host 127.0.0.1 --port 8000
```

Endpoint khi chay HTTP: `http://127.0.0.1:8000/mcp` (health check tai
`http://127.0.0.1:8000/health`).

> ⚠️ **Canh bao bao mat:** `notebooklm-mcp` **khong co co che xac thuc
> rieng** o tang HTTP. Mac dinh no tu choi bind ra ngoai `127.0.0.1`
> (bao loi va thoat) tru khi ban chu dong set
> `NOTEBOOKLM_ALLOW_EXTERNAL_BIND=1`. **Khong bao gio** expose port nay
> thang ra Internet — bat ky ai goi toi deu co toan quyen tren tai khoan
> Google dang dang nhap (doc/sua/xoa notebook...). Neu can truy cap tu xa,
> xem [Remote MCP Deployment](REMOTE_MCP.md) de biet cach lam dung (qua
> gateway co OAuth/HTTPS, hoac dung Claude Code Remote Control).

## 6. Xac minh moi thu hoat dong

Qua CLI:

```bash
nlm notebook list
```

Qua AI assistant da ket noi: hoi no goi tool `notebook_list` (hoac tuong
duong, tuy app dat ten tool the nao). Neu thay danh sach notebook hien co
cua ban → da ket noi thanh cong.

## 7. Cac lenh kiem tra/chan doan huu ich

```bash
nlm doctor              # Chan doan toan dien: storage, auth, browser, MCP wiring
nlm login --check       # Kiem tra rieng phan dang nhap con hop le khong
nlm auth refresh        # Lam moi session thu cong (huu ich cho cron/scheduler)
nlm setup list          # Liet ke app nao dang duoc cau hinh MCP
nlm usage                # Xem con lai bao nhieu quota (rolling window + weekly)
nlm --version            # Xem phien ban, tu kiem tra co ban moi tren PyPI khong
```

## 8. Xu ly su co thuong gap

| Trieu chung | Nguyen nhan thuong gap | Cach xu ly |
|---|---|---|
| AI assistant khong thay notebook nao / bao chua dang nhap | Chua `nlm login`, hoac dang sai profile | Chay `nlm login --check`; neu fail thi `nlm login` lai |
| `auth_status` bao `"stale"` | Cookie da cu, can lam moi | `nlm login` lai (hoac `nlm auth refresh` cho may chay tu dong) |
| Agent goi nham tool / lan lon 2 MCP server | Con cai server Gemini Notebook/NotebookLM cu ten khac | Go bo server cu, xem [huong dan migrate](GETTING_STARTED.md#migrating-from-another-notebooklm-mcp) |
| `nlm setup add claude-desktop` bao Claude Desktop con dang chay | App chua dong han, hoac tien trinh Crashpad con sot (macOS) | Dong han app roi chay lai; xem [Known Issues #6](KNOWN_ISSUES.md#6-claude-desktop-profile-setup) |
| Loi lien quan Keychain/Credential Manager (macOS/Windows) | Protected mode can quyen OS keystore, co the bi hoi lai khi doi Python/uv | Nhap mat khau dang nhap may, chon "Always Allow"; xem [Known Issues #8](KNOWN_ISSUES.md#8-protected-mode--keystore-environments) |
| Loi lien quan RPC/response bat thuong (vi du sau khi Google cap nhat NotebookLM) | Google doi protocol noi bo | Chay voi `--debug`; neu la loi protocol that su, xem [Known Issues #4](KNOWN_ISSUES.md#4-api-instability-undocumented-internal-apis) va (cho nguoi muon tu sua code) [Protocol Maintenance Guide](PROTOCOL_MAINTENANCE.md) |
| Chay tren server/Docker/SSH, Protected mode bao loi keystore | Protected mode can desktop session, khong dung duoc tren headless | Dung File mode: `nlm auth storage set file` |

Can chan doan sau hon chua co trong bang nay? Chay `nlm doctor` truoc, roi
xem [Known Issues](KNOWN_ISSUES.md) hoac [Authentication Guide →
Troubleshooting](AUTHENTICATION.md#troubleshooting).
