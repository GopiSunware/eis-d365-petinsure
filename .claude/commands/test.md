---
description: Run tests and fix any failures
---

# Test Runner Command

Run the project's test suite and handle any failures.

## Instructions

1. **Detect Test Framework**
   - Check for pytest (Python)
   - Check for jest/vitest (JavaScript/TypeScript)
   - Look at package.json or pyproject.toml

2. **Run Tests**
   - Execute the appropriate test command
   - Capture output and results
   - Note any failures

3. **Handle Failures**
   - If `$ARGUMENTS` includes "fix", attempt to fix failures
   - Analyze error messages
   - Identify root causes
   - Apply fixes and re-run

4. **Report Results**
   - Summary of pass/fail counts
   - Details of any failures
   - Coverage if available

## Arguments

- No args: Run all tests
- `fix`: Run tests and fix failures
- `coverage`: Run with coverage report
- `watch`: Run in watch mode
- File path: Run tests for specific file

## Examples

```
/test              # Run all tests
/test fix          # Run and fix failures
/test coverage     # Run with coverage
/test src/auth     # Run tests for auth module
```
