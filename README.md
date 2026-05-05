# Backstage Essentials Toolkit

A reusable, subject-neutral toolkit for building courses from plain text source files. Drives Claude Code to draft lessons, quizzes, diagrams, microsims, and a final assessment in your course's voice, then exports to Thinkific, Canvas, Google Classroom, static web, or PDF.

Designed for instructional designers and teachers who can use a terminal but should not have to learn pip, virtualenvs, or git plumbing to ship a course.

---

## Quick install

**macOS or Linux** (one line, paste into Terminal):

```bash
curl -fsSL https://raw.githubusercontent.com/backstageessentials/backstage-essentials-toolkit/main/install.sh | bash
```

**Windows** (PowerShell, one line):

```powershell
irm https://raw.githubusercontent.com/backstageessentials/backstage-essentials-toolkit/main/install.ps1 | iex
```

The script installs the toolkit to `~/Code/backstage-essentials-toolkit` (or `%USERPROFILE%\Code\` on Windows), checks every prerequisite, and tells you the exact next command to type. It is idempotent: running it again on a configured machine pulls the latest and re-verifies.

If you would rather not pipe a script from the internet, the same scripts are committed in this repo. Clone first, then run `bash install.sh` or `.\install.ps1` locally.

---

## Prerequisites

The installer checks for these and tells you what to fix if any are missing.

| Tool | Why | Get it |
|------|-----|--------|
| **Python 3.10 or newer** | The `bes` CLI is a Python package. | macOS: `brew install python@3.12` or [python.org](https://www.python.org/downloads/macos/). Windows: [python.org](https://www.python.org/downloads/windows/), check "Add Python to PATH" during install. Linux: `sudo apt install python3 python3-pip python3-venv`. |
| **git** | Clones the toolkit and your course repos. | macOS: `xcode-select --install` or `brew install git`. Windows: [Git for Windows](https://git-scm.com/download/win). Linux: `sudo apt install git`. |
| **Node.js / npm** | Renders Mermaid diagrams via `mmdc`. | [nodejs.org](https://nodejs.org/) (LTS is fine). |
| **Claude Code** | The toolkit drives Claude Code to author content. | `npm install -g @anthropic-ai/claude-code`, or [Anthropic's docs](https://docs.anthropic.com/en/docs/claude-code). |

Optional: install `pango`, `cairo`, `libffi`, `gdk-pixbuf` (macOS: `brew install pango cairo libffi gdk-pixbuf`; Linux: `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`) if you want WeasyPrint to handle PDF export with full CSS support. Without them, PDF export falls back to headless Chrome, which works but cannot resolve table-of-contents page numbers.

---

## macOS install steps

1. **Open Terminal.** Cmd+Space, type `Terminal`, hit Enter.
2. **Paste the one-liner** from Quick install above and press Enter.
3. **Watch the output.** The script prints six steps. Each step ends in `OK` (green) or `error` (red). On error, it tells you exactly what to install and stops.
4. **First-time prompts.** If `xcode-select --install` opens a dialog asking to install Command Line Tools, click Install and re-run the script when it finishes.
5. **Done.** The script ends with the literal first command to type. Follow it.

If you have never used Homebrew and the script asks for it, install Homebrew once from [brew.sh](https://brew.sh/), then re-run the toolkit installer.

---

## Windows install steps

1. **Open PowerShell.** Press the Windows key, type `PowerShell`, hit Enter. (Regular PowerShell is fine; you do not need "Run as Administrator".)
2. **Paste the one-liner** from Quick install above and press Enter.
3. **If PowerShell refuses to run the script** because of execution policy, run this once and try again:
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```
   Or run the installer in bypass mode for a single shot:
   ```powershell
   powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/backstageessentials/backstage-essentials-toolkit/main/install.ps1 | iex"
   ```
4. **Watch the output.** Same six-step pattern as macOS. Each step ends in `OK` or `error`.
5. **Done.** The script ends with the first command to type next.

If Windows Defender flags the script, it is a false positive (the script is plain PowerShell, unsigned because it is open source). Allow it and continue.

---

## Linux install steps

```bash
curl -fsSL https://raw.githubusercontent.com/backstageessentials/backstage-essentials-toolkit/main/install.sh | bash
```

Same six-step output as macOS. On Debian or Ubuntu you will likely need `python3-venv` and `python3-pip` system packages first:

```bash
sudo apt install python3 python3-pip python3-venv git curl nodejs npm
```

---

## Verify the install

In a fresh terminal window:

```bash
bes --version
```

You should see something like `bes, version 0.1.0`. If the shell says "command not found", close and reopen the terminal. If it still cannot find `bes`, see Troubleshooting.

---

## First course: five steps to a rendered preview

This walks you from a blank `~/Code` to a real lesson rendered in HTML. It assumes the install above succeeded.

**1. Create a new course.**

```bash
cd ~/Code
bes new-course
```

`bes` will prompt for a course name, target platform (`thinkific`, `canvas`, `google-classroom`, `static-web`, or `pdf`), target audience, and slug. It scaffolds a sibling folder under `~/Code` with the course skeleton.

**2. Open the new course in Claude Code.**

```bash
cd ~/Code/<your-course-slug>
claude
```

Claude Code reads the course's `CLAUDE.md` and the build spec automatically.

**3. Draft the first lesson.** Inside Claude Code, type:

```
draft Unit 1 lesson 1
```

Claude Code runs `bes new-lesson` under the hood, captures the structured prompt, reads the lesson-drafter skill, and writes the lesson markdown file into `content/unit-01/lessons/`.

**4. Render a preview.** From the same course folder, in your terminal:

```bash
bes preview
```

This produces an HTML preview at `preview/course-preview.html`.

**5. Open the preview.**

```bash
open preview/course-preview.html      # macOS
xdg-open preview/course-preview.html  # Linux
start preview\course-preview.html     # Windows
```

That is the loop. Draft, preview, edit, preview again. Run `bes commit` and `bes push` when you are happy.

---

## What the toolkit can do

Run `bes --help` for the full list. The most-used commands:

| Command | What it does |
|---------|-------------|
| `bes new-course` | Scaffold a new course folder with build spec, configs, and a course-level `CLAUDE.md`. |
| `bes new-lesson` | Draft a single lesson via the lesson-drafter skill. |
| `bes new-quiz` | Generate a unit's knowledge-check questions. |
| `bes add-diagrams` | Add Mermaid diagrams to existing lessons where they earn their place. |
| `bes add-microsim` | Add an interactive HTML widget to a lesson by customizing one of seven starter templates. |
| `bes build-final` | Generate the course final assessment question bank (typically 200 questions, 100 sampled per attempt). |
| `bes build-course` | Build a course end to end: every lesson, every unit's knowledge check, the final. |
| `bes preview` | Render an HTML preview of the entire course locally. |
| `bes export-pdf` | Generate a PDF version of the course (works regardless of the course's primary platform). |
| `bes sync` | Push content to the platform configured in `course-config.yaml`. |
| `bes validate` | Lint the course for missing fields, broken refs, draft flags. |
| `bes commit` / `bes push` | Stage, commit, push the course repo. |

Skills the toolkit ships with: course-spec-builder, repo-bootstrap, lesson-drafter, quiz-builder, final-assessment-builder, diagram-builder, microsim-builder, course-validator. Each is self-contained in `skills/` and reads voice context from the course it is run in, so the same skill produces different output for a high-school history course vs. an adult trade course.

---

## Troubleshooting

**`bes: command not found` after a successful install.**
Close and reopen your terminal so the new PATH takes effect. If still missing on macOS or Linux, the installer used `--user` mode; add this to `~/.zshrc` or `~/.bashrc`:
```bash
export PATH="$(python3 -m site --user-base)/bin:$PATH"
```
On Windows, add `%APPDATA%\Python\Python312\Scripts` (or whichever Python version) to your user PATH via System Properties > Environment Variables.

**`error: externally-managed-environment` during pip install.**
This is PEP 668 on newer macOS Python and most modern Linux distros. The install script handles it automatically by retrying with `--user`. If you ran `pip install` manually and hit this, use `python3 -m pip install --user -e .` instead.

**PowerShell says "running scripts is disabled".**
Run this once:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Or run the installer one-shot with `-ExecutionPolicy Bypass`. The README's Windows section has the exact command.

**PDF export TOC page numbers are blank.**
WeasyPrint's system libraries are missing, so the renderer fell back to headless Chrome, which cannot resolve CSS `target-counter()`. Install the libs:
```bash
brew install pango cairo libffi gdk-pixbuf      # macOS
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi-dev   # Debian/Ubuntu
```
Re-run `bes export-pdf`. It should report `Renderer: weasyprint` and the TOC numbers will populate.

**`Claude Code (the 'claude' CLI) is not installed`.**
The toolkit cannot author content without Claude Code. Install it:
```bash
npm install -g @anthropic-ai/claude-code
```
If npm errors with EACCES, either follow [npm's permissions guide](https://docs.npmjs.com/resolving-eacces-permissions-errors-when-installing-packages-globally) or use a Node version manager like `nvm` so npm installs into your home directory.

---

## License and contributing

Released under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE) (CC BY-NC-SA 4.0).

This is a tool I (Bill Larsen, Backstage Essentials LLC) wrote for my own course work and decided to share. Bug reports and pull requests are welcome via GitHub Issues. I read everything; I do not promise to merge everything.

The reference implementation course is [`live-event-technician-test-course`](https://github.com/backstageessentials/live-event-technician-test-course) (sibling repo). Look there to see what a finished toolkit-built course looks like.
