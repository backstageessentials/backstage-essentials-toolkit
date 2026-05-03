# Chromebook Prework

One-time setup steps for using this toolkit on a new Chromebook. Do these in order. Each step is a few minutes. The whole sequence takes about an hour, mostly waiting for installs to finish.

This is for ChromeOS specifically. A separate doc will cover Mac and Linux setup when those are needed.

## What you will have at the end

- Crostini (the Linux environment built into ChromeOS) turned on
- Git installed and configured with your name, email, and a Personal Access Token
- Python 3.10 or higher
- Claude Code installed and working
- The toolkit cloned and the bes command installed and working from any folder

## Step 1: Turn on Crostini

ChromeOS includes a Linux environment called Crostini that you can turn on. This is where everything else lives.

1. Open ChromeOS Settings (the gear icon in the system tray, or Settings from the launcher)
2. In the search bar at the top, type "Linux"
3. Click "Developers"
4. Click "Linux development environment"
5. Click "Set up" or "Turn on"
6. ChromeOS will ask how much disk space to give it. 10 GB is the default and is fine for course building. You can resize later.
7. Click Install. This takes 5 to 10 minutes.

When it finishes, the Terminal app appears in your launcher. Click it. You will see a Linux command prompt that looks something like:

```
bill@penguin:~$
```

That is Crostini. From here forward, "the terminal" means this Terminal app.

## Step 2: Update Crostini

Before installing anything new, update the existing software.

```
sudo apt update
sudo apt upgrade -y
```

This takes a couple minutes. You will see scrolling text. When the prompt comes back, you are ready for the next step.

## Step 3: Install Python and pip

Crostini comes with Python but the version may be old. Install Python 3.10 or higher.

```
sudo apt install -y python3 python3-pip python3-venv
```

Verify the version:

```
python3 --version
```

You want 3.10 or higher. If the version is older, install a newer one through deadsnakes (Google "deadsnakes Crostini" for current instructions, since this changes over time).

## Step 4: Install Git

Git is usually pre-installed on Crostini, but verify.

```
git --version
```

If you see a version number, you are good. If you see "command not found," install it:

```
sudo apt install -y git
```

## Step 5: Configure Git

Tell git who you are. Use the email tied to your GitHub account.

```
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

Tell git to remember credentials so you do not have to paste your token on every push.

```
git config --global credential.helper store
```

This is one-time per machine. Git remembers it forever.

## Step 6: Generate a Personal Access Token on GitHub

Git on the command line needs a Personal Access Token (PAT) to authenticate with GitHub. GitHub stopped accepting real passwords for git years ago.

In a browser, signed in to GitHub:

1. Click your profile picture in the top right
2. Click "Settings"
3. On the left sidebar, scroll all the way down and click "Developer settings"
4. Click "Personal access tokens"
5. Click "Tokens (classic)"
6. Click "Generate new token" then "Generate new token (classic)"
7. Note: type "Chromebook Crostini"
8. Expiration: 90 days is fine
9. Scopes: check the box for "repo" (the top group). That covers private repo access.
10. Click "Generate token" at the bottom
11. Copy the token. It starts with `ghp_` followed by a long string. You will only see it once. Save it in 1Password or similar.

Set a calendar reminder to regenerate the token before it expires. The bes command will fail with auth errors when the token expires, and the fix is just to generate a new one.

## Step 7: Install Claude Code

Claude Code is the AI helper that runs in the terminal and writes code for you. Install instructions change over time, so check the current docs at https://docs.claude.com when you do this.

As of this writing, the install is one command (check the latest docs first):

```
curl -fsSL https://claude.ai/install.sh | bash
```

Verify it works:

```
claude
```

You should see Claude Code start up. Press Ctrl+C to exit for now.

## Step 8: Clone the Toolkit

The toolkit lives in a private GitHub repo. Clone it down to your Chromebook.

```
mkdir -p ~/Code
cd ~/Code
git clone https://YOUR-USERNAME@github.com/backstageessentials/backstage-essentials-toolkit.git
```

Replace `YOUR-USERNAME` with your GitHub username.

When git prompts for the password, paste your Personal Access Token from Step 6. Use Ctrl + Shift + V to paste in the terminal. The screen will look like nothing happened (terminals hide password input), but the paste worked. Press Enter once.

If you get a "credential value contains carriage return" error, see the tips-and-tricks doc.

## Step 9: Install the bes Command

From inside the cloned toolkit folder, install the bes command.

```
cd ~/Code/backstage-essentials-toolkit
pip install -e .
```

The `-e` flag means "editable install." It tells pip to point at the toolkit folder rather than copy files to a system location. When you `git pull` updates to the toolkit later, bes picks them up automatically with no reinstall needed.

Verify bes works:

```
bes help
```

You should see the bes command list and short descriptions.

## Step 10: Add bes to Your PATH (if needed)

If `bes help` returned "command not found," your shell does not know where to find bes. Add the install location to your PATH.

```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Try `bes help` again. It should work now.

## Step 11: Test Everything Together

Final verification that all the pieces work.

```
cd ~/Code
mkdir test-course
cd test-course
bes new-course
```

If bes prompts you for course name and other details, the toolkit is working. Type Ctrl+C to cancel for now (we are just verifying, not creating a real course yet).

```
cd ~
rm -rf ~/Code/test-course
```

That cleans up the test folder.

You are done. The next time you sit down to work on a course, just open the terminal, navigate to a course folder (or create one with `bes new-course`), and start working.

## Backing Up Crostini

Worth doing once you have everything set up. Crostini is a separate Linux container that is not synced to your Google account. If the container gets corrupted, deleted, or your Chromebook gets reset, everything in Crostini goes with it.

1. ChromeOS Settings, search for "Linux"
2. Click Developers, then Linux development environment
3. Find "Backup and restore"
4. Back up to Google Drive

Restoring on a new machine takes one click and brings everything back: installed packages, git config, Claude Code, the toolkit, your repos, all of it.

## Common First-Day Issues

See `tips-and-tricks.md` in the docs folder for the full list. The most common first-day issues:

- Pasting tokens at password prompts looks frozen but is working. Press Enter once after pasting.
- "Repository not found" on a private repo means git is not authenticating. Use the username-embedded URL format.
- Carriage return errors when pasting tokens mean a hidden newline came along with the token. Re-copy it carefully.
- If bes is not found after install, open a new terminal tab.
