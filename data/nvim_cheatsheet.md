# 🧠 Primeagen's Vim Cheat Sheet

Master horizontal motions, text objects, and plugin workflows with this high-speed guide based on two Vim videos by ThePrimeagen.

---

## ⚡ 1. Horizontal Motion Essentials

Move across the line with precision:

| Motion         | What it Does                            |
|----------------|------------------------------------------|
| `f<char>`      | Jump **to** character (forward)          |
| `F<char>`      | Jump **to** character (backward)         |
| `t<char>`      | Jump **before** character (forward)      |
| `T<char>`      | Jump **before** character (backward)     |
| `;` / `,`      | Repeat last `f`/`t` motion forward/back  |
| `0`            | Beginning of line (column 0)             |
| `^`            | First non-blank character of line        |
| `$`            | End of line                              |

### 🛠 Combine with Commands:
- `d$` → delete to end of line  
- `yT)` → yank up to before `)`  
- `d2F{` → delete up to 2nd `{`

---

## ✂️ 2. Text Object Power Moves

| Command    | What it Does                           |
|------------|-----------------------------------------|
| `viw`      | Select inner word                       |
| `va"`      | Select around quotes                    |
| `vi{` / `va{` | Inside/around braces                  |
| `di(`      | Delete inside parentheses               |
| `yiW`      | Yank "big word" (whitespace delimited)  |

> 💡 Use capital versions (like `viW`) for wider selections.

**Voorbeelden**  
- Haakjesinhoud vervangen: `ci(` → typ nieuwe tekst → `Esc`.  
- String zonder quotes kopiëren: `yi'` (yank inside quotes).  

---

## ✍️ 3. Insert Mode Shortcuts

| Command | Action                                |
|---------|----------------------------------------|
| `I`     | Insert at beginning of line            |
| `A`     | Insert at end of line                  |
| `o`     | New line **below**, then insert        |
| `O`     | New line **above**, then insert        |

---

## 🧪 4. Buffers & Windows

- **Buffer** = In-memory file representation
- **Window** = View into a buffer

💡 Multiple windows can show the *same buffer* — changes sync instantly.

**Wanneer gebruik je wat?**  
- `:bnext` / `:bprev` → wisselen tussen geopende files zonder opnieuw te openen.  
- `:split` / `:vsplit` → twee views naast/onder elkaar; handig voor referentie en vergelijken.  
- `:q` sluit alleen het huidige venster; `:bd` sluit buffer.  

---

## 🔌 5. Plugin Toolkit

### 🚀 Telescope  
Fuzzy file search, live grep, buffer switching, and more  
🔗 https://github.com/nvim-telescope/telescope.nvim

#### 🗝️ Kickstart.nvim Keymap Example:
```lua
local builtin = require('telescope.builtin')

vim.keymap.set('n', '<leader>?', builtin.oldfiles, { desc = '[?] Find recently opened files' })
vim.keymap.set('n', '<leader><space>', builtin.buffers, { desc = '[ ] Find existing buffers' })
vim.keymap.set('n', '<leader>/', function()
  builtin.current_buffer_fuzzy_find(require('telescope.themes').get_dropdown {
    winblend = 10,
    previewer = false,
  })
end, { desc = '[/] Fuzzily search in current buffer' })

vim.keymap.set('n', '<leader>sf', builtin.find_files, { desc = '[S]earch [F]iles' })
vim.keymap.set('n', '<leader>sh', builtin.help_tags, { desc = '[S]earch [H]elp' })
vim.keymap.set('n', '<leader>sw', builtin.grep_string, { desc = '[S]earch current [W]ord' })
vim.keymap.set('n', '<leader>sg', builtin.live_grep, { desc = '[S]earch by [G]rep' })
vim.keymap.set('n', '<leader>sd', builtin.diagnostics, { desc = '[S]earch [D]iagnostics' })
