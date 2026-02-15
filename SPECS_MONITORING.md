# NACHA Specifications Monitoring & Auto-Regeneration

## Overview

This system automatically monitors the `specs/official/` directory for changes and regenerates the YAML validation schemas with proper versioning.

**Key Features:**
- 📊 **Automatic Detection** - Detects added, modified, and deleted specification files
- 📝 **Semantic Versioning** - Auto-increments version (Major.Minor.Patch)
- 💾 **Version Backups** - Creates timestamped backups of each version
- 🚨 **Alert System** - Generates detailed alerts when changes occur
- 🔄 **CI/CD Integration** - GitHub Actions workflow for automatic regeneration
- ✅ **Validation** - Validates generated YAML specifications
- 🔐 **Change Tracking** - File hash tracking for accurate change detection

---

## How It Works

### 1. Change Detection

When files are added, modified, or deleted in `specs/official/`:

```
specs/official/
├── NACHA_FILE_FORMAT_SPECIFICATION.md  (modified)
└── NACHA_IMPLEMENTATION_GUIDE.md       (unchanged)
```

The system calculates SHA256 hashes and compares with the last known state.

### 2. Version Increment Rules

| Change Type | Action | Version Bump |
|---|---|---|
| File added | new specification | `1.0.0` → `1.1.0` (minor) |
| File modified | spec updated | `1.1.0` → `1.1.1` (patch) |
| File deleted | spec removed | `1.1.1` → `2.0.0` (major) |

### 3. Processing Steps

```
1. Detect Changes
   ↓ (File hash comparison)
   
2. Increment Version
   ↓ (Semantic versioning)
   
3. Create Backup
   ↓ (specs/versioned/v{version}_{timestamp}/)
   
4. Update YAML Specs
   ↓ (specs/yml/*.yml)
   
5. Generate Alert
   ↓ (specs/.versions/ALERT_{timestamp}.txt)
   
6. Save Metadata
   ↓ (specs/.versions/version_history.json)
   
7. Commit Changes
   ↓ (Auto-commit when triggered)
```

---

## Triggers

### GitHub Actions (Automatic)

**Triggers when:**
- Push to `main` or `develop` with changes in `specs/official/`
- Pull Request with changes in `specs/official/`
- Manual workflow dispatch via GitHub UI

**Workflow File:** `.github/workflows/regenerate-specs.yml`

**Jobs:**
1. `regenerate-specs` - Main regeneration
2. `validate-specs` - YAML validation
3. `notify-success` - Success notification

### Manual Trigger

```bash
# Run regeneration script directly
python scripts/regenerate_specs.py
```

---

## Directory Structure

```
nacha_parser/
├── specs/
│   ├── official/                          # SOURCE (Monitor this!)
│   │   ├── NACHA_FILE_FORMAT_SPECIFICATION.md
│   │   └── NACHA_IMPLEMENTATION_GUIDE.md
│   │
│   ├── yml/                               # OUTPUT (Auto-generated)
│   │   ├── nacha_validation_schema.yml
│   │   ├── nacha_validation_rules.yml
│   │   ├── nacha_error_definitions.yml
│   │   └── VERSION                        # Current version
│   │
│   ├── versioned/                         # VERSION HISTORY
│   │   ├── v1.0.0_20260214_150230/
│   │   │   ├── nacha_validation_schema.yml
│   │   │   ├── nacha_validation_rules.yml
│   │   │   ├── nacha_error_definitions.yml
│   │   │   └── MANIFEST.json
│   │   └── v1.0.1_20260214_152145/
│   │       └── ...
│   │
│   ├── .versions/                         # METADATA
│   │   ├── version_history.json           # Full version history
│   │   ├── ALERT_20260214_150230.txt      # Change alerts
│   │   └── ALERT_20260214_152145.txt
│   │
│   └── .regeneration.config.yml           # Configuration
│
└── .github/workflows/
    └── regenerate-specs.yml               # GitHub Actions workflow
```

---

## Version History File

**Location:** `specs/.versions/version_history.json`

```json
{
  "versions": [
    {
      "version": "1.0.0",
      "timestamp": "20260214_150230",
      "changes_summary": "Initial version",
      "backup_location": "specs/versioned/v1.0.0_20260214_150230"
    },
    {
      "version": "1.0.1",
      "timestamp": "20260214_152145",
      "changes_summary": "Added: 1 file, Modified: 0, Deleted: 0",
      "backup_location": "specs/versioned/v1.0.1_20260214_152145"
    },
    {
      "version": "1.1.0",
      "timestamp": "20260214_160000",
      "changes_summary": "Added: 0, Modified: 1, Deleted: 0",
      "backup_location": "specs/versioned/v1.1.0_20260214_160000"
    }
  ],
  "current_version": "1.1.0",
  "last_updated": "2026-02-14T16:00:00.123456",
  "file_hashes": {
    "NACHA_FILE_FORMAT_SPECIFICATION.md": "a1b2c3d4e5f6...",
    "NACHA_IMPLEMENTATION_GUIDE.md": "f6e5d4c3b2a1..."
  }
}
```

---

## Alert Format

When specifications change, an alert file is created:

**File:** `specs/.versions/ALERT_20260214_152145.txt`

```
╔══════════════════════════════════════════════════════════════╗
║         NACHA SPECIFICATION ALERT - VERSION 1.0.1            ║
╚══════════════════════════════════════════════════════════════╝

📋 CHANGES DETECTED IN specs/official/
──────────────────────────────────────────────────────────────

✅ ADDED (1):
   • NACHA_BUSINESS_RULES.md

📝 MODIFIED (0):

❌ DELETED (0):

──────────────────────────────────────────────────────────────
⚙️  ACTION TAKEN:
   • YAML specifications regenerated
   • Version incremented to 1.0.1
   • Backup created in specs/versioned/v1.0.1_20260214_152145/
   • Files committed to specs/yml/

📌 NEXT STEPS:
   1. Review changes in specs/yml/
   2. Run validation tests
   3. Commit and push changes
   4. Update implementation code if needed

⏱️  Generated: 2026-02-14 15:21:45
═══════════════════════════════════════════════════════════════
```

---

## Usage Guide

### Scenario 1: Add New Specification

1. **Create new markdown file** in `specs/official/`
   ```bash
   touch specs/official/NACHA_BUSINESS_RULES.md
   ```

2. **Commit the change**
   ```bash
   git add specs/official/NACHA_BUSINESS_RULES.md
   git commit -m "Add business rules specification"
   git push
   ```

3. **GitHub Actions triggers automatically:**
   - Detects new file (added)
   - Increments version minor: `1.0.0` → `1.1.0`
   - Creates backup of new version
   - Generates alert showing what changed
   - Auto-commits regenerated YAML files

4. **Review the alert:**
   - Check `specs/.versions/ALERT_*.txt`
   - Verify generated YAML files
   - Update implementation if needed

### Scenario 2: Modify Existing Specification

1. **Edit markdown file**
   ```bash
   nano specs/official/NACHA_FILE_FORMAT_SPECIFICATION.md
   # Make changes
   ```

2. **Commit and push**
   ```bash
   git add specs/official/NACHA_FILE_FORMAT_SPECIFICATION.md
   git commit -m "Update file format specification"
   git push
   ```

3. **Automatic regeneration:**
   - Detects modified file
   - Increments version patch: `1.1.0` → `1.1.1`
   - Creates backup
   - Generates alert
   - Auto-commits updates

### Scenario 3: Manual Regeneration

If you want to regenerate specs without committing:

```bash
# Navigate to project root
cd /Users/rjoshi/ai_projects/nacha_parser

# Run regenerator directly
python scripts/regenerate_specs.py
```

### Scenario 4: Check for Changes (No Regeneration)

```bash
# Check what would be regenerated
python scripts/regenerate_specs.py --check-only
```

---

## Implementation Integration

When specifications are regenerated, you need to:

1. **Reload YAML files** in your Python code:
   ```python
   import yaml
   
   with open('specs/yml/nacha_validation_schema.yml', 'r') as f:
       schema = yaml.safe_load(f)
   ```

2. **Update validation logic** if schema structure changes

3. **Run tests** to ensure compatibility:
   ```bash
   pytest tests/specifications/
   ```

---

## GitHub Actions Workflow Details

### Workflow: `regenerate-specs.yml`

**Location:** `.github/workflows/regenerate-specs.yml`

**Triggers:**
```yaml
on:
  push:
    paths:
      - 'specs/official/**'
    branches:
      - main
      - develop
  pull_request:
    paths:
      - 'specs/official/**'
  workflow_dispatch:  # Manual trigger
```

**Key Jobs:**

1. **regenerate-specs** (Main Job)
   - Runs `script/regenerate_specs.py`
   - Creates version backups
   - Commits changes to main branch
   - Creates pull request for PR branches

2. **validate-specs** (Validation Job)
   - Validates generated YAML syntax
   - Ensures all YAML is well-formed

3. **notify-success** (Notification Job)
   - Posts success message
   - Optional: Slack notifications (requires secret setup)

---

## Configuration

**File:** `specs/.regeneration.config.yml`

Contains:
- Monitor configuration (source, patterns)
- Regeneration settings (output, versioning)
- Notification options (alerts, commits)
- Validation rules
- GitHub Actions integration

**Modify this file to change:**
- Version increment rules
- Backup retention period
- Notification preferences
- Validation settings

---

## Troubleshooting

### Issue: Alert not generated

**Check:**
1. Ensure files are in `specs/official/` with `.md` extension
2. Verify file changes are detected: `git status`
3. Check workflow logs: GitHub Actions → regenerate-specs → workflow run

### Issue: Version not incrementing

**Check:**
1. Verify hash calculation: `specs/.versions/version_history.json`
2. Ensure change type is detected correctly (added/modified/deleted)
3. Check `.regeneration.config.yml` version rules

### Issue: YAML generation failed

**Check:**
1. Validate YAML files manually: `python -m yaml specs/yml/*.yml`
2. Check error details in workflow logs
3. Review specification markdown syntax

### Issue: Auto-commit not working

**Check:**
1. GitHub Actions has write permissions (check workflow settings)
2. Branch protection rules allow auto-commits
3. Verify git configuration in workflow

---

## Best Practices

### ✅ Do's

- **Commit specification changes separately** from code changes
- **Review alerts** before accepting auto-commits
- **Test implementation** after specification regeneration
- **Keep backup history** (helps track specification evolution)
- **Use clear commit messages** for spec changes

### ❌ Don'ts

- **Don't manually edit** YAML files (they're auto-generated)
- **Don't commit** to `specs/yml/` directly
- **Don't ignore version history** - it helps track breaking changes
- **Don't disable validation** - it catches errors early

---

## Commands Quick Reference

```bash
# Regenerate specs
python scripts/regenerate_specs.py

# Check for changes only
python scripts/regenerate_specs.py --check-only

# View version history
cat specs/.versions/version_history.json

# View latest alert
cat specs/.versions/ALERT_*.txt | tail -100

# View current specifications version
cat specs/yml/VERSION

# List all versions
ls -la specs/versioned/

# Restore previous version
cp -r specs/versioned/v1.0.0_20260214_150230/* specs/yml/
```

---

## Further Reading

- **Specification Format:** See `specs/official/NACHA_FILE_FORMAT_SPECIFICATION.md`
- **Implementation Guide:** See `specs/official/NACHA_IMPLEMENTATION_GUIDE.md`
- **Validation Rules:** See `specs/yml/nacha_validation_rules.yml`

---

**Last Updated:** 2026-02-14  
**Version:** 1.0  
**Author:** Automated System
