"""
Knowledge Base Reorganization Tool
Phase A: Dry-run scan and planning
Phase B: Apply moves (only after explicit GO)

Prioriteiten (hoog → laag):
1) sql, 2) tdv, 3) elastic, 4) python, 5) docker, 6) git, 7) ai, 8) ebooks, 9) misc
"""

import os
import csv
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================
NOTES_DIR = Path(r"C:\Notes")
OUTPUT_DIR = Path(r"C:\Projecten\memory-vault-main\memory-vault-main\data")

# Priority order (index = priority, lower = higher priority)
# Updated with new groups: personal, tools, microsoft
PRIORITY_GROUPS = [
    "sql", "tdv", "elastic", "python", "docker", "git", 
    "ai", "ebooks", "microsoft", "tools", "personal", "misc"
]

# Specific file routing rules (filename pattern -> (source_group, subfolder))
SPECIFIC_FILE_RULES = {
    # CV files -> personal/cv/
    "cv_marco": ("personal", "cv"),
    "marco_stalman_cv": ("personal", "cv"),
    
    # vim/nvim -> tools/vim/ or tools/nvim/
    "nvim_": ("tools", "nvim"),
    "neovim": ("tools", "nvim"),
    "vim_": ("tools", "vim"),
    "lazyvim": ("tools", "vim"),
    
    # Microsoft certs and tools
    "dp-900": ("microsoft", "certs"),
    "dp-203": ("microsoft", "certs"),
    "az-": ("microsoft", "certs"),
    "power bi": ("microsoft", "powerbi"),
    "powerbi": ("microsoft", "powerbi"),
    
    # TDV specific files
    "howto-scipt-and-sp": ("tdv", ""),  # TDV stored procedures guide
    "howto-script-and-sp": ("tdv", ""),  # alternate spelling
}

# Cheatsheets: which domain takes priority over "tools"
# If filename contains both "cheatsheet" AND one of these, use the domain
CHEATSHEET_DOMAIN_PRIORITY = {
    "docker": "docker",
    "compose": "docker",
    "git": "git", 
    "sql": "sql",
    "pandas": "python",
    "python": "python",
    "elastic": "elastic",
    "logstash": "elastic",
    "kibana": "elastic",
    "tdv": "tdv",
    "tibco": "tdv",
}

# Mapping rules: keyword patterns -> source_group
# These are used to classify files that aren't already in a priority folder
CLASSIFICATION_RULES = {
    "sql": ["sql", "database", "query", "joins", "cte", "postgres", "mysql", "mssql"],
    "tdv": ["tdv", "tibco", "data_virtualization", "datavirtualization", "tib_tdv"],
    "elastic": ["elastic", "elasticsearch", "kibana", "logstash", "elk", "opensearch"],
    "python": ["python", "pandas", "numpy", "flask", "django", "fastapi", "pip", "venv"],
    "docker": ["docker", "container", "dockerfile", "compose", "kubernetes", "k8s"],
    "git": ["git", "github", "gitlab", "version_control", "branching", "merge"],
    "ai": ["ai_engineer", "ai-engineer", "stappenplan-ai", "machine_learning_notes", 
           "ml_notes", "llm_notes", "rag_notes"],  # Only AI notes, not ebooks
    "microsoft": ["azure", "microsoft", "sharepoint", "teams", "office365"],
    "tools": ["keybind", "keymap", "cheatsheet", "shortcut"],
    "personal": ["cv", "resume", "sollicitatie"],
}

# Files/folders to skip (never move)
SKIP_PATTERNS = [
    ".obsidian",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
]
# Files to skip entirely (system files, not useful for indexing)
SKIP_FILES = [
    ".ds_store",
    "thumbs.db",
    "desktop.ini",
    ".gitignore",
    ".gitkeep",
]
# Extensions to never move (executables/scripts that might break)
RISKY_EXTENSIONS = [".exe", ".bat", ".cmd", ".ps1", ".sh", ".msi"]

# Cheatsheet patterns -> tools folder with specific subfolder
CHEATSHEET_TOOL_MAP = {
    "vim": "vim",
    "nvim": "nvim", 
    "neovim": "nvim",
    "lazyvim": "vim",
    "devtools": "devtools",
    "linux": "linux",
}


class NotesReorganizer:
    """Scans and plans reorganization of C:/Notes folder."""
    
    def __init__(self, notes_dir: Path = NOTES_DIR):
        self.notes_dir = notes_dir
        self.plan: List[Dict] = []
        self.stats = defaultdict(int)
        self.collisions: Dict[str, List[str]] = defaultdict(list)
        self.risks: List[Dict] = []
        
    def scan(self) -> None:
        """Scan all files and create reorganization plan."""
        print(f"📂 Scanning {self.notes_dir}...")
        
        for item in self.notes_dir.rglob("*"):
            if item.is_file():
                self._process_file(item)
        
        # Detect collisions
        self._detect_collisions()
        
        print(f"✓ Scanned {len(self.plan)} files")
    
    def _should_skip(self, path: Path) -> Tuple[bool, str]:
        """Check if file/folder should be skipped."""
        path_str = str(path).lower()
        filename = path.name.lower()
        
        # Skip system files (like .DS_Store)
        if filename in SKIP_FILES:
            return True, f"skip_system_file:{filename}"
        
        # Skip special folders
        for pattern in SKIP_PATTERNS:
            if pattern.lower() in path_str:
                return True, f"skip_folder:{pattern}"
        
        # Skip risky extensions
        if path.suffix.lower() in RISKY_EXTENSIONS:
            return True, f"risky_extension:{path.suffix}"
        
        return False, ""
    
    def _get_current_folder(self, path: Path) -> str:
        """Get the top-level folder relative to notes_dir."""
        try:
            rel_path = path.relative_to(self.notes_dir)
            parts = rel_path.parts
            if len(parts) > 1:
                return parts[0].lower()
            return ""  # Root file
        except ValueError:
            return ""
    
    def _classify_file(self, path: Path) -> Tuple[str, str, str]:
        """
        Classify a file into a source_group.
        Returns (source_group, subfolder, reason)
        """
        filename = path.name.lower()
        stem = path.stem.lower()
        current_folder = self._get_current_folder(path)
        
        # RULE 1: Check specific file rules first (CV, vim, DP-900, etc.)
        for pattern, (group, subfolder) in SPECIFIC_FILE_RULES.items():
            if pattern in filename or pattern in stem:
                return group, subfolder, f"specific_rule:{pattern}"
        
        # RULE 2: If already in a priority folder, keep it there
        if current_folder in PRIORITY_GROUPS:
            return current_folder, "", "already_in_priority_folder"
        
        # RULE 3: Ebooks folder - ALL stay in ebooks (no AI split for ebooks)
        if current_folder == "ebooks":
            return "ebooks", "", "ebook_folder"
        
        # RULE 4: Cheatsheets - check if they belong to a DOMAIN first (sql, docker, etc.)
        if "cheatsheet" in filename or "keybind" in filename or "keymap" in filename:
            # FIRST: Check if cheatsheet belongs to a domain (sql, docker, git, etc.)
            for domain_pattern, domain_folder in CHEATSHEET_DOMAIN_PRIORITY.items():
                if domain_pattern in filename:
                    return domain_folder, "", f"cheatsheet:domain:{domain_pattern}"
            
            # SECOND: Check if it's a tool-specific cheatsheet (vim, nvim, devtools)
            for tool_pattern, tool_subfolder in CHEATSHEET_TOOL_MAP.items():
                if tool_pattern in filename:
                    return "tools", tool_subfolder, f"cheatsheet:tool:{tool_pattern}"
            
            # THIRD: Generic cheatsheet -> tools/misc
            return "tools", "misc", "cheatsheet:generic"
        
        # RULE 5: Readwise -> misc
        if current_folder == "readwise":
            return "misc", "readwise", "readwise_folder"
        
        # RULE 6: Check filename against classification rules
        for group, keywords in CLASSIFICATION_RULES.items():
            for keyword in keywords:
                if keyword in filename or keyword in stem:
                    return group, "", f"keyword_match:{keyword}"
        
        # RULE 7: Check full path for classification hints
        path_lower = str(path).lower()
        for group, keywords in CLASSIFICATION_RULES.items():
            for keyword in keywords:
                if keyword in path_lower:
                    return group, "", f"path_match:{keyword}"
        
        # RULE 8: PDF files without classification -> ebooks (not inbox)
        if path.suffix.lower() == ".pdf":
            return "ebooks", "uncategorized", "pdf_to_ebooks"
        
        # RULE 9: Root files or unclassified -> inbox
        if current_folder == "":
            return "inbox", "", "root_file"
        
        # Unknown folder -> misc with original folder name preserved
        return "misc", current_folder, f"unclassified_folder:{current_folder}"
    
    def _process_file(self, path: Path) -> None:
        """Process a single file and add to plan."""
        # Check if should skip
        should_skip, skip_reason = self._should_skip(path)
        if should_skip:
            self.plan.append({
                "current_path": str(path),
                "proposed_path": str(path),  # No change
                "proposed_source_group": "skip",
                "reason": skip_reason,
                "risk": "skip"
            })
            self.stats["skipped"] += 1
            return
        
        # Classify the file (now returns subfolder too)
        source_group, subfolder, reason = self._classify_file(path)
        
        # Calculate proposed path
        rel_path = path.relative_to(self.notes_dir)
        current_folder = self._get_current_folder(path)
        
        # Determine if file needs to move
        if current_folder == source_group and not subfolder:
            # Already in correct folder (no subfolder requirement)
            proposed_path = path
            risk = "none"
        elif current_folder == source_group and subfolder:
            # In correct group but might need subfolder
            current_parts = rel_path.parts
            if len(current_parts) > 1 and current_parts[1].lower() == subfolder:
                # Already in correct subfolder
                proposed_path = path
                risk = "none"
            else:
                # Needs to move to subfolder
                proposed_path = self.notes_dir / source_group / subfolder / path.name
                risk = "move"
        else:
            # Needs to move to different group
            if subfolder:
                proposed_path = self.notes_dir / source_group / subfolder / path.name
            else:
                proposed_path = self.notes_dir / source_group / path.name
            risk = "move"
        
        # Check if classification is ambiguous
        if "unclassified" in reason or (reason == "root_file" and source_group == "inbox"):
            risk = "ambiguous" if risk == "move" else risk
        
        self.plan.append({
            "current_path": str(path),
            "proposed_path": str(proposed_path),
            "proposed_source_group": source_group,
            "reason": reason,
            "risk": risk
        })
        
        self.stats[source_group] += 1
        if risk not in ["none", "skip"]:
            self.stats["needs_move"] += 1
    
    def _detect_collisions(self) -> None:
        """Detect filename collisions in proposed paths."""
        path_files = defaultdict(list)
        
        for item in self.plan:
            if item["risk"] != "skip":
                proposed = item["proposed_path"]
                path_files[proposed].append(item["current_path"])
        
        for proposed_path, sources in path_files.items():
            if len(sources) > 1:
                for source in sources:
                    self.collisions[proposed_path].append(source)
                    # Mark as collision in plan
                    for item in self.plan:
                        if item["current_path"] == source:
                            item["risk"] = "collision"
                            self.risks.append({
                                "type": "collision",
                                "file": source,
                                "proposed": proposed_path,
                                "collides_with": [s for s in sources if s != source]
                            })
    
    def get_summary(self) -> str:
        """Generate summary of the plan."""
        lines = []
        lines.append("=" * 70)
        lines.append("📊 DRY-RUN REORGANIZATION PLAN SUMMARY")
        lines.append("=" * 70)
        lines.append("")
        lines.append("📁 Files per proposed source_group:")
        lines.append("-" * 40)
        
        all_groups = PRIORITY_GROUPS + ["inbox", "skip"]
        for group in all_groups:
            count = self.stats.get(group, 0)
            if count > 0:
                if group in PRIORITY_GROUPS:
                    priority = PRIORITY_GROUPS.index(group) + 1
                    lines.append(f"  [{priority:2}] {group:12} : {count:5} files")
                else:
                    lines.append(f"  [ -] {group:12} : {count:5} files")
        
        lines.append("-" * 40)
        lines.append(f"  TOTAL            : {len(self.plan):5} files")
        lines.append(f"  Needs moving     : {self.stats.get('needs_move', 0):5} files")
        lines.append(f"  Skipped          : {self.stats.get('skipped', 0):5} files")
        lines.append("")
        
        # Risks
        lines.append("⚠️  TOP RISKS (need your approval):")
        lines.append("-" * 40)
        
        risk_items = [item for item in self.plan if item["risk"] not in ["none", "skip"]]
        
        # Collisions first
        collisions = [item for item in risk_items if item["risk"] == "collision"]
        if collisions:
            lines.append(f"\n🔴 COLLISIONS ({len(collisions)}):")
            for item in collisions[:5]:
                lines.append(f"    {item['current_path']}")
                lines.append(f"    → {item['proposed_path']}")
        
        # Ambiguous
        ambiguous = [item for item in risk_items if item["risk"] == "ambiguous"]
        if ambiguous:
            lines.append(f"\n🟡 AMBIGUOUS ({len(ambiguous)}):")
            for item in ambiguous[:10]:
                lines.append(f"    {Path(item['current_path']).name}")
                lines.append(f"    → {item['proposed_source_group']} ({item['reason']})")
        
        # Regular moves (just count)
        moves = [item for item in risk_items if item["risk"] == "move"]
        if moves:
            lines.append(f"\n🟢 MOVES ({len(moves)} total)")
            # Show first 5
            for item in moves[:5]:
                lines.append(f"    {Path(item['current_path']).name}")
                lines.append(f"    → {item['proposed_source_group']}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def save_plan(self, output_path: Path = None) -> Path:
        """Save plan to CSV file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = OUTPUT_DIR / f"reorganization_plan_{timestamp}.csv"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "current_path", "proposed_path", "proposed_source_group", "reason", "risk"
            ])
            writer.writeheader()
            writer.writerows(self.plan)
        
        return output_path
    
    def apply_moves(self, csv_path: Path) -> List[Dict]:
        """
        PHASE B: Apply moves from CSV plan.
        Only call this after explicit GO!
        """
        moves_log = []
        
        # Read plan
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            plan = list(reader)
        
        print(f"📦 Applying {len(plan)} planned operations...")
        
        for item in plan:
            if item["risk"] in ["skip", "none"]:
                continue
            
            if item["risk"] == "collision":
                print(f"  ⚠️  SKIP collision: {item['current_path']}")
                moves_log.append({
                    "action": "skip_collision",
                    "from": item["current_path"],
                    "to": item["proposed_path"]
                })
                continue
            
            src = Path(item["current_path"])
            dst = Path(item["proposed_path"])
            
            if not src.exists():
                print(f"  ⚠️  Source missing: {src}")
                moves_log.append({
                    "action": "skip_missing",
                    "from": str(src),
                    "to": str(dst)
                })
                continue
            
            # Create destination folder
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            try:
                src.rename(dst)
                print(f"  ✓ {src.name} → {item['proposed_source_group']}/")
                moves_log.append({
                    "action": "moved",
                    "from": str(src),
                    "to": str(dst),
                    "source_group": item["proposed_source_group"]
                })
            except Exception as e:
                print(f"  ❌ Failed: {src.name} - {e}")
                moves_log.append({
                    "action": "failed",
                    "from": str(src),
                    "to": str(dst),
                    "error": str(e)
                })
        
        return moves_log


def main_dry_run():
    """Execute Phase A: Dry-run scan and planning."""
    print("=" * 70)
    print("🔍 FASE A: DRY-RUN REORGANIZATION PLAN")
    print("=" * 70)
    print()
    
    reorganizer = NotesReorganizer()
    reorganizer.scan()
    
    # Save CSV
    csv_path = reorganizer.save_plan()
    print(f"\n📄 Plan saved to: {csv_path}")
    
    # Print summary
    print()
    print(reorganizer.get_summary())
    
    print()
    print("=" * 70)
    print("❓ Type 'GO' to apply these changes, or review the CSV first.")
    print("=" * 70)
    
    return csv_path


def main_apply(csv_path: str):
    """Execute Phase B: Apply moves."""
    print("=" * 70)
    print("📦 FASE B: APPLYING REORGANIZATION")
    print("=" * 70)
    print()
    
    reorganizer = NotesReorganizer()
    moves_log = reorganizer.apply_moves(Path(csv_path))
    
    # Save log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = OUTPUT_DIR / f"moves_log_{timestamp}.csv"
    
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        if moves_log:
            writer = csv.DictWriter(f, fieldnames=moves_log[0].keys())
            writer.writeheader()
            writer.writerows(moves_log)
    
    print(f"\n📄 Move log saved to: {log_path}")
    
    # Summary
    moved = sum(1 for m in moves_log if m["action"] == "moved")
    failed = sum(1 for m in moves_log if m["action"] == "failed")
    skipped = sum(1 for m in moves_log if m["action"].startswith("skip"))
    
    print(f"\n✅ Completed: {moved} moved, {skipped} skipped, {failed} failed")
    print("\n🔄 Run re-ingest to update ChromaDB:")
    print("   python ingestion.py")
    
    return log_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "apply":
        if len(sys.argv) > 2:
            main_apply(sys.argv[2])
        else:
            print("Usage: python reorganize_notes.py apply <csv_path>")
    else:
        main_dry_run()
