# Commands

Every command below runs in **Git Bash** on Windows. Forward slashes
throughout: in Git Bash a backslash escapes the next character rather than
separating folders, so `tools\serve_prototype.py` silently becomes
`toolsserve_prototype.py`.

## Start Uvaha with Sofiia

LM Studio must be running with its server started.

```bash
cd ~/Orthodox_Intelligence
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:1234
```

Then open <http://127.0.0.1:8765>. Change `1234` if LM Studio shows a
different port.

The default waits 120 seconds for each local completion. A CPU-bound 7B model
can take much longer; allow up to 25 minutes per attempt when needed:

```bash
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:1234 --model-timeout-seconds 1500
```

## Optionally enable Web sources

This requires a Brave Search API account and key. `read -s` accepts the key
without displaying it or placing it directly in the command history:

```bash
cd ~/Orthodox_Intelligence
read -s UVAHA_BRAVE_API_KEY
export UVAHA_BRAVE_API_KEY
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:1234 --model-timeout-seconds 1500 --web-search
```

In PowerShell, the equivalent keeps the key out of the visible prompt:

```powershell
$secureKey = Read-Host "Brave Search API key" -AsSecureString
$env:UVAHA_BRAVE_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:1234 --model-timeout-seconds 1500 --web-search
Remove-Item Env:UVAHA_BRAVE_API_KEY
```

Select **Automatic** in Uvaha to permit search when the local library does not
cover the question. The search terms then leave this computer for Brave Search;
the returned passages come back to the local process and the answer is still
generated locally. Brave controls account eligibility, terms, retention, and
pricing, so this optional mode may carry provider charges. The provider bundle
is not server-cached and is not added to Plithos, training data, or evaluation
data. Displayed source text and metadata can be saved in the browser's local
chat storage for local-corpus evidence. Web-origin source cards are filtered
before persistence; a reopened Web-backed answer retains only the answer and a
note that its Web sources were not stored.

Select **Local only**, or start Uvaha without `--web-search`, to make no outbound
search requests. Close the terminal when finished to remove the environment
variable from that shell.

## Start Uvaha without a model

Works when LM Studio is broken or not installed. Uvaha becomes the evidence
navigator: it searches the corpus and shows the sources, and says so rather
than pretending a model is loaded. Adding `--web-search` can retrieve Web
sources, but without a model it still does not synthesize an answer.

```bash
cd ~/Orthodox_Intelligence
python tools/serve_prototype.py
```

## Stop Uvaha

Press **Ctrl+C** in the Git Bash window running it.

## Update to the latest fixes

```bash
cd ~/Orthodox_Intelligence
git pull
```

Stop and restart Uvaha afterwards; it reads its code at startup.

## Reinstall the corpus

Needed if the installer refuses, or after changing which commit is pinned.
The `core.autocrlf` line is not optional on Windows: git rewrites line
endings on checkout, which changes every byte of the corpus and fails every
content hash.

```bash
cd ~/plithos_corpus
git config core.autocrlf false
git rm --cached -r -q .
git reset --hard
cd ~/Orthodox_Intelligence
python tools/install_plithos_corpus.py --corpus-repo ../plithos_corpus
```

It should report 1,900 entities and 44,542 texts. **If it refuses,
that is the check working** - it will not install a corpus that is not the one
this build was pinned to.

## Move to a newer corpus

Only when the pin in `config/plithos_corpus.v1.json` has been updated to match.

```bash
cd ~/plithos_corpus
git checkout main
git pull
cd ~/Orthodox_Intelligence
git pull
python tools/install_plithos_corpus.py --corpus-repo ../plithos_corpus
```

## Check the repository is sound

```bash
cd ~/Orthodox_Intelligence
python tools/check_repository.py
python tools/run_evaluation.py --fail-on-any
python -m unittest discover -s tests
```

## A port is already in use

```bash
netstat -ano | findstr :8765
```

The last column is the process id. Then:

```bash
taskkill //PID <that number> //F
```

The doubled slashes are for Git Bash, which would otherwise read `/PID` as a
path.

## The model will not load

`Engine protocol runtime llama-server ... exited before becoming healthy` means
the engine never read the model file, and no generation setting will change
it. In LM Studio, on that model's settings page:

1. Set **GPU Offload to 0** and load it. If it loads, the model is sound and
   the graphics runtime is the fault; raise the offload a few layers at a time
   to find the ceiling.
2. If it still fails at 0, try a different quantization, or a build of the
   same model from a different publisher; a truncated download fails this way.
3. **Uvaha does not need the model.** Run it without `--model-endpoint` and
   the corpus, the calendar, the boundaries and exact-text retrieval all work.

## Every answer comes back as a refusal

If Uvaha answers each question with "Sofiia generated a draft, but it did
not pass the local citation and quotation verifier", read the line the
refusal now ends with. It names the check that failed, and the two cases
mean different things.

*Reason: model output was not strict JSON* means nothing is holding the
model to a shape. Look at the two lines the server prints at startup:

    Model: Sofiia v0.1 · llama.cpp-loopback-development · loopback only
    Structured output: json_schema

`Structured output` must say `grammar` or `json_schema`. If it says
`unknown until the model server answers`, the model server was not
running when Uvaha started: start LM Studio's local server first, then
start Uvaha.

*Reason: answer cited a segment that was not retrieved*, or a reason
naming a quotation, means the model is being held to the shape and is
still getting the substance wrong. That is the verifier doing its work.
A larger model helps; nothing needs fixing.

Update first, in any case:

    cd ~/Orthodox_Intelligence
    git pull

## Build the self-contained Uvaha

One folder that needs nothing else on the machine: no LM Studio, no Git, no
Python, no download. Building it is the only step that reaches the network.

You need the model file first. In LM Studio, download
**OLMo-2-1124-7B-Instruct-Q4_K_M-GGUF** by hus960, then find where it landed:

    dir /s /b "%USERPROFILE%\.lmstudio\models\*OLMo*Q4_K_M*.gguf"

Then, in Git Bash or PowerShell, from the repository:

    cd ~/Orthodox_Intelligence
    git pull
    python tools/build_windows_portable.py --out C:/Uvaha --model "<the .gguf path>" --record-hashes

The first build resolves the current llama.cpp Windows CPU release, downloads
it and the embedded Python, and prints the hash of everything it took. Read
those, then keep them:

    git add config/windows_package_olmo2_q4km.v0.1.json
    git commit -m "Record what the bundle was built from"

Every build after that verifies against those hashes and stops if a published
component has changed underneath.

Then open **C:\Uvaha** and double-click **Uvaha.cmd**. It loads the model,
opens Uvaha in the browser, and unloads the model when you close the window.
The folder can be copied to another machine as it stands.

The corpus travels inside the bundle, so install it before building if you
have not:

    python tools/install_plithos_corpus.py --corpus-repo ../plithos_corpus

**Do not hand this folder to anyone else.** The installed corpus carries
material whose redistribution rights have not been reviewed. It is built for
your own machine.
   the corpus, the boundaries, and exact-text retrieval all work.
