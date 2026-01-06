---
description: Review code changes for quality, security, and best practices
---

# Code Review Command

Review the current code changes using the code-reviewer agent.

## Instructions

1. **Identify Changes**
   - Check `git diff` for unstaged changes
   - Check `git diff --staged` for staged changes
   - If no changes, ask what to review

2. **Perform Review**
   - Use the code-reviewer agent for thorough analysis
   - Check for security issues
   - Verify best practices
   - Look for performance concerns

3. **Report Findings**
   - Summarize strengths and issues
   - Provide specific file:line references
   - Give actionable recommendations
   - State if ready to commit

## Arguments

If `$ARGUMENTS` is provided:
- If it's a file path, review that specific file
- If it's "staged", review only staged changes
- If it's "all", review all modified files

## Output

Provide a structured review with:
- Overview of what was reviewed
- Issues found (with severity)
- Recommendations
- Final verdict (ready/needs-work)
