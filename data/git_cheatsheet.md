# Git Cheatsheet

This cheatsheet provides a quick reference for the most commonly used Git commands, including `rebase`.

## Basic Commands
* **`git init`**: Initializes a new Git repository in the current directory.
* **`git clone <repository_url>`**: Clones an existing repository from a URL.
* **`git status`**: Shows the current state of the working directory and staging area.
* **`git add <file>`**: Adds a file to the staging area.
* **`git add .`**: Adds all changes in the current directory to the staging area.
* **`git commit -m "Your commit message"`**: Records the staged changes as a new commit with a message.
* **`git commit -am "Your commit message"`**: Stages all modified and deleted files, then commits them with a message.
* **`git log`**: Shows the commit history.
* **`git log --oneline`**: Shows a condensed commit history.
* **`git diff`**: Shows changes between the working directory and the staging area.
* **`git diff --staged`**: Shows changes between the staging area and the last commit.

## Branching
* **`git branch`**: Lists all local branches.
* **`git branch <branch_name>`**: Creates a new branch.
* **`git checkout <branch_name>`**: Switches to an existing branch.
* **`git checkout -b <new_branch_name>`**: Creates a new branch and switches to it.
* **`git merge <branch_name>`**: Merges the specified branch into the current branch.
* **`git branch -d <branch_name>`**: Deletes a local branch (only if it's been merged).
* **`git branch -D <branch_name>`**: Forces deletion of a local branch.

## Remote Operations
* **`git remote -v`**: Lists configured remote repositories.
* **`git remote add <name> <url>`**: Adds a new remote repository with the given name.
* **`git fetch <remote>`**: Fetches changes from a remote repository without merging.
* **`git pull <remote> <branch>`**: Fetches and merges changes from a remote branch into the current branch.
* **`git push <remote> <branch>`**: Pushes local commits on a branch to the remote repository.
* **`git push -u <remote> <branch>`**: Pushes and sets the upstream tracking branch.

## Undoing Changes
* **`git reset <file>`**: Unstages a file (keeps file changes in working directory).
* **`git checkout -- <file>`**: Discards changes in the working directory for a specific file.
* **`git reset --hard HEAD`**: Discards all local changes and reverts to the last commit (USE WITH CAUTION).
* **`git revert <commit_hash>`**: Creates a new commit that undoes the changes of a previous commit.
* **`git commit --amend -m "Updated message"`**: Modifies the last commit message or adds new staged changes into it (if any files are staged).

## Rebase (Advanced)
* **`git rebase <target_branch>`**: Replays your current branch’s commits on top of `<target_branch>`. Useful for maintaining a linear history.
* **`git rebase -i HEAD~<n>`**: Interactively rebase the last `n` commits. Allows you to pick, reword, squash, fixup, or drop commits.
  * `pick`: Use the commit as is.
  * `reword`: Use the commit but edit the commit message.
  * `edit`: Use the commit but pause to amend it.
  * `squash`: Merge this commit into the previous commit, combining messages.
  * `fixup`: Merge this commit into the previous commit, discarding this commit’s message.
  * `drop`: Remove the commit entirely.
* **`git rebase --continue`**: Continues a rebase after resolving conflicts.
* **`git rebase --abort`**: Aborts the rebase process and returns to the original branch state.
* **`git rebase --skip`**: Skips the current patch and proceeds with the rebase.

## Stashing
* **`git stash`**: Temporarily saves changes that are not ready to be committed, reverting to the HEAD commit.
* **`git stash list`**: Shows a list of all stashed changes.
* **`git stash apply`**: Reapplies the most recently stashed changes without removing them from the stash list.
* **`git stash apply stash@{n}`**: Reapplies a specific stash entry (replace `n` with the index).
* **`git stash pop`**: Reapplies the most recent stash entry and removes it from the stash list.
* **`git stash drop stash@{n}`**: Deletes a specific stash entry.
* **`git stash clear`**: Removes all stash entries.

---

## ℹ️ Wanneer gebruik je welk Git-commando? (+ korte voorbeelden)
- `git status` → altijd voor commit/pull om te zien wat staged/niet.  
- `git add <file>` → gericht staged; `git add -p` om alleen delen te pakken.  
- `git commit -am "msg"` → snelle commit voor bestaande bestanden (nieuwe files eerst `git add`).  
- `git log --oneline --graph -20` → recent overzicht + structuur.  
- `git diff --staged` → check wat er echt gecommit wordt.  
- `git checkout -b feature/x` → nieuwe feature-branch starten.  
- `git merge main` → branch bijwerken met main (bewaar merge commit).  
- `git rebase main` → history netjes lineair maken voor PR.  
- `git reset --hard HEAD` → alleen gebruiken om lokale, ongepushede wijzigingen weg te gooien.  
- `git revert <hash>` → gepushte commit terugdraaien met nieuwe commit (veilig voor gedeelde branches).  
- `git stash && git pull && git stash pop` → snel lokaal werk parkeren, updaten, terugzetten.  
