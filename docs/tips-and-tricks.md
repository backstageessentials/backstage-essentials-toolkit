# Tips and Tricks

Painful lessons captured so future you, or anyone else using this toolkit, does not relearn them. Each section names the symptom first, then the cause, then the fix.

## Git clone says "Repository not found" but the repo definitely exists

**Symptom:** You run `git clone https://github.com/youraccount/your-private-repo.git` and get back `fatal: Repository not found`. You can see the repo in your browser. You are signed in. The URL is correct.

**Cause:** The repo is private, and git is not authenticating. GitHub will not confirm a private repo exists to anonymous callers, so it returns the same error as if the repo did not exist at all. Misleading but on purpose.

**Fix:** Embed your username in the URL so git is forced to authenticate before reading.

```
git clone https://YOUR-USERNAME@github.com/YOUR-USERNAME/your-private-repo.git
```

Git will prompt for a password. Paste your Personal Access Token (not your real password). After the first successful clone, git stores the token and stops asking.

## Pasting a token at the password prompt does nothing visible

**Symptom:** Git asks `Password for 'https://...':` and you paste your token. The screen looks frozen. No characters appear. You think the paste failed.

**Cause:** Terminals hide password input on purpose so people looking over your shoulder cannot see your password. The paste worked. The cursor just does not move.

**Fix:** Trust the paste. Press Enter exactly once after pasting. Do not press Enter multiple times. Do not type anything else.

**Also:** Use `Ctrl + Shift + V` to paste in Linux terminals. Regular `Ctrl + V` does not work. Right-click the terminal and choose Paste also works.

## "credential value for password contains carriage return"

**Symptom:** You paste your token and git rejects it with this error.

**Cause:** When you copied the token, an invisible newline character came along with it. Git is being cautious and refusing to use a token that has a newline mid-string.

**Fix:** Re-highlight just the token text in 1Password (or wherever you stored it), right click, Copy. That usually strips the newline. If that does not work, copy the token into a plain text note first, manually verify there is no trailing character, then copy from the note.

## Token rejected after rotating it

**Symptom:** You revoked your old token and generated a new one. Git pull or push fails with "Invalid username or token."

**Cause:** Git cached the old token and is still using it.

**Fix:** Wipe the cached credentials and try again.

```
rm -f ~/.git-credentials
git pull
```

Git will prompt for the password fresh. Paste the new token.

## ALL CAPS placeholders pasted as-is

**Symptom:** A command in this doc shows `YOUR-USERNAME` or `YOUR-API-KEY`. You paste it into the terminal exactly as written. Nothing works.

**Cause:** The all caps text is a placeholder, not a literal value. Git is literally trying to use the string "YOUR-USERNAME" as a username.

**Fix:** Always replace all caps placeholders with your real values before running. If a doc shows `YOUR-USERNAME`, swap in your actual GitHub username.

## Settings tab missing on a repo

**Symptom:** You open a repo on GitHub. The row of tabs shows Code, Issues, Pull requests, Actions, Projects, Security, Insights. No Settings. You cannot delete the repo or change its settings.

**Cause:** You are signed in as a collaborator, not the owner. Only the owner sees Settings. This commonly happens when you have multiple GitHub accounts and the wrong one is signed in.

**Fix:** Click your profile picture top right, see who you are signed in as, sign out, sign back in as the repo owner.

## Multiple GitHub accounts is a recipe for confusion

**Symptom:** Things do not work as expected. Files end up in the wrong repo. Tokens authenticate as the wrong identity. You cannot find Settings on your own repo.

**Cause:** You have two or more GitHub accounts and tools are picking up the wrong one.

**Fix:** Pick one account as your active account for any given project. Always verify which account a browser tab is signed in as by clicking the profile picture. When using git on the command line, embed the username in the URL (`https://username@github.com/...`) to make it explicit which identity is being used.

## Pushed to the wrong repo

**Symptom:** Claude Code or git pushed a commit to a different repo than you expected.

**Cause:** Either the wrong repo was open in the working directory, or the git remote was pointing at a different URL than you thought.

**Fix:**

```
cd ~/Code/your-actual-repo
pwd
git remote -v
```

The first line moves you to the right place. The second confirms you are there. The third shows you what URL git is actually pointing at. If the remote is wrong, fix it:

```
git remote set-url origin https://YOUR-USERNAME@github.com/YOUR-USERNAME/your-actual-repo.git
```

To recover from a wrong push, you can revert the bad commit:

```
git revert COMMIT_HASH
git push
```

Revert preserves history showing the mistake and the fix. Cleaner than trying to delete the bad commit.

## Claude Code memory drifts when projects have similar names

**Symptom:** Claude Code does the right thing in the wrong repo, or refers to a deleted project as if it still exists.

**Cause:** Claude Code memory is fuzzy. If two projects have similar names or were both worked on recently, Claude Code may conflate them.

**Fix:** Be explicit in prompts about which repo a task belongs to. After completing major work, tell Claude Code to update its memory with a clear summary: "Project X is the active course repo. Project Y was deleted. The Routledge book is a Word manuscript, not a code project." Verify by asking Claude Code what it remembers about each project.

## bes command not found after install

**Symptom:** You ran `pip install -e .` from the toolkit folder. Now you type `bes` and get "command not found."

**Cause:** Either the install failed silently, or your shell is using a cached path that does not yet include the bes binary.

**Fix:** Open a new terminal tab. The new shell will pick up the new command. If still not working, run `pip show backstage-essentials-toolkit` to verify the install succeeded. If it did, check that `~/.local/bin` is in your PATH (`echo $PATH`). If not, add it:

```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## bes sync fails with "no platform configured"

**Symptom:** You run `bes sync` and get an error about no platform.

**Cause:** Your `course-config.yaml` is missing the platform field, or has an unknown value.

**Fix:** Open `course-config.yaml`. Add or correct the platform field. Valid values: `thinkific`, `canvas`, `google-classroom`, `static-web`, `pdf`. Example:

```yaml
course:
  name: "Your Course Name"
  platform: thinkific
  ...
```

## Crostini files invisible in ChromeOS Files app

**Symptom:** You created a folder in your Crostini terminal. The ChromeOS Files app does not show it.

**Cause:** Crostini files live in a separate Linux container filesystem. They show up in the Files app under "Linux files," not under "My files."

**Fix:** Open the Files app. On the left sidebar, look for "Linux files." Click that. Your Crostini home directory contents are there. Pin it to the sidebar for easier access.

## Backing up Crostini

**Symptom:** Your Chromebook gets reset or you switch machines. Everything in Crostini is gone.

**Cause:** Crostini is a separate Linux container. It is not synced to your Google account. If the container goes, the contents go with it.

**Fix:** Periodically back up the entire Crostini container.

1. Open ChromeOS Settings
2. Search for "Linux"
3. Click Developers → Linux development environment
4. Find "Backup and restore"
5. Back up to Google Drive or to Downloads

Restoring on a new machine takes one click and brings everything back: installed packages, git config, Claude Code, your repos, all of it.

## Adding more tips here

When you hit a new gotcha and figure out the fix, add it to this doc. Pattern: Symptom, Cause, Fix. Three short paragraphs. The next person hitting the same wall (often you, three months later) will thank you.
