# Data Storage Structure

All project data is now stored within the project folders, ready for deployment to Azure.

## EIS Dynamics POC - DocGen Service (ws7_docgen)

**Base Path:** `eis-dynamics-poc/src/ws7_docgen/data/`

```
ws7_docgen/data/
├── batches/
│   ├── batches.json          # Batch processing metadata
│   ├── fingerprints.json     # Document fingerprints for duplicate detection
│   └── .gitkeep
├── storage/
│   └── uploads/              # Uploaded documents
├── temp/                     # Temporary ZIP extraction
├── exports/                  # Generated exports (PDF, Word, CSV)
└── .gitignore               # Excludes runtime data from git
```

**Environment Variables:**
- `LOCAL_STORAGE_PATH` - defaults to `{BASE_DIR}/data/storage`
- `TEMP_DIR` - defaults to `{BASE_DIR}/data/temp`

## PetInsure360 Backend

**Base Path:** `petinsure360/backend/data/`

```
backend/data/
├── uploads/                  # Customer uploaded documents
│   └── .gitkeep
├── pipeline/
│   ├── pipeline_state.json   # Pipeline execution state
│   └── .gitkeep
├── raw/
│   └── claims_sample.json    # Synthetic test data (kept in git)
├── claim_scenarios.json      # Test scenarios (kept in git)
└── .gitignore               # Excludes runtime data, keeps sample data
```

## What Changed

### Before (❌ Bad for Azure deployment)
```python
# Hardcoded /tmp paths - lost on reboot, not deployable
BATCHES_FILE = "/tmp/docgen/batches.json"
LOCAL_STORAGE_PATH = "/tmp/docgen/storage"
UPLOAD_DIR = "/tmp/petinsure360_uploads"
```

### After (✅ Good for Azure deployment)
```python
# Project-relative paths - deployable to Azure
from pathlib import Path
from app.config import DATA_DIR  # Computed from BASE_DIR

BATCHES_FILE = str(DATA_DIR / "batches" / "batches.json")
LOCAL_STORAGE_PATH = str(DATA_DIR / "storage")
UPLOAD_DIR = str(BASE_DIR / "data" / "uploads")
```

## Files Updated

### DocGen Service (ws7_docgen)
- ✅ `app/config.py` - Added `DATA_DIR` constant
- ✅ `app/routers/upload.py` - Batches and uploads
- ✅ `app/agents/validate_agent.py` - Fingerprints
- ✅ `app/exporters/csv_exporter.py` - Export directory
- ✅ `app/exporters/pdf_exporter.py` - Export directory
- ✅ `app/exporters/word_exporter.py` - Export directory

### PetInsure360 Backend
- ✅ `app/api/docgen.py` - Upload directory
- ✅ `app/api/pipeline.py` - Pipeline state file

## Verification

All `/tmp` references removed from code:
```bash
grep -r "/tmp/" eis-dynamics-poc/src/ws7_docgen/app/     # Returns: 0
grep -r "/tmp/" petinsure360/backend/app/                 # Returns: 0
```

## Azure Deployment

When deploying to Azure App Service:
1. Data directories are created automatically on startup
2. Use Azure Storage for persistent data:
   - Set `USE_LOCAL_STORAGE=False` in production
   - Configure `AZURE_STORAGE_CONNECTION_STRING`
   - Uploads go to Azure Blob Storage instead of local filesystem
3. For stateful data (batches, pipeline state), use:
   - Azure Cosmos DB, or
   - Azure File Share mounted to `/data`

## Git Behavior

`.gitignore` files ensure:
- ✅ Sample/synthetic data IS committed
- ❌ Runtime data (uploads, batches) is NOT committed
- ✅ Empty directory structure IS preserved with `.gitkeep`

## Benefits

1. **Portable** - All artifacts in project folder
2. **Azure-ready** - Easy to deploy to App Service
3. **Version control** - Sample data tracked, runtime data excluded
4. **No data loss** - Survives reboots (unlike /tmp)
5. **Development** - Local testing uses same paths as production
