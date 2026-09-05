"""Start Uvaha and the model it talks to as one thing the owner can close.

An installed bundle has two processes, not one: llama-server holding the
weights, and the Uvaha server in front of it. Asking a reader to start two
things in the right order, in a terminal, is the difference between an
application and a set of instructions - and a model server left running after
the window is closed holds four gigabytes until the machine is restarted.

So this owns the model server: it starts it, waits for it to answer, hands the
port to Uvaha, and takes it down again on the way out, whether the exit is
ordinary, an interrupt, or a failure to start. Nothing here downloads
anything, and nothing here reaches beyond loopback.
"""
from __future__ import annotations

import contextlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


LOOPBACK = "127.0.0.1"
MODEL_READY_TIMEOUT_SECONDS = 300.0
MODEL_POLL_SECONDS = 1.0
SHUTDOWN_GRACE_SECONDS = 10.0


class LauncherError(RuntimeError):
    """Raised when the bundle cannot be started as the owner would expect."""


def free_port() -> int:
    """A port the operating system has just confirmed is free.

    Asked for rather than assumed: 8080 and 8765 are ordinary ports and a
    second copy of the bundle, or anything else on the machine, may hold them.
    A bundle that refuses to start because something unrelated owns a port is
    a bundle the owner cannot use.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((LOOPBACK, 0))
        return int(probe.getsockname()[1])


def read_package(manifest_path: Path) -> dict:
    try:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LauncherError(f"cannot read the package manifest: {manifest_path}") from exc
    if not isinstance(payload, dict) or payload.get("package_id") != "uvaha-windows-portable":
        raise LauncherError("this manifest does not describe the Uvaha bundle")
    network = payload.get("network") or {}
    if network.get("downloads_at_runtime") is not False:
        raise LauncherError("the bundle manifest must state that it downloads nothing at runtime")
    return payload


def model_flags(package: dict) -> list[str]:
    component = (package.get("components") or {}).get("llama_cpp") or {}
    flags = component.get("server_flags")
    if not isinstance(flags, list) or not flags:
        raise LauncherError("the manifest does not carry the model server's required flags")
    out: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise LauncherError("the manifest carries an empty model server flag")
        out.extend(flag.split())
    return out


def wait_for_model(port: int, deadline_seconds: float = MODEL_READY_TIMEOUT_SECONDS,
                   sleep=time.sleep, now=time.monotonic) -> None:
    """Block until the model server answers, or say plainly that it did not.

    A seven-billion-parameter model takes a while to load from disk and the
    window would otherwise open on an application that refuses every question
    for reasons the reader cannot see.
    """
    started = now()
    while now() - started < deadline_seconds:
        try:
            with urlopen(f"http://{LOOPBACK}:{port}/health", timeout=2.0) as response:
                if response.status == 200:
                    return
        except (URLError, OSError):
            pass
        sleep(MODEL_POLL_SECONDS)
    raise LauncherError(
        "the model server did not answer within "
        f"{int(deadline_seconds)} seconds; the weights may be missing or the machine short of memory"
    )


def start_model(server_binary: Path, weights: Path, port: int, flags: list[str],
                popen=subprocess.Popen) -> subprocess.Popen:
    if not Path(server_binary).is_file():
        raise LauncherError(f"the model server is missing from the bundle: {server_binary}")
    if not Path(weights).is_file():
        raise LauncherError(f"the model weights are missing from the bundle: {weights}")
    command = [
        str(server_binary),
        "-m", str(weights),
        "--host", LOOPBACK,
        "--port", str(port),
        *flags,
    ]
    creation = 0
    if os.name == "nt":
        # Its own process group, so a Ctrl-C in the console reaches this
        # launcher rather than killing the model out from under it and leaving
        # the shutdown below with nothing to do.
        creation = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        return popen(command, creationflags=creation) if creation else popen(command)
    except OSError as exc:
        raise LauncherError("the model server would not start") from exc


def stop_model(process, grace_seconds: float = SHUTDOWN_GRACE_SECONDS) -> None:
    """Take the model server down, and make sure it is down.

    Terminate first, because a model server asked politely closes its files.
    Kill after the grace period, because a four-gigabyte process that ignores
    the request must not outlive the window that started it.
    """
    if process is None or process.poll() is not None:
        return
    with contextlib.suppress(Exception):
        process.terminate()
    try:
        process.wait(timeout=grace_seconds)
        return
    except Exception:
        pass
    with contextlib.suppress(Exception):
        process.kill()
    with contextlib.suppress(Exception):
        process.wait(timeout=grace_seconds)


def open_browser(port: int, opener=webbrowser.open) -> None:
    with contextlib.suppress(Exception):
        opener(f"http://{LOOPBACK}:{port}/")


def run(bundle_root: Path, *, open_window: bool = True) -> int:
    """Start the model, start Uvaha, and take the model down again after.

    The bundle's own layout, so nothing here is configurable and nothing has
    to be typed:

        <bundle>/app/                 this repository
        <bundle>/runtime/python/      the embedded interpreter
        <bundle>/runtime/llama/       llama-server.exe and its libraries
        <bundle>/model/*.gguf         the weights
        <bundle>/corpus/              the installed Plithos artifact
        <bundle>/package.json         the manifest this reads
    """
    bundle_root = Path(bundle_root).resolve()
    package = read_package(bundle_root / "package.json")

    server_binary = bundle_root / "runtime" / "llama" / (
        "llama-server.exe" if os.name == "nt" else "llama-server"
    )
    weights = next(iter(sorted((bundle_root / "model").glob("*.gguf"))), None)
    if weights is None:
        raise LauncherError(f"no model weights found in {bundle_root / 'model'}")

    model_port = free_port()
    uvaha_port = free_port()

    print("Uvaha")
    print("Loading the model. The first question after this is the slow one.")
    process = start_model(server_binary, weights, model_port, model_flags(package))
    try:
        wait_for_model(model_port)
        print(f"Ready. Uvaha is at http://{LOOPBACK}:{uvaha_port}/")
        print("Close this window to stop Uvaha and unload the model.")
        if open_window:
            open_browser(uvaha_port)

        sys.path.insert(0, str(bundle_root / "app"))
        from oi_prototype.server import serve  # noqa: PLC0415

        serve(
            bundle_root / "app",
            uvaha_port,
            corpus_install=bundle_root / "corpus",
            model_endpoint=f"http://{LOOPBACK}:{model_port}",
            model_timeout_seconds=900.0,
        )
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        stop_model(process)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    bundle_root = Path(argv[0]) if argv else Path(__file__).resolve().parents[2]
    try:
        return run(bundle_root)
    except LauncherError as exc:
        print(f"Uvaha could not start: {exc}", file=sys.stderr)
        print("Nothing was changed. The bundle folder can be deleted and rebuilt.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    with contextlib.suppress(AttributeError, ValueError):
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    raise SystemExit(main())
