# Handoff: Generator Change Required Before course-gating Skill Works

**Date:** 2026-05-04
**Context:** Bill and the web Claude built a course-gating skill tonight that locks unit pages until prior units are completed. The skill is ready and lives in `skills/course-gating/`. But before it can work, the static-web generator needs one small change. This note explains what to change and why.

## The Decision Bill Made

Gating is now a **standard feature** of every static-web course. Not opt-in. Every course built with the toolkit's static-web sync should have gating turned on automatically.

## The Problem

The course-gating skill needs to read browser storage to find out whether a student passed a unit's knowledge check. The gate can't open until it sees a record like "passed: true" for the unit's KC.

But right now, the static-web generator emits unit knowledge checks with two attributes that prevent any record from being written:

```html
<section class="test-section"
         data-storage-key=""
         data-persist-attempts="false"
         data-simple-mode="true"
         ...>
```

`data-storage-key=""` means "don't save anywhere." `data-persist-attempts="false"` means "don't save attempts at all." So the existing JS in your shared script bundle, when it sees a simple-mode KC with these settings, never writes a record. The gating skill has nothing to read.

The course final assessment, by contrast, has these set correctly already:

```html
<section class="test-section"
         data-storage-key="course-{slug}-final-attempts"
         data-persist-attempts="true"
         data-simple-mode="false"
         ...>
```

So the final works for gating already. Only the unit KCs need the change.

## The Fix

In the generator code that emits unit knowledge check `<section class="test-section">` HTML, change two attributes to be populated by default:

**Before:**
```python
data_storage_key = ""  # or unset
data_persist_attempts = "false"
```

**After:**
```python
data_storage_key = f"course-{course_slug}-unit-{unit_number}-kc-attempts"
data_persist_attempts = "true"
```

Keep `data-simple-mode="true"` as it is. Simple mode means the KC has unlimited retakes (no lockout). That's correct for unit knowledge checks. The change here only flips on storage, not retake behavior.

The shared script bundle that processes test-section elements already handles persistence when the storage key is set. Look for the function that submits a test attempt; you'll see logic like:

```javascript
// Persist this attempt.
var record = {
  attempt_number: attemptNumber,
  question_ids: visible.map(...),
  wrong_ids: wrongIds,
  score: pct,
  passed: passed,
  timestamp: new Date().toISOString()
};
attempts.push(record);
writeAttempts(section, attempts);
```

`writeAttempts(section, attempts)` writes to `localStorage` if and only if `section.dataset.storageKey` is non-empty and `section.dataset.persistAttempts === "true"`. So once the generator emits the right attributes, the existing JS does the right thing automatically. No JavaScript changes needed.

## Verification

After making the generator change:

1. Re-run `bes sync` on a test static-web course (or whatever command produces the static-web output).
2. Open a unit page in a browser, take the KC, submit it.
3. Open browser DevTools, go to Application > Local Storage, look for a key like `course-{slug}-unit-1-kc-attempts`. You should see a JSON array containing the attempt with a `passed: true` or `passed: false` field.
4. If yes, the change worked. If no, check that both `data-storage-key` and `data-persist-attempts="true"` made it into the rendered HTML.

## Then Run the Gating Skill

Once the generator change ships and a course is regenerated:

```
cd ~/Code/your-course
python3 -m skills.course-gating.lib.gating --site ./site
```

Or via Claude Code, paste a prompt like:

```
Run the course-gating skill in apply mode against ./site for this course.
```

The skill will:
- Discover unit pages and the final
- Read the now-populated storage keys
- Generate `assets/gating.js` and `assets/gating.css`
- Patch every HTML file to wire up gating
- Show a summary

After that, opening Unit 2 in the browser without completing Unit 1 will show a "complete Unit 1 first" lockout card. The student must read every lesson and pass the unit KC.

## Why Standard, Not Opt-In

Bill chose "standard." Every static-web course gets gating, no flag needed. This is the right call for a few reasons:

- Static-web courses are typically structured for linear learning anyway
- One less config knob to remember per course
- If a future course really needs free-roam navigation, the gating skill has a `--remove` mode that strips it cleanly

If a future use case requires opt-in, add an `enable_gating: false` flag to course-config.yaml, have the generator skip emitting `data-storage-key` and `data-persist-attempts` when the flag is false, and let the gating skill detect the empty keys and gracefully no-op.

## Files Created Tonight

```
skills/course-gating/
  SKILL.md
  lib/
    __init__.py
    gating.py
  templates/
    gating.js.template
    gating.css.template
```

The skill is fully functional once the generator change ships. Bill has been working with desktop Claude on the generator (which is presumably under a Phase 18 or similar visual polish iteration). Desktop Claude has the generator code; web Claude does not. So this change is a desktop Claude task.

## What Bill Saw Working Tonight

I ran a smoke test against Bill's uploaded sample course pages. The skill correctly:
- Found 1 unit page (only unit-1.html was uploaded, not all 6)
- Found the final.html
- Parsed the lesson IDs from unit-1.html
- Detected the final's storage key
- Detected the missing storage key on the unit-1 KC and emitted a clear warning

So the skill's detection logic is verified. The actual gating will be verified after the generator change ships and a real 6-unit course is regenerated.

End of handoff.
