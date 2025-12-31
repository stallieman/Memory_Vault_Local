# git_details

# 🚀 Stap-voor-stap: Project naar GitHub Pushen

## 📋 Scenario 1: Nieuw Project (Eerste keer)

### Stap 1: Maak een Repository op GitHub
1. Ga naar [github.com](https://github.com)
2. Klik op het **+** icoon rechts boven → **New repository**
3. Vul in:
   - Repository name (bijv. `my-project`)
   - Beschrijving (optioneel)
   - Public of Private
   - **NIET** "Initialize with README" aanvinken (als je al lokale files hebt)
4. Klik **Create repository**

---

### Stap 2: Initialiseer Git Lokaal
Open je terminal in je project folder:

```bash
# Controleer of je in de juiste folder zit
pwd

# Initialiseer Git repository
git init
```

---

### Stap 3: Voeg Files Toe aan Staging Area

```bash
# Bekijk status van files
git status

# Voeg ALLE files toe
git add .

# Of voeg specifieke files toe
git add README.md
git add src/main.py
```

**💡 Tip:** Gebruik `git add .` voor alle files, of `git add <bestandsnaam>` voor specifieke files.

---

### Stap 4: Maak je Eerste Commit

```bash
# Commit met een duidelijke message
git commit -m "Initial commit"

# Of meer gedetailleerd
git commit -m "feat: add initial project structure"
```

**✅ Goede commit messages:**
- `"Initial commit"`
- `"feat: add user authentication"`
- `"fix: resolve login bug"`
- `"docs: update README"`

---

### Stap 5: Verbind met GitHub Remote

```bash
# Voeg remote repository toe (vervang USERNAME en REPO)
git remote add origin https://github.com/USERNAME/REPO.git

# Controleer of remote correct is toegevoegd
git remote -v
```

**📝 Voorbeeld:**
```bash
git remote add origin https://github.com/johndoe/my-project.git
```

---

### Stap 6: Push naar GitHub

```bash
# Push naar main branch (eerste keer met -u flag)
git push -u origin main

# Of als je branch 'master' heet
git push -u origin master
```

**💡 De `-u` flag:**
- Betekent `--set-upstream`
- Koppelt je lokale branch aan de remote branch
- Daarna kan je gewoon `git push` gebruiken

---

## ✅ Klaar! Je project staat nu op GitHub! 🎉

---

## 📋 Scenario 2: Bestaand Project Updaten

Als je al een keer hebt gepusht en nu nieuwe wijzigingen wilt toevoegen:

### Quick Workflow (3 stappen)

```bash
# 1. Voeg gewijzigde files toe
git add .

# 2. Commit met message
git commit -m "feat: add new feature"

# 3. Push naar GitHub
git push
```

### Stap-voor-stap Uitgelegd

#### Stap 1: Controleer Status
```bash
# Bekijk welke files gewijzigd zijn
git status
```

Output ziet er ongeveer zo uit:
```
Changes not staged for commit:
  modified:   src/main.py
  
Untracked files:
  new-file.txt
```

---

#### Stap 2: Stage je Wijzigingen

```bash
# Alle wijzigingen toevoegen
git add .

# Of specifieke files
git add src/main.py
git add new-file.txt

# Controleer wat je hebt toegevoegd
git status
```

---

#### Stap 3: Commit je Wijzigingen

```bash
# Commit met duidelijke message
git commit -m "fix: resolve database connection issue"

# Voor modified files kun je ook direct committen
git commit -am "update: improve error handling"
```

**💡 `-am` flag:** 
- Stages automatisch alle **gewijzigde** files
- Werkt NIET voor nieuwe files
- Commit in één stap

---

#### Stap 4: Push naar GitHub

```bash
# Push naar remote
git push

# Of expliciet naar main branch
git push origin main
```

---

## 🔄 Scenario 3: Pull Eerst (Als er remote wijzigingen zijn)

Als iemand anders heeft gepusht of je hebt op GitHub zelf gewijzigd:

```bash
# 1. Haal eerst remote wijzigingen op
git pull

# 2. Los eventuele conflicts op (zie onder)

# 3. Dan pas pushen
git add .
git commit -m "merge remote changes"
git push
```

---

## 🛠️ Handige Extra Commando's

### Bekijk Commit History
```bash
# Volledige history
git log

# Compacte versie (aanbevolen)
git log --oneline

# Laatste 5 commits
git log --oneline -5
```

---

### Bekijk Verschillen
```bash
# Verschillen tussen working directory en staging
git diff

# Verschillen tussen staging en laatste commit
git diff --staged

# Verschillen van specifiek file
git diff README.md
```

---

### Remote Repository Info
```bash
# Bekijk remote URLs
git remote -v

# Remote URL wijzigen
git remote set-url origin https://github.com/USERNAME/NEW-REPO.git
```

---

### Branch Overzicht
```bash
# Lokale branches
git branch

# Alle branches (inclusief remote)
git branch -a

# Huidige branch naam
git branch --show-current
```

---

## ⚠️ Veelvoorkomende Problemen & Oplossingen

### ❌ Probleem 1: "fatal: not a git repository"
**Oplossing:**
```bash
# Je bent niet in een git folder, initialiseer eerst
git init
```

---

### ❌ Probleem 2: "error: failed to push some refs"
**Oorzaak:** Remote heeft wijzigingen die jij niet hebt

**Oplossing:**
```bash
# Haal eerst remote wijzigingen op
git pull origin main

# Of force pull (gebruik met voorzichtigheid!)
git pull origin main --rebase

# Dan push
git push origin main
```

---

### ❌ Probleem 3: "Permission denied (publickey)"
**Oorzaak:** Geen SSH key of niet geauthenticeerd

**Oplossing Optie 1 - HTTPS gebruiken:**
```bash
# Verander naar HTTPS URL
git remote set-url origin https://github.com/USERNAME/REPO.git
```

**Oplossing Optie 2 - SSH Key toevoegen:**
1. Genereer SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
2. Voeg toe aan GitHub: Settings → SSH and GPG keys → New SSH key
3. Test: `ssh -T git@github.com`

---

### ❌ Probleem 4: Verkeerde files gecommit
**Oplossing - Laatste commit aanpassen:**
```bash
# Voeg nieuwe wijzigingen toe aan laatste commit
git add forgotten-file.txt
git commit --amend --no-edit

# Of wijzig ook de commit message
git commit --amend -m "Updated commit message"

# Force push (als je al had gepusht)
git push --force
```

**⚠️ Let op:** `--force` alleen gebruiken als je zeker weet wat je doet!

---

### ❌ Probleem 5: Merge Conflicts
**Wanneer:** Bij `git pull` als remote en local wijzigingen botsen

**Oplossing:**
```bash
# 1. Na git pull zie je conflict
git status

# 2. Open conflicted files en los op (verwijder <<<< ==== >>>> markers)

# 3. Mark als resolved
git add conflicted-file.py

# 4. Commit de merge
git commit -m "resolve merge conflict"

# 5. Push
git push
```

---

## 📁 .gitignore - Belangrijke Files Uitsluiten

Maak een `.gitignore` file in je project root:

```bash
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
*.egg-info/

# Node.js
node_modules/
npm-debug.log
yarn-error.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets (BELANGRIJK!)
.env
*.key
*.pem
config/secrets.json

# Build outputs
dist/
build/
*.log
```

**💡 Tip:** Voeg `.gitignore` toe VOOR je eerste commit!

---

## 🎯 Best Practices

### ✅ DO's:
1. **Commit vaak** - kleine, logische changes
2. **Duidelijke messages** - beschrijf WAT en WAAROM
3. **Pull voordat je pusht** - voorkom conflicts
4. **Test lokaal** - voordat je pusht
5. **Gebruik .gitignore** - voor secrets en build files
6. **Branches gebruiken** - voor nieuwe features

### ❌ DON'Ts:
1. **Geen secrets pushen** - API keys, passwords, tokens
2. **Geen grote binaries** - grote bestanden horen niet in git
3. **Niet force pushen** - op shared branches
4. **Geen vage messages** - "update" of "fix stuff" zijn niet nuttig
5. **Niet alles committen** - gebruik .gitignore

---

## 🔁 Complete Workflow Voorbeeld

```bash
# === DAG 1: Project opzetten ===
mkdir my-project
cd my-project
git init
touch README.md
echo "# My Project" > README.md

# .gitignore aanmaken
cat > .gitignore << EOF
__pycache__/
.env
node_modules/
EOF

# Eerste commit
git add .
git commit -m "Initial commit: project setup"

# Verbind met GitHub
git remote add origin https://github.com/USERNAME/my-project.git
git push -u origin main

# === DAG 2: Feature toevoegen ===
# ... werk aan je code ...
git status                          # Check wat je hebt gewijzigd
git add src/new-feature.py          # Stage specifieke file
git commit -m "feat: add user login feature"
git push                            # Push naar GitHub

# === DAG 3: Bug fix ===
# ... fix een bug ...
git add .
git commit -m "fix: resolve null pointer exception"
git push

# === DAG 4: Pull remote changes ===
git pull                            # Haal wijzigingen van anderen op
# ... los eventuele conflicts op ...
git push                            # Push je eigen wijzigingen
```

---

## 🎓 Git Workflow Summary

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Working Directory  →  Staging Area  →  Repository │
│                                                     │
│      git add              git commit               │
│                                                     │
│                      git push →  GitHub             │
│                      git pull ←  GitHub             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Reference Commands

```bash
# === Setup (eerste keer) ===
git init
git remote add origin <url>
git add .
git commit -m "Initial commit"
git push -u origin main

# === Dagelijks gebruik ===
git add .
git commit -m "message"
git push

# === Updates ophalen ===
git pull

# === Status checken ===
git status
git log --oneline

# === Problemen oplossen ===
git pull                     # Eerst pullen bij conflicts
git reset <file>            # Unstage file
git checkout -- <file>      # Discard changes
```

---

## 📚 Handige Resources

- **GitHub Docs:** https://docs.github.com
- **Git Cheatsheet:** https://education.github.com/git-cheat-sheet-education.pdf
- **Interactive Git Tutorial:** https://learngitbranching.js.org

---

## ✨ Laatste Tips

1. **Commit early, commit often** - kleine commits zijn makkelijker te tracken
2. **Pull before you push** - voorkom merge conflicts
3. **Read error messages** - Git geeft vaak duidelijke hints
4. **Practice makes perfect** - Git lijkt complex maar wordt makkelijker met gebruik
5. **Backup is belangrijk** - GitHub is ook je backup!

**Success!** 🎉 Je bent nu klaar om als een pro met Git en GitHub te werken!

