# ⚠️ CRITICAL DEVELOPMENT RULES ⚠️

## 🚫 NEVER USE SYSTEM /tmp/ FOLDER

### ❌ FORBIDDEN - DO NOT DO THIS:
```python
# WRONG - Data lost on reboot, not deployable to Azure
UPLOAD_DIR = "/tmp/uploads"
STATE_FILE = "/tmp/data.json"
CACHE_DIR = "/tmp/cache"
```

### ✅ CORRECT - USE PROJECT-RELATIVE PATHS:

#### For Temporary Work Files
If you need temporary storage during development or processing:

```python
# Create tmp folder INSIDE the project
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "tmp"  # Project-local tmp folder
TEMP_DIR.mkdir(exist_ok=True)

# Now you can use it
temp_file = TEMP_DIR / "processing.tmp"
```

**Project Structure:**
```
your-service/
├── app/
├── data/          # Persistent data
├── tmp/           # Temporary work files (add to .gitignore)
└── .gitignore     # Include: tmp/
```

#### For Persistent Data
Always use the `data/` folder:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Organized subdirectories
UPLOADS_DIR = DATA_DIR / "uploads"
STATE_FILE = DATA_DIR / "state" / "app_state.json"
EXPORTS_DIR = DATA_DIR / "exports"
```

## Why This Matters

### 1. **Azure Deployment Fails**
- `/tmp` is ephemeral on Azure App Service
- Data disappears between deployments
- Not accessible in containerized environments

### 2. **Data Loss**
- System `/tmp` cleared on reboot
- No backup, no recovery
- Production data lost permanently

### 3. **Not Portable**
- Can't package the project
- Can't version control
- Can't test locally then deploy

### 4. **Team Collaboration**
- Other developers can't run your code
- CI/CD pipelines fail
- Docker builds incomplete

## Migration Checklist

When you see `/tmp` in any code:

- [ ] Create project-local `tmp/` or `data/` folder
- [ ] Update all hardcoded `/tmp` paths
- [ ] Add to `.gitignore` if temporary
- [ ] Test that services restart correctly
- [ ] Verify data persists after reboot

## Git Configuration

**For temporary work files (`tmp/`):**
```gitignore
# .gitignore
tmp/
*.tmp
*.cache
```

**For persistent data (`data/`):**
```gitignore
# .gitignore in data/ folder
*
!.gitignore
!.gitkeep
!raw/           # Keep sample data
!*.example      # Keep example configs
```

## Real Example from This Project

### Before (BROKEN):
```python
# ws7_docgen/app/routers/upload.py
BATCHES_FILE = "/tmp/docgen/batches.json"  # ❌ LOST ON REBOOT

# petinsure360/backend/app/api/docgen.py
UPLOAD_DIR = "/tmp/petinsure360_uploads"   # ❌ NOT DEPLOYABLE
```

### After (FIXED):
```python
# ws7_docgen/app/config.py
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# ws7_docgen/app/routers/upload.py
from app.config import DATA_DIR
BATCHES_FILE = str(DATA_DIR / "batches" / "batches.json")  # ✅ PERSISTENT

# petinsure360/backend/app/api/docgen.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = str(BASE_DIR / "data" / "uploads")            # ✅ DEPLOYABLE
```

## Quick Reference

| Need | Use | Don't Use |
|------|-----|-----------|
| Temporary processing | `{PROJECT}/tmp/` | `/tmp/` |
| Persistent data | `{PROJECT}/data/` | `/tmp/` |
| Uploads | `{PROJECT}/data/uploads/` | `/tmp/uploads/` |
| Cache | `{PROJECT}/tmp/cache/` | `/tmp/cache/` |
| State files | `{PROJECT}/data/state/` | `/tmp/state/` |
| Exports | `{PROJECT}/data/exports/` | `/tmp/exports/` |

## Exception

The ONLY acceptable use of system `/tmp`:
- Truly ephemeral data (< 1 second lifetime)
- OS-managed temp files (e.g., `tempfile.NamedTemporaryFile()`)
- Immediately deleted after use

Even then, prefer project-local `tmp/` for clarity.

---

## 📋 Files Updated in January 2025 Migration

This migration removed ALL `/tmp` usage:

**EIS Dynamics POC (ws7_docgen):**
- ✅ `app/config.py`
- ✅ `app/routers/upload.py`
- ✅ `app/agents/validate_agent.py`
- ✅ `app/exporters/csv_exporter.py`
- ✅ `app/exporters/pdf_exporter.py`
- ✅ `app/exporters/word_exporter.py`

**PetInsure360:**
- ✅ `backend/app/api/docgen.py`
- ✅ `backend/app/api/pipeline.py`

**Verification:**
```bash
grep -r "/tmp/" eis-dynamics-poc/src/ws7_docgen/app/     # Returns: 0 ✅
grep -r "/tmp/" petinsure360/backend/app/                 # Returns: 0 ✅
```

---

**REMEMBER:** If you see `/tmp/` in any future code or documentation, it's a **BUG** that must be fixed immediately!
