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

1. Search for **OLMo 2 1124 7B Instruct** and take the **allenai** one, from
   the laboratory that trained it rather than a re-upload.
2. Download the **Q4_K_M** build, about 4.3 GB. It should say
   **Full GPU Offload Possible**.
3. Open the **Developer** tab (or **Local Server**) and press **Start Server**.
4. Note the address it shows, usually `http://127.0.0.1:1234`.

**Olmo 3 does not load in LM Studio, and this was established the hard way.**
It is the obvious choice on paper: same laboratory, same Apache-2.0 licence, a
year newer, far more used, and upstream llama.cpp registers
`Olmo3ForCausalLM`. It fails anyway. Every attempt ends the same:

    Engine protocol runtime llama-server ... exited before becoming healthy.
    exitCode=1, signal=null

That is not a settings problem and no amount of tuning moves it. It happened
with automatic optimisation on and off, at 4096 and 8192 context, with Flash
Attention on and off, and with the GPU both undetected and detected. An engine
that exits *before becoming healthy* never loaded the file.

The likely cause is that Olmo 3 uses sliding-window attention on all layers
except every fourth, which is a structural change from OLMo 2, and LM Studio
bundles its own copy of llama.cpp that lags upstream. **If a later LM Studio
adds it, Olmo 3 is worth revisiting** - it holds 65,536 tokens of context
against OLMo 2's 4,096, which would remove the evidence-truncation problem
entirely.

Until then use OLMo 2, which is also what `OI-012` names as **S0**, the
reference substrate, because it is the model the forced-choice experiment
actually tested.

Two settings matter, and both are on the model's load screen:

- **Context length: 4096.** OLMo 2 was trained at 4,096 tokens. Asking for
  more does not give you more; it degrades the answers. (Olmo 3 holds 65,536,
  so this number is per-model rather than a fixed rule.)
- **GPU offload: start at 0 on the tested Windows laptop.** OLMo 2 loaded and
  produced an answer at 0 after failing with GPU layers offloaded. That proves
  the model file and CPU path are sound and points to the graphics runtime or
  offload path. Once CPU generation works, raise the setting a few layers at a
  time only if you want to find a stable acceleration level.

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

Then open a terminal and run these one at a time. **Git for Windows installs
Git Bash, and that is the window it opens for you** - it works, and so does
PowerShell. Every command here uses forward slashes, which both understand.
Do not convert them to backslashes: in Git Bash a backslash is an escape
character, so `tools\install_plithos_corpus.py` silently becomes
`toolsinstall_plithos_corpus.py` and the file is reported missing.

```powershell
cd $HOME
git clone https://github.com/plithosorthodox/Orthodox_Intelligence.git
git clone https://github.com/plithosorthodox/plithos_corpus.git
cd Orthodox_Intelligence
python tools/install_plithos_corpus.py --corpus-repo ../plithos_corpus
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
cd $HOME/Orthodox_Intelligence
python tools/install_plithos_corpus.py --corpus-repo ../plithos_corpus
```

That verifies the corpus against its published hashes before installing it,
and prints what it installed. It should say 1,900 entities and 44,542
texts. **If the hashes do not match it stops rather than installing** - that
check is the point of the whole exercise, so an objection there is worth
reporting, not working around.

## 4. Start Uvaha

With LM Studio's server still running:

```powershell
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:1234
```

Uvaha normally waits up to 120 seconds for one local completion. If the 7B
model is running on the processor and reaches that limit, restart Uvaha with
`--model-timeout-seconds 1500`. That allows up to 25 minutes for each attempt;
it does not make generation faster.

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

**LM Studio reports 0 GPUs.** The Vulkan runtime is not installed. Open
**Runtime** in the left sidebar and install it; the Radeon is invisible to LM
Studio until then, and everything runs on the processor.

**Very slow.** GPU offload 0 is the known-working baseline on the tested
laptop, but it runs on the processor. Only raise offload after the model has
answered successfully at 0; watch Task Manager's GPU graph while testing.

**The model will not load.** Set GPU offload to 0 first. If it then loads, the
model file is sound and the graphics/offload path is the fault. If it still
fails, memory or the model artifact may be the problem; a **1B** model needs
about 1.5 GB. It is
much faster and noticeably less able; measured on a processor alone it
answered in 34 seconds against the 7B's 1,168, and it sometimes produces
answers that satisfy every structural check while saying nothing.

**Answers get cut off mid-sentence.** The token budget ran out before the
model finished. This is the one failure that looks like a fault in the model
and is not.

**"No such file or directory" with two path parts run together**, such as
`toolsinstall_plithos_corpus.py`. A backslash was used in Git Bash, where it
escapes the next character instead of separating folders. Use forward slashes.

**A port is already in use.** Something else has 8765 or 1234. Close it, or
change the port in the command.
