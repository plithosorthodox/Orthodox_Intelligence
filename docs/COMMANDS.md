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

## Start Uvaha without a model

Works when LM Studio is broken or not installed. Uvaha becomes the evidence
navigator: it searches the corpus and shows the sources, and says so rather
than pretending a model is loaded.

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
