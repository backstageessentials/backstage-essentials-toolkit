# Screenshot shot list

This is the capture plan for the README's install steps and feature tour. Phase 13 deferred screenshots to a manual pass since automated capture would only show terminal text the README already documents.

Capture as PNGs at 2x resolution (Retina). Annotate with arrows or callouts using Skitch, Annotate, or macOS Preview. File names match the slugs below so the README can reference them by stable path.

## macOS install (5 frames)

| File | What to capture |
|------|-----------------|
| `macos-01-terminal-open.png` | Spotlight search showing "Terminal" highlighted, before pressing Enter. |
| `macos-02-paste-oneliner.png` | Terminal window with the `curl ... \| bash` one-liner pasted but not yet run. |
| `macos-03-prereqs-ok.png` | Step 2 output of install.sh showing all five `OK` lines (Python, git, curl, npm, Claude Code). |
| `macos-04-pip-install.png` | Step 5 output showing `pip install -e .` running, then `OK Installed editable package`. |
| `macos-05-done-success.png` | Final green "Done" message with the `cd ~/Code` and `bes new-course` next-step prompt. |

## Windows install (5 frames)

| File | What to capture |
|------|-----------------|
| `windows-01-powershell-open.png` | Start menu search showing "PowerShell" before launch. |
| `windows-02-execution-policy.png` | The `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` prompt with `Y` answered. |
| `windows-03-prereqs-ok.png` | Step 2 output showing all four `OK` lines on Windows. |
| `windows-04-pip-install.png` | Step 5 output during `pip install -e .`. |
| `windows-05-done-success.png` | Final "Done" message with the `cd $env:USERPROFILE\Code` next-step prompt. |

## Feature tour (3 frames, optional but high-impact)

| File | What to capture |
|------|-----------------|
| `feature-mermaid.png` | A rendered Mermaid diagram inside a lesson preview (the live event course's Unit 4 cabling diagrams are good source material). |
| `feature-microsim.png` | A MicroSim in action: the formula explorer or timeline scrubber from the live event course's static preview. |
| `feature-final-retest.png` | The final assessment in test mode showing the "Attempt 2 of 3" counter and the lockout panel after the third failed attempt. Use `?reset=true` between captures to walk through cleanly. |

## Hero / landing image

| File | What to capture |
|------|-----------------|
| `hero-demo.gif` (optional) | A 5–10 second screen recording of `bes new-course` → typing answers → folder appears → `claude` opens → first lesson drafted. Compress with `gifski` or similar. Keep under 4 MB so GitHub renders it inline. |

## Wiring screenshots into the README

Once captured, reference them in `README.md` like:

```markdown
1. **Open Terminal.** Cmd+Space, type `Terminal`, hit Enter.

   ![Terminal opened from Spotlight](docs/screenshots/macos-01-terminal-open.png)
```

Until images exist, the README's install sections work fine on text alone. Add image references in the same commit that adds the PNG files so we never ship broken-image badges.
