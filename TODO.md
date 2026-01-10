# TODO - Pet Insurance Platform

## High Priority - Bugs to Fix

(None currently)

---

## Medium Priority - Enhancements

### 3. Real AI Usage Tracking
- **Current**: AI tokens/costs in Cost Monitor are MOCK data
- **Need**: Connect to real Anthropic/OpenAI usage APIs
- **Options**:
  - Anthropic Admin API for organization usage
  - OpenAI Usage API for token consumption
  - Internal tracking by logging API calls
- **Files to Update**:
  - `claims_data_api/app/services/costs_service.py` - `/ai-usage` endpoint

---

## Completed

- [x] Connect real Azure Cost Management API (2026-01-10)
- [x] Connect real AWS Cost Explorer API (2026-01-10)
- [x] Fix AI Usage tab TypeError crash (2026-01-10)
- [x] Fix Admin Portal API URL (localhost -> production) (2026-01-10)
- [x] Fix DocGen service - added `pydantic-settings` and `aiofiles` (2026-01-10)
- [x] Configure DocGen URL in Agent Portal (2026-01-10)
