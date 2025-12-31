# Neovim Keybindings and Tips

Leader key: `<Space>`

## Essentials
- `\<leader>w` — Save current file
- `\<leader>q` — Quit current window
- `\<leader>Q` — Quit all without saving

## Search & Files
- `\<leader>ff` — Find files (Telescope)
- `\<leader>fg` — Live grep in project (Telescope)
- `\<leader>fb` — List buffers (Telescope)
- `\<leader>fh` — Search help tags (Telescope)
- `\<leader>fz` — FZF-Lua file finder

## LSP (Language Server)
- `gd` — Go to definition
- `gD` — Go to declaration
- `gi` — Go to implementation
- `gr` — List references
- `K` — Hover docs
- `\<leader>rn` — Rename symbol
- `\<leader>ca` — Code action
- `[d` / `]d` — Prev/next diagnostic

## Run & Format
- `\<leader>f` — Format buffer via Conform (Stylua, Black, Prettier, SQL formatter)
- Format on save: enabled (via Conform)
- Python run (shell): `:!python3 %`
- Python run (terminal split): `:terminal python3 %`
- Python debug: `<F5>`
- Direct Black (optional): `:!black %`
- Command-line format: `:lua require('conform').format({ async = true, lsp_fallback = true })`

## Debugging (nvim-dap)
- `<F5>` — Start/continue
- `<F10>` — Step over
- `<F11>` — Step into
- `<F12>` — Step out
- `\<leader>db` — Toggle breakpoint
- `\<leader>dr` — Toggle REPL

## Databases (vim-dadbod + UI)
- `\<leader>du` — Toggle DB UI
- Auto-exec for table helpers: ON by default. Toggle via `:DBUIToggleAutoExec` or `\<leader>dx`
- SQLite connections: `:DBUIAddConnection sqlite:~/Projects/SQL/your.db`
- Or set env: `export DBUI_URL='sqlite:~/Projects/SQL/your.db'`
- Helper: run `nvimsql your.db` (uses `DBUI_SQL_DIR=~/Projects/SQL`)
- Auto-load: any `*.db`, `*.sqlite`, `*.sqlite3` in `~/Projects/SQL` appear under Connections (via `g:dbs`).
- SQLite table helpers: `Count`, `Schema`, `Indexes`, `Foreign_Keys` (available per table)
- Drawer width: 50 columns (change with `let g:db_ui_winwidth=<num>`)
- Saved queries location: `~/Projects/SQL/db_ui_queries` (`let g:db_ui_save_location`)
- Save current query: `\<Leader>W` (db_ui mapping)
- Completion in SQL buffers is enabled via `vim-dadbod-completion`.

## Copilot
- `\<leader>cp` — Toggle Copilot suggestion auto-trigger / dismiss
- `\<leader>cc` — Open Copilot Chat panel
- Inline (insert mode): `Ctrl-l` accept, `Alt-]` next, `Alt-[` prev, `Ctrl-]` dismiss

## Appearance
- Colors: Catppuccin (Mocha). Transparent background enabled
- Switch flavour: `:Catppuccin [latte|frappe|macchiato|mocha]`

## Notes
- Statusline: lualine shows mode/branch/filename/position.
- Treesitter powers syntax and indentation.
- Telescope provides file and text search.

---

# Vim Motion Magic (Quick Tips)
- Move by words: `w` (next word), `b` (back), `e` (end)
- Jump to line: `gg` (top), `G` (bottom), `{count}G` (line number)
- Line positions: `0` (start), `^` (first non-blank), `$` (end)
- Find characters: `f{char}` forward, `F{char}` backward; `t{char}` up to before
- Repeat last find: `;` (same direction), `,` (reverse)
- Jumps: `%` to matching bracket/paren
- Screen scroll: `Ctrl-d` half down, `Ctrl-u` half up
- Marks: `m{letter}` to set, `` `{letter}` `` to jump
- Change inside: `ciw` (change inside word), `ci"` (inside quotes), `ci(`, `ci{`
- Delete around: `daw`, `da"`, `da(`, `da{`
- Yank (copy) to system clipboard: `"+y` (visual selection) or `"+yy` (line)
- Indent blocks: `>`/`<` after selecting with `V` (linewise)
- Replace single char: `r{char}`; repeat last change with `.`
- Counts amplify: `3w`, `5j`, `10dd` etc.

Practice tip: use motions with operators (d/c/y) to edit rapidly without the mouse.

## LSP: Getting Started
- `:LspInfo` — Show active clients, servers, and status
- `:checkhealth vim.lsp` — Diagnose setup and root detection issues
- Start/stop/restart: `:LspStart [name]`, `:LspStop [name]`, `:LspRestart [name]`
- Enable debug logs: `:lua vim.lsp.set_log_level("debug")`
- Log file path: `:lua print(vim.lsp.get_log_path())`
- Root folders matter. Open files inside your project (e.g. under a folder with `.git`, `pyproject.toml`, `package.json`).
- Install/update servers: `:Mason`, `:MasonInstall <name>` (e.g. `pyright`, `lua-language-server`, `sqls`)
