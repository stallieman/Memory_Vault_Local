# VIM Motions

## 1. Move to start/end of line
- `0` — go to **start** of line  
- `$` — go to **end** of line  

Use `$` + `p` to paste at line end, `0` before indentation.

## 2. Word navigation
- `w` — jump to **start of next word**  
- `b` — jump **back to start** of previous word  
- `e` — jump to **end of word**  

Great for quick edits: `ciw` after `w` to change next word.

## 3. Jump to specific character
- `f<char>` — jump **forward** to character in the line (e.g. `f,`, `f(`, etc)  
- `F<char>` — jump **backward** to character in the line  

Use `;`/`,` to repeat forward/backward (e.g. hop door CSV).

## 4. Change inside word
- `ciw` — **change inside word** (replace whole word under cursor, e.g. for `{{date}}`)

## 5. Change/delete/yank to end of line
- `C` — change to end of line (`c$` does the same)  
- `D` — delete to end of line (`d$`)  
- `Y` — yank (copy) the whole line  

Handig bij code: `C` om rest van statement te herschrijven.

## 6. Visual mode for selections
- `v` — start **visual mode** (select text with movement keys, then operate)  
- `V` — **visual line mode** (select whole lines)  

Combineer met actie: `VjjJ` → 3 regels selecteren en samenvoegen.

## 7. Undo/redo
- `u` — **undo**  
- `Ctrl+r` — **redo**  

---

## Moving Between Files and Buffers

- `:e <filename>` — open or create a file  
- `:w` — save file  
- `:q` — quit file  
- `:bnext` / `:bprev` — next/previous buffer  

Quick session voorbeeld: `:e app.py` → wijzig → `:w` → `:bnext` naar tests.  

---

## For Python/SQL:

- `%` — jump between matching brackets or parentheses (handy in code!)
- `gg` — go to top of file
- `G` — go to bottom of file

Gebruik `%` in SQL om naar parende haakjes in CTE/CASE te springen.  
