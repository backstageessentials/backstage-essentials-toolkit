# Backstage Essentials Course — Build Spec, Plain English Edition (Chromebook, v3)

Bill Larsen, Backstage Essentials LLC | May 2026

## 0. What This Whole Thing Is, In Plain English

You write your course on your Chromebook in regular files. Lessons go in markdown files. Quiz questions go in YAML files. A small script (we will write it) reads those files and ships them to Thinkific automatically. GitHub keeps a backup of every version of every file, so if you ever need to undo a change you can.

Claude Code is the AI helper you talk to from your Linux terminal. It writes the files for you when you tell it what to do. You review, fix, and approve.

The course is Backstage Essentials. It is a self paced training course for live event production. People who finish the course earn a certificate of completion. This is not a third party certification. There is no certifying body, no accreditation, no Certified Whatever Technician credential. Just a clear, honest course completion certificate.

The Word doc you are reading is the instruction sheet you hand to Claude Code in June so it knows what to build.

## 1. Vocabulary You Will See

- **Repo**: short for repository. One project on GitHub. Like a folder that lives both on your Chromebook and on GitHub at the same time.
- **Commit**: save a snapshot. Like Ctrl plus S, but git remembers every snapshot forever and lets you go back.
- **Push**: send your saved snapshots from your Chromebook up to GitHub.
- **Pull**: grab the latest version from GitHub down to your Chromebook.
- **Clone**: copy a GitHub repo down to your Chromebook for the first time.
- **Crostini**: the Linux environment built into ChromeOS. The Terminal app on your Chromebook is Crostini. Claude Code runs inside it.
- **PAT**: Personal Access Token. The password GitHub gives you so git on your Chromebook can push and pull without typing your real password every time.
- **API key**: a long secret password that lets your sync script log in to Thinkific automatically.
- **.env file**: a hidden file that holds your API key. It never gets committed to GitHub. Stays on your Chromebook only.
- **YAML**: a simple file format for structured data. Looks like an indented list. Easier to read than JSON.
- **Markdown**: a simple way to write formatted text using plain characters. Pound sign for headings, asterisks for bold.

## 2. The Big Picture, Step by Step

1. Use your existing GitHub account.
2. Connect git on your Chromebook to that account (one time setup).
3. Create an empty private repo on GitHub. Name it `backstage-essentials-course`.
4. Clone the repo down to your Chromebook from the Linux terminal.
5. Open Claude Code in that folder. Hand it this Word doc.
6. Tell Claude Code to build the folder structure and the sync script. It writes the files. You review.
7. Claude Code can run the git commit and push commands for you. Now your work is backed up on GitHub.
8. In June when Thinkific is live and you have the API key, run the sync script. Course goes up.

That is the whole flow. The rest of this doc is detail.

## 3. Setting Up GitHub From Your Chromebook

Your GitHub account already exists. The work below is teaching git on the Chromebook how to talk to it.

### 3.1 Tell Git Who You Are

Open the Terminal app on your Chromebook. This drops you into Crostini. Type these two commands, swapping in your real name and the email tied to your GitHub account.

```
git config --global user.name "Bill Larsen"
git config --global user.email "bill@backstageessentials.com"
```

This is one time. Git remembers it forever on this Chromebook.

### 3.2 Connect to GitHub Using a Personal Access Token

HTTPS with a Personal Access Token is the simplest path on Crostini. SSH keys also work fine if you prefer them, but PAT is fewer steps.

1. In a browser, sign in to GitHub. Click your profile picture in the top right, then **Settings**.
2. On the left, scroll down and click **Developer settings**.
3. Click **Personal access tokens**, then **Tokens (classic)**, then **Generate new token (classic)**.
4. **Note**: type "Chromebook Crostini" so future you knows what this token is for.
5. **Expiration**: 90 days is fine. You can regenerate when it expires.
6. **Scopes**: check the box for `repo`. That is all you need for private repo push and pull.
7. Click **Generate token**. Copy the token. You will only see it once. Paste it somewhere safe (1Password) for now.

Next, tell git on your Chromebook to remember the token so you do not have to paste it on every push.

```
git config --global credential.helper store
```

First time you push, git will ask for your username and password. Username is your GitHub username. Password is the token you just copied. After that, git stores it and stops asking.

### 3.3 Create the Repo on GitHub

1. In a browser, go to github.com and sign in.
2. Click the green **New** button on the left side of the home page. Or click the plus sign in the top right and choose **New repository**.
3. **Repository name**: `backstage-essentials-course`
4. **Description**: `Backstage Essentials course content and Thinkific sync`
5. **Privacy**: choose **Private**. Always private for this project. Course content is your IP.
6. Check the box for **Add a README file**.
7. Skip the .gitignore and license dropdowns for now. We add those later.
8. Click **Create repository**.

You now have an empty repo on GitHub with one file in it (the README).

### 3.4 Clone the Repo to Your Chromebook

Back in the Terminal app on your Chromebook, decide where you want repos to live. A `Code` folder in your home directory works.

```
mkdir -p ~/Code
cd ~/Code
```

Now clone the repo. Replace the username in the URL with your actual GitHub username before running.

```
git clone https://github.com/YOUR-USERNAME/backstage-essentials-course.git
cd backstage-essentials-course
```

**Important**: anywhere this doc shows `YOUR-USERNAME` or `YOUR-API-KEY` in all caps, you must swap in the real value. Do not paste the all caps placeholder as is. Git will fail with a confusing "repository not found" error.

**Private repo gotcha**: if your repo is private, git will not even prompt for credentials when given a bare URL. It will fail with "repository not found" because GitHub will not confirm a private repo exists to anonymous callers. To force git to ask for the password, embed your username in the URL like this: `https://YOUR-USERNAME@github.com/YOUR-USERNAME/backstage-essentials-course.git`

There is now a folder on your Chromebook named `backstage-essentials-course` inside `~/Code`. Anything you save in there can be pushed to GitHub.

To see this folder in the ChromeOS Files app, right click the Linux files section and pin it, or just navigate to Linux files then Code then `backstage-essentials-course`.

### 3.5 Pasting Tokens at Password Prompts

When git asks for a password, it wants the token, not a real password. GitHub stopped accepting real passwords years ago.

1. Copy the token from 1Password. Make sure you only grab the `ghp_` string itself, not any prefix or label.
2. Click into the terminal.
3. Paste with Ctrl plus Shift plus V. Regular Ctrl plus V does not work in Linux terminals.
4. The screen will look like nothing happened. The terminal hides password input on purpose. Trust the paste worked.
5. Press Enter once. Just one tap.

If you get an error like "credential value for password contains carriage return", the copy picked up an invisible newline character. Re highlight just the token text in 1Password, right click, Copy, and try again.

## 4. Building the Folder Structure (Claude Code Does It)

You do not need to create the folders by hand. That is what Claude Code is for.

1. In the Terminal app, make sure you are in the repo folder. If you put it in `~/Code`, type: `cd ~/Code/backstage-essentials-course`
2. Type: `claude`
3. Once Claude Code is running, paste this Word doc text in. Or save the doc as a `.md` file in the folder and tell Claude Code to read it.
4. Tell Claude Code: "Build the folder structure exactly as Section 6 of the spec describes. Create empty placeholder files. Do not write content yet."
5. Claude Code creates everything. Look at it in the Files app under Linux files to confirm the folders and files are there. Or run `ls` in the terminal.
6. Tell Claude Code: "Stage everything, commit with the message 'Initial folder structure', and push to origin main." Claude Code runs the git commands. You watch.

Done. The skeleton is up. The next phase is filling in the lesson and quiz files, which is the main work of June through October.

## 5. The Spec Itself (the technical part)

Everything below is what Claude Code uses to build the actual code. You do not need to memorize it. You only need to read enough to spot if something looks wrong when Claude Code reports back.

## 6. Repo Structure

This is the folder layout Claude Code will create.

```
backstage-essentials-course/
  README.md
  .env.example
  .gitignore
  requirements.txt
  course-config.yaml
  content/
    unit-01-professional-foundation/
      unit.yaml
      lessons/
        01-introduction.md
        02-the-call.md
      knowledge-check.yaml
    unit-02-pre-production/
    unit-03-load-in/
    unit-04-systems-build/
    unit-05-show-day/
    unit-06-strike-and-wrap/
  exam/
    course-final.yaml
  scripts/
    sync.py
    validate.py
    helpers/
      thinkific_client.py
      content_parser.py
  .github/
    workflows/
      deploy.yml   (optional, auto sync on push)
```

What each folder is for, in plain English:

- `content/` holds the course material. One folder per unit. Inside each unit is a yaml file describing the unit, a `lessons` folder for the lesson markdown files, and a `knowledge-check` yaml for the unit quiz.
- `exam/` holds the course final assessment in one yaml file. 200 plus questions live here. This is the comprehensive end of course test, not a certification exam.
- `scripts/` holds the Python files that read your content and push it to Thinkific.
- `.github/` is optional. Holds GitHub Actions workflow files for auto deploy. You can ignore this until later.
- `course-config.yaml` sits at the top. Defines the overall course settings (name, price, completion threshold).
- `.env.example` is a template for the secret API key file. The real `.env` file you create later and never commit.
- `.gitignore` tells git which files to skip. Includes `.env`, `sync-state.json`, and other things you do not want on GitHub.

## 7. File Formats

### 7.1 course-config.yaml

```yaml
course:
  name: "Backstage Essentials"
  slug: "backstage-essentials"
  description: "Self paced live event production course."
  price_usd: 247
  completion_threshold: 0.75
  certificate: "course-completion"
  units: 6
```

### 7.2 unit.yaml (one per unit folder)

```yaml
unit:
  number: 1
  title: "The Professional Foundation"
  description: "Professionalism, safety, reputation."
  book_chapters: [1, 2]
  learning_outcomes:
    - "Demonstrate professional conduct on a real show floor."
    - "Identify and mitigate site safety hazards."
    - "Make go or no go safety decisions under pressure."
```

### 7.3 lesson markdown (one file per lesson)

```markdown
---
title: "The Call: What It Is and How to Take One"
order: 2
type: text
duration_minutes: 12
---

# The Call

Body content as markdown. Headings, lists, images, links.
Images live in the unit folder under images/ and reference
relatively.
```

### 7.4 knowledge-check.yaml (one per unit)

```yaml
quiz:
  title: "Unit 1 Knowledge Check"
  pass_threshold: 0.7
  questions:
    - id: u1-kc-01
      type: scenario
      question: |
        You arrive 10 minutes late to a 6 AM call.
        The crew chief is mid brief. What do you do?
      choices:
        - text: "Apologize and get to work without explanation."
          correct: true
        - text: "Explain that traffic was bad."
          correct: false
      explanation: |
        Crew chiefs want execution, not excuses.
```

### 7.5 course-final.yaml (the 200 plus question final assessment)

This is the comprehensive end of course test. Passing it is required to earn the course completion certificate. It is not a certification exam and confers no professional credential beyond proof you finished the course.

```yaml
final_assessment:
  name: "Backstage Essentials Course Final"
  total_questions_in_bank: 200
  questions_per_attempt: 100
  pass_threshold: 0.75
  randomize: true
  questions:
    - id: u1-q01
      unit: 1
      difficulty: medium
      type: scenario
      question: |
        You arrive at load in and see...
      choices:
        - text: "Option A"
          correct: false
        - text: "Option B"
          correct: true
      explanation: |
        Why B is right and A is wrong.
```

## 8. What the Sync Script Does

`scripts/sync.py` is the worker. When you run it, it does this:

1. Loads your secret API key from the `.env` file.
2. Reads `course-config.yaml`. Creates the course on Thinkific if it does not exist. Updates it if it does.
3. Walks the content folder one unit at a time. Creates the chapter, pushes each lesson, creates the unit quiz.
4. Reads the course final question bank. Creates or updates the final assessment quiz.
5. Logs a summary at the end. Tells you what got created, updated, or errored.

The script is idempotent. Fancy word for "safe to run a hundred times in a row." Each run just makes Thinkific match what is in your files. No duplicates.

`scripts/validate.py` runs first as a safety check. Catches typos, missing fields, duplicate IDs, questions with no correct answer marked. Run it before every sync.

## 9. Thinkific API Notes (for Claude Code)

- Base URL: `https://api.thinkific.com/api/public/v1/`
- Auth headers: `X-Auth-API-Key` and `X-Auth-Subdomain`
- Courses: `POST /courses`, `PUT /courses/{id}`
- Chapters: `POST /chapters`
- Lessons: `POST /contents` (type Lesson, body is HTML)
- Quizzes: `POST /quizzes`, then `POST /quiz_questions` one per question
- Rate limit: roughly 120 requests per minute. Use exponential backoff.

Pushing 200 questions hits rate limits fast. Build in chunked batching with a sleep between batches.

## 10. Daily Workflow Once Everything is Set Up

1. Open the Terminal app. Navigate to your repo folder: `cd ~/Code/backstage-essentials-course`
2. Pull anything new from GitHub: `git pull`
3. Type `claude` to start Claude Code.
4. Tell Claude Code what you want to write today. Example: "Draft Lesson 3 for Unit 1, on punctuality."
5. Claude Code drafts the file. You read it. Rewrite anything that does not sound like you.
6. Tell Claude Code to write 5 quiz questions on the same topic for the final assessment bank.
7. Tell Claude Code: "Show me the diff, then commit with a good message and push." It will run `git status`, `git diff`, `git add`, `git commit`, and `git push` for you. You watch and approve.
8. When you have a unit ready, run the sync script: `python3 scripts/sync.py`
9. Open Thinkific in your browser. Spot check the lesson rendered correctly.

## 11. Pilot First

1. Build the repo skeleton (section 6).
2. Have Claude Code write `sync.py` and `validate.py`.
3. Make a throwaway test course on Thinkific. Point the script at that first.
4. Build Unit 1 only. Push lessons. Push the unit quiz. Verify on Thinkific. Fix anything that broke.
5. Once the pipeline works end to end on Unit 1, scale to Units 2 through 6.

This avoids the worst case where you build 6 units of content and then discover the sync script has a bug that scrambles half of it.

## 12. Risk Notes

- **Markdown to HTML conversion**: use the `markdown-it-py` library. Test with one of your richest lessons (code blocks, lists, images) before scaling.
- **Image hosting**: lesson images need to be uploaded to Thinkific media first, then referenced. Or host on a CDN you control. Decide once and stick with it.
- **Quiz endpoint** can be slow when pushing 200 questions. Chunk it.
- **Portability**: if you ever leave Thinkific, your content is in clean files. Retarget with a new sync script.
- **Crostini specific**: the Linux container is a separate filesystem from the rest of ChromeOS. Files live in Linux files in the Files app. Back up the whole container occasionally using the ChromeOS Linux settings (Backup and restore).

## 13. Launch Instruction for Claude Code

In June 2026, paste this in Claude Code on day one of the build:

> Read the build spec doc in this folder. Build the repo structure exactly as Section 6 describes. Then write `scripts/sync.py` and `scripts/validate.py` per Sections 8 and 9. Test against a Thinkific test course before populating real content. Confirm round trip (file to API to review on Thinkific) works for one lesson and one quiz before we scale.

## 14. What to Have Ready Before June 2026

- GitHub account active under bill@backstageessentials.com (already done).
- Crostini (Linux) turned on in ChromeOS settings (already done).
- Git on Crostini configured with your name, email, and a Personal Access Token (Section 3 above).
- `backstage-essentials-course` repo created on GitHub (private).
- Repo cloned to `~/Code` on the Chromebook.
- Claude Code installed on Crostini and working (already done).
- Python 3.10 plus installed on Crostini. Check with: `python3 --version`
- Thinkific account active (Basic trial or paid).
- Thinkific API key generated. Stored in 1Password or wherever you keep secrets.

## 15. Change Notes from v2

This v3 of the spec removes all references to CLET (Certified Live Event Technician). Backstage Essentials is no longer pursuing third party certification body status. The course awards a certificate of completion only, with no professional credential implied.

Specific changes from v2:

- Course name: was "Live Event Technician", now "Backstage Essentials"
- Slug: was "live-event-technician", now "backstage-essentials"
- Certificate field: was "CLET", now "course-completion"
- Final exam file: was `exam/clet-exam-bank.yaml`, now `exam/course-final.yaml`
- Final exam name: was "CLET Certification Exam", now "Backstage Essentials Course Final"
- Pass threshold field renamed to `completion_threshold` for clarity
- All language reframed from certification to course completion

If Claude Code is updating an existing repo from v2 to v3, all of the above renames need to happen consistently across `course-config.yaml`, the exam folder, the build spec markdown stored in `docs`, and any reference notes in `docs/reference-screenshots`.

— Bill
