---
name: course-gating
version: 1.0
description: Gate unit advancement until prior unit is completed (lessons viewed AND knowledge check passed). Hard gate, prevents direct URL navigation. Final assessment locked until all units pass.
inputs:
  - course_root: folder_path, optional, defaults to current working directory
  - site_root: folder_path, required (where the generated static-web output lives, typically ./site or ./build)
  - mode: enum (apply, dry-run, remove), default apply
  - require_quiz_pass: boolean, default true (false means lessons-viewed-only gate)
outputs:
  - {site_root}/assets/gating.js (new file, the gating logic)
  - Modified HTML files in {site_root}: index.html, unit-N.html, final.html (gating script tag added, lock UI markup injected)
  - Console summary of files modified
dependencies:
  - course-spec-builder (course needs a spec)
  - repo-bootstrap (course needs the structure)
  - sync/static-web (must have been run; this skill modifies the static-web output)
phase: 5
status: ready
subject_neutral: true
audience_neutral: true
---

# Course Gating

Adds hard gating to a generated static-web course so that:

- A unit page is locked until the prior unit is completed
- "Completed" means: every lesson in the unit was scrolled-viewed AND the unit's knowledge check has at least one attempt with `passed: true`
- A locked unit page shows a "complete Unit N first" message instead of the lesson content. URL navigation is blocked at page-load time.
- The course final is locked until all units are completed
- Index page unit cards visually show locked state and become non-clickable when locked

The skill is non-destructive. Running it on an already-gated site is idempotent. Running with `mode: remove` strips the gating cleanly.

## When to Use

Run after `bes sync` (or after the static-web generator produces site output) on any course that wants enforced linear progression. Skip for courses where students should be free to jump around.

Do NOT use this skill if:
- The static-web output does not exist yet (run sync first)
- The course is being delivered through a platform LMS like Thinkific or Canvas (those have native gating; use their UI)
- The course is intentionally non-linear (skip-around exploration)

## How the Gate Works

The skill writes a single JavaScript file at `{site_root}/assets/gating.js`. Every gated page loads this script. The script:

1. **On every page load**, reads progress state from localStorage:
   - Lesson-viewed state from `course-{slug}-viewed-lessons` (existing key from your generator)
   - Quiz attempts from per-section `data-storage-key` values on test-section elements (existing pattern)
2. **Computes per-unit completion**: a unit is complete when all its lessons are in viewed-lessons AND its KC has any attempt with `passed: true`
3. **On unit pages**: if any prior unit is incomplete, hides the lesson content and shows a lock card pointing the student back to the earliest incomplete unit
4. **On final page**: if any unit is incomplete, hides the assessment and shows a lock card listing missing units
5. **On index page**: each unit card with prior-unit incomplete gets a `locked` class. CSS makes it greyed out, removes hover effects, and an inline click handler prevents navigation. A small "Complete Unit N first" badge appears on the card.

Progress state lives entirely in the student's localStorage. There is no server. If a student clears their browser data, they start over.

## Steps

1. Find the course root by walking up from cwd until course-config.yaml is found.

2. Verify `site_root` exists and contains `index.html`, at least one `unit-N.html`, and (probably) `final.html`. If not, stop and tell the user to run sync first.

3. Read `course-config.yaml` to get the course slug and unit count. The slug is needed because lesson-viewed storage uses the key `course-{slug}-viewed-lessons`.

4. Scan the site to discover the unit pages. Look for files named `unit-1.html`, `unit-2.html`, etc. Record how many units exist and their numbers.

5. For each unit page, parse the HTML to extract:
   - The lesson IDs in this unit (from `article.lesson-card[id]` elements)
   - The KC test-section's `data-storage-key` value
   - The KC test-section's `data-pass-threshold` value
   
   Store this as a JSON object the gating script will read at runtime.

6. For the final page, extract:
   - The final test-section's `data-storage-key`
   - The pass threshold

7. Write `{site_root}/assets/gating.js`. The script contains:
   - The course slug
   - The discovered unit map (lesson IDs and storage keys per unit)
   - The final's storage key
   - The completion logic and the lock UI rendering
   - Templates for the lock cards (in plain string concatenation, so no build step needed)

8. Write `{site_root}/assets/gating.css`. Holds styles for:
   - `.unit-card.locked` (greyed out, no hover, lock badge)
   - `.gating-lockout` (the lock card shown on locked unit and final pages)

9. Patch each HTML file:
   - Add `<link rel="stylesheet" href="assets/gating.css">` in the head if not already there
   - Add `<script src="assets/gating.js" defer></script>` before the closing `</body>` if not already there
   - For unit pages and final.html: wrap the main content in a `<div id="gated-content">...</div>` so the gating script can hide it cleanly. If wrapper already exists, skip.
   - For index.html: add `data-unit-number="N"` attributes to each `.unit-card` anchor so the gating script can identify them.

10. Idempotency check: if the script tag already exists, skip the inject. The skill can run repeatedly without breaking anything.

11. If `mode: dry-run`, print what would change but don't write files.

12. If `mode: remove`, delete `assets/gating.js` and `assets/gating.css`, strip the script and link tags from each HTML, unwrap `gated-content` divs, remove `data-unit-number` attrs.

13. Show a summary:
    - Files written or modified
    - Number of units gated
    - Whether the final is gated
    - Any warnings (no KC found in a unit, no final page, etc.)

## Output: gating.js Structure

The script is roughly 180 lines, plain ES5 (matches your existing scripts), no dependencies. Skeleton:

```javascript
(function () {
  // ============================================================
  // Course Gating (Path A skill, can be merged into generator later)
  // Reads existing localStorage keys produced by the static-web
  // generator. Adds: prior-unit-complete enforcement on unit and
  // final pages, locked card state on the index.
  // ============================================================

  var CONFIG = {
    courseSlug: "{COURSE_SLUG}",
    units: [
      // injected at build time, one entry per unit
      {
        number: 1,
        lessonIds: ["unit-1-lesson-1-...", "..."],
        kcStorageKey: "course-{slug}-unit-1-kc-attempts"
      },
      // ...
    ],
    final: {
      storageKey: "course-{slug}-final-attempts"
    }
  };

  function getViewedLessons() {
    // Read from `course-{slug}-viewed-lessons` localStorage
  }

  function getKcAttempts(storageKey) {
    // Parse JSON from a quiz storage key
  }

  function isUnitComplete(unit) {
    // All lessons viewed AND any KC attempt has passed: true
  }

  function isFinalUnlocked() {
    // All units complete
  }

  function findFirstIncompleteUnit() {
    // Return the unit number of the earliest incomplete unit, or null
  }

  function gateUnitPage(currentUnitNumber) {
    // If any prior unit incomplete, hide #gated-content and show lock
  }

  function gateFinalPage() {
    // If any unit incomplete, hide #gated-content and show lock
  }

  function gateIndexPage() {
    // Iterate .unit-card[data-unit-number]; lock those with incomplete prerequisites
  }

  // Detect which page we're on and run the right gate.
  function init() {
    var currentUnit = parseCurrentUnitNumber();
    if (currentUnit !== null) {
      gateUnitPage(currentUnit);
    } else if (isFinalPage()) {
      gateFinalPage();
    } else if (isIndexPage()) {
      gateIndexPage();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
```

## Output: gating.css Structure

```css
/* Locked unit card on the index */
.unit-card.locked {
  opacity: 0.55;
  cursor: not-allowed;
  pointer-events: none;
  position: relative;
}
.unit-card.locked::after {
  content: "Locked";
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  background: var(--bg-soft);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--rule);
}

/* Lock card shown on a locked unit or final page */
.gating-lockout {
  max-width: 640px;
  margin: 48px auto;
  padding: 32px;
  text-align: center;
  border: 1px solid var(--rule);
  border-radius: var(--radius-md);
  background: var(--bg-soft);
}
.gating-lockout h2 {
  color: var(--brand);
  margin-top: 0;
}
.gating-lockout .gating-cta {
  display: inline-block;
  margin-top: 16px;
  padding: 12px 22px;
  background: var(--brand);
  color: #fff;
  text-decoration: none;
  font-weight: 700;
  border-radius: var(--radius-sm);
}
```

## Examples

### Example 1: First gate run on a fresh course

State: course generated, six unit pages, final page. No gating yet.

Command (via prompt to Claude Code, since this is a Phase 5 skill that still uses the LLM-driven workflow):
```
Run course-gating in apply mode against ./site
```

Result:
- assets/gating.js written (about 6 KB)
- assets/gating.css written (about 1 KB)
- index.html: 6 unit cards now have `data-unit-number`, head has new link tag, body has new script tag
- unit-1.html through unit-6.html: each has `gated-content` wrapper, link and script tags added
- final.html: same

Console summary:
```
Files modified: 8
- index.html (added 6 data-unit-number attrs, link tag, script tag)
- unit-1.html through unit-6.html (added gated-content wrapper, link, script)
- final.html (added gated-content wrapper, link, script)
Files written: 2
- assets/gating.js
- assets/gating.css
Units gated: 6 (units 2-6 require prior unit completion)
Final gated: yes
Unit 1 not gated (no prerequisite)
```

### Example 2: Re-run on already-gated site

State: gating already applied yesterday. Course author re-syncs after editing lessons.

Result: skill detects existing script tags, skips injection. assets/gating.js is regenerated to match current unit structure (in case unit count or storage keys changed). No duplicate modification.

### Example 3: Removing gating

State: course author decides to allow free navigation.

Command:
```
Run course-gating in remove mode against ./site
```

Result:
- assets/gating.js deleted
- assets/gating.css deleted
- All script and link tags stripped
- gated-content wrappers unwrapped
- data-unit-number attrs removed

Course is back to free navigation.

## Quality Checks

Before declaring done:
- gating.js parses as valid JavaScript (no syntax errors)
- Every unit page has the gated-content wrapper (visible by ID)
- The CONFIG object in gating.js matches the actual lesson IDs in the HTML
- The storage keys in gating.js match the data-storage-key values in the HTML
- Running the skill twice produces no diff (idempotent)
- Removing then re-applying produces the same result as the first apply

## Common Mistakes

- **Hardcoding the slug.** Read it from course-config.yaml, never assume.
- **Missing the lesson IDs.** The lesson-viewed storage uses the article id, not the lesson filename. Parse the HTML, do not guess.
- **Quiz storage key drift.** Different course generations may use different storage keys. Always read them from the HTML, never construct them.
- **Forgetting the final.** Easy to miss because final.html is structured slightly differently from unit pages. Test that the final lockout works after applying.
- **Breaking existing scripts.** The gating script must use the IIFE pattern with no globals (matches your existing script style).
- **Aggressive locking.** If lesson IDs in the HTML do not match what's in viewed-lessons localStorage (because a student visited mid-development before IDs stabilized), they may get permanently locked. Ship a "reset progress" link in the lockout card so a student can recover.

## The Hook for Future Generator Merge

This skill is Path A: a standalone post-processor. To merge into the generator (Path B) later:

1. Move the contents of `gating.js` to a template in the generator's templates folder
2. Move the contents of `gating.css` to the generator's main stylesheet
3. Have the generator emit `data-unit-number` attrs on unit cards directly
4. Have the generator emit `gated-content` wrappers directly
5. Add a `gating: true` flag to course-config.yaml that the generator reads to decide whether to emit the gating elements
6. Delete this standalone skill once the generator has it baked in

The interface is stable: the gating only depends on the existing localStorage shape (`viewed-lessons`, attempt arrays per quiz). As long as that shape stays put, swapping Path A for Path B is mechanical.

## Files in This Skill Folder

- `SKILL.md` (this file)
- `lib/gate_apply.py` (the apply-mode logic)
- `lib/gate_remove.py` (the remove-mode logic)
- `lib/html_patcher.py` (HTML manipulation utilities)
- `templates/gating.js.template` (the JS template with placeholder tokens)
- `templates/gating.css.template` (the CSS, no placeholders needed)

## Changelog

### 1.0 (2026-05-04)
- Initial version
- Pattern A gating (lessons viewed AND KC passed)
- Hard gate: blocks direct URL navigation on unit and final pages
- Visual lock state on index page
- Idempotent apply, clean remove
- Path A standalone, hook documented for future Path B generator merge
