---
name: Bug Report
about: Report a defect found during testing
title: "[BUG] "
labels: bug
assignees: ""
---

## Bug Summary

<!-- One-sentence description of the defect -->

---

## Tracking Information

| Field | Value |
|-------|-------|
| **Bug ID** | BUG-XXXX *(assign from bug-registry.md)* |
| **Severity** | Critical / High / Medium / Low |
| **Status** | Open / In Progress / Fixed / Closed |
| **Found In Build** | `build-XXX-XXXXXXX` *(run number + short SHA)* |
| **Fixed In Build** | `build-XXX-XXXXXXX` *(fill when resolved)* |
| **Test Case That Found It** | `module::ClassName::test_name` |
| **Test Type** | Unit / Integration / Security / Performance / E2E |

---

## Environment

- **Component**: Backend API / Frontend / AI Module / E2E
- **Python/Node Version**:
- **Commit SHA**: 

---

## Steps to Reproduce

1. 
2. 
3. 

---

## Expected Result

<!-- What should have happened -->

---

## Actual Result

<!-- What actually happened — include error message or stack trace -->

```
paste error here
```

---

## Root Cause Analysis

<!-- Fill in after investigation -->

---

## Fix Description

<!-- Describe the fix and which files were changed -->

---

## Verification

- [ ] Test case that found the bug now passes on the fix build
- [ ] No regression in related test cases
- [ ] Fix committed to the appropriate branch
