---
description: Debug an issue or error in the codebase
---

# Debug Command

Systematically investigate and resolve an issue.

## Instructions

1. **Understand the Problem**
   - What is the error message?
   - What behavior is expected vs actual?
   - When did it start/what changed?

2. **Gather Evidence**
   - Check relevant logs
   - Examine error stack traces
   - Review recent changes

3. **Isolate the Cause**
   - Narrow down to specific file/function
   - Trace data flow
   - Check dependencies

4. **Identify Root Cause**
   - Don't fix symptoms
   - Find the actual source of the problem

5. **Propose Solution**
   - If `$ARGUMENTS` includes "fix", implement the fix
   - Otherwise, explain the fix needed

## Arguments

`$ARGUMENTS` should describe:
- The error message or symptom
- Or "fix" followed by the issue description

## Common Investigations

| Symptom | Check |
|---------|-------|
| Connection refused | Service running? Port correct? |
| Import error | Package installed? Path correct? |
| 500 error | Server logs, stack trace |
| Test failure | Expected vs actual, test setup |
| Timeout | Network, database, async issues |

## Examples

```
/debug "TypeError: undefined is not a function"
/debug "API returns 500 on login"
/debug fix "tests failing after auth changes"
/debug "ECONNREFUSED on port 8000"
```

## Output

Provide:
1. Issue summary
2. Investigation steps taken
3. Root cause identified
4. Solution (implemented or proposed)
5. Prevention recommendations
