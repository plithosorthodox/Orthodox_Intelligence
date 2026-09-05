# Running Uvaha on Windows

Written for an ASUS Vivobook with a Ryzen AI 7 and Radeon integrated
graphics, on Windows 11. It assumes no prior setup and nothing installed.

Two programs run side by side. **Sofiia** is the model, served locally.
**Uvaha** is the application that retrieves evidence, asks Sofiia, verifies
the answer, and shows it. Neither sends anything over the network once
installed.

Nothing here has been executed on Windows. It was worked out on Linux and
written down carefully; if a step does not match what you see, that is worth
reporting rather than working around.

## What this machine can do

The Radeon graphics are integrated, sharing system memory rather than having
their own. That is fine for a 7B model at Q4_K_M, which needs about 5 GB, and
it will be far faster than a processor alone. The NPU that makes this a
Copilot+ PC is not used: llama.cpp cannot reach it, and neither can we.

Check available memory first. Open Task Manager, Performance, Memory. **16 GB
is enough. 8 GB is not** - use the 1B model named at the end instead.

## 1. Install the model server

Download **LM Studio** from `lmstudio.ai` and install it. It is a normal
Windows program and it detects AMD graphics on its own.

**Search happens inside the program, not on the website.** The model list on
`lmstudio.ai/models` is a catalogue to browse; the search box is in the app,
under the magnifying glass or **Discover** in the left sidebar.

In LM Studio:

1. Search for **Olmo 3** and choose the **7B Instruct** model.
2. Download the **Q4_K_M** build, about 4.5 GB.
3. Open the **Developer** tab (or **Local Server**) and press **Start Server**.
4. Note the address it shows, usually `http://127.0.0.1:1234`.

**Why Olmo 3 rather than the OLMo 2 named in the manifest.** They are the same
family from the same laboratory under the same Apache-2.0 licence, and
llama.cpp supports both. Olmo 3 is a year newer and far more widely used, and
the one thing Uvaha needs that OLMo 2 was measurably bad at is holding a fixed
output shape - which is exactly what a newer instruction-tuned model tends to
do better.

This does not overturn `OI-012`. That decision names OLMo 2 7B as **S0**, the
reference substrate, because it is the model the forced-choice experiment
actually tested, and it should stay S0 until something is tested against it.
Which model the application ships with is a separate question from which model
the research measures. If Olmo 3 proves better here, that is a reason to run
the comparison, not a reason to skip it.

Two settings matter, and both are on the model's load screen:

- **Context length: 4096.** OLMo 2 was trained at 4,096 tokens. Asking for
  more does not give you more; it degrades the answers.
- **GPU offload: as high as it will go.** This is what uses the Radeon
  graphics. If the model fails to load, lower it and try again.

## 2. Install Python

Open the Microsoft Store, search **Python**, install **3.12 or newer**. 3.13
is fine. Nothing else is needed: Uvaha uses no third-party packages at all, so
there is nothing to `pip install` and nothing to go stale.

## 3. Get Uvaha and the corpus

**Both repositories are private, so this needs you signed in to GitHub.**
A plain `git clone` will fail or ask for a password that no longer works;
GitHub stopped accepting account passwords for git in 2021. There are two ways
round it, and the first is easier than it sounds.

### The easy way: let Git ask

Install **Git for Windows** from `git-scm.com`, taking the defaults. It
includes Git Credential Manager, which opens a browser window the first time
you clone something private and lets you sign in to GitHub normally. You
authorise once and it remembers.

Then open **PowerShell** (press Start, type PowerShell) and run these one at a
time:

```powershell
cd $HOME
git clone https://github.com/plithosorthodox/Orthodox_Intelligence.git
git clone https://github.com/plithosorthodox/plithos_corpus.git
cd Orthodox_Intelligence
python tools\install_plithos_corpus.py --corpus-repo ..\plithos_corpus
```

A browser window appearing on the first `git clone` is the expected
behaviour, not an error.

### The way with no git at all

If that goes wrong, you can download both by hand. Signed in to GitHub in your
browser, open each repository, press the green **Code** button, choose
**Download ZIP**, and unpack both into your user folder (the one PowerShell
means by `$HOME`) so that they sit side by side, one named
`Orthodox_Intelligence` and the other `plithos_corpus`.

GitHub names the unpacked folders `Orthodox_Intelligence-main` and
`plithos_corpus-main`. **Rename them to drop the `-main`**, or the paths in
the commands below will not match.

One thing this costs you: the corpus installer verifies the corpus against the
exact upstream commit it was built from, and a ZIP carries no git history for
it to read. If it objects, that is why, and the clone route avoids it.

Either way, finish with:

```powershell
cd $HOME\Orthodox_Intelligence
python tools\install_plithos_corpus.py --corpus-repo ..\plithos_corpus
```

That verifies the corpus against its published hashes before installing it,
and prints what it installed. It should say roughly 1,873 entities and 36,585
texts. **If the hashes do not match it stops rather than installing** - that
check is the point of the whole exercise, so an objection there is worth
reporting, not working around.

## 4. Start Uvaha

With LM Studio's server still running:

```powershell
python tools\serve_prototype.py --model-endpoint http://127.0.0.1:1234
```

Open `http://127.0.0.1:8765` in a browser.

If you leave off `--model-endpoint`, Uvaha still runs. It becomes the evidence
navigator: it searches the corpus and shows you the sources, and says so
plainly instead of pretending a model is loaded.

## What you should see, and what it means

Ask **"Who was Saint Nicholas?"** and you should get evidence from the corpus
with a citation under each passage.

Ask **"Are you an Orthodox priest?"** and it must refuse. That refusal is
deterministic and does not involve the model at all.

Ask **"Quote John 3:16 exactly"** and it should reproduce the verse from the
installed edition rather than from the model's memory.

**Sometimes it will decline to answer.** That is the design working. Uvaha
checks that every citation names a passage that was actually retrieved and
that every quotation appears in its source; when a draft fails that twice, it
returns nothing rather than show you something it cannot stand behind.

## If it is slow, or fails

**Very slow.** GPU offload is probably not on. Check it in LM Studio, and
watch Task Manager's GPU graph while it answers - it should move.

**The model will not load.** Not enough memory. Lower GPU offload, or search
LM Studio for a **1B** model instead, which needs about 1.5 GB. It is
much faster and noticeably less able; measured on a processor alone it
answered in 34 seconds against the 7B's 1,168, and it sometimes produces
answers that satisfy every structural check while saying nothing.

**Answers get cut off mid-sentence.** The token budget ran out before the
model finished. This is the one failure that looks like a fault in the model
and is not.

**A port is already in use.** Something else has 8765 or 1234. Close it, or
change the port in the command.
