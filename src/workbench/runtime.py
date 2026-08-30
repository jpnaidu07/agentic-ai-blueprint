"""Explicit allowlisted system actions and restricted generated-code execution."""

import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import uuid

import httpx

from src.blueprint import specs
from src.workbench.security import WorkbenchError, local_path, no_secrets
from src.workbench.system import command, executable, inspect_system

IMAGE = "agent-blueprint-runner:local"
SUFFIXES = {".py", ".html", ".css", ".js", ".json", ".md", ".txt", ".yaml", ".yml", ".svg"}


def source_snapshot(path):
    result = {}
    if not path.exists():
        return result
    if path.is_symlink():
        raise WorkbenchError("Runtime source cannot be a symbolic link.")
    for file in sorted(path.rglob("*")):
        relative = file.relative_to(path).as_posix()
        if file.is_symlink():
            raise WorkbenchError("Symbolic links are not allowed in runtime source.")
        if file.is_file():
            local_path(path, relative)
            if file.suffix not in SUFFIXES or file.stat().st_size > 150000:
                raise WorkbenchError("Unsupported or oversized runtime source file.")
            result[relative] = file.read_text(encoding="utf-8")
    if len(result) > 100 or sum(len(v) for v in result.values()) > 1500000:
        raise WorkbenchError(
            "Runtime exceeds this workbench's bounded generation size; export to a dedicated coding environment."
        )
    return result


def source_digest(path):
    return specs.digest(source_snapshot(path))


class Runtime:
    def __init__(self, root, state):
        self.root, self.state = root, state
        self.apps = {}
        self.active_tests = set()
        self.owner = uuid.uuid4().hex[:10]

    def docker(self):
        docker = executable("docker")
        if not docker:
            raise WorkbenchError(
                "Install Docker Desktop (Windows/macOS) or Docker Engine (Linux), start it, then verify `docker info`. Generated code is never run directly on the host."
            )
        result = command([docker, "info", "--format", "{{.ServerVersion}}"], timeout=10)
        if result.returncode:
            raise WorkbenchError(
                "Start Docker and run `docker info`, then retry. No host code was executed."
            )
        return docker

    def runner_ready(self):
        docker = self.docker()
        if command([docker, "image", "inspect", IMAGE]).returncode:
            raise WorkbenchError(
                "Choose Build isolated runner in Setup. It downloads the pinned Python dependencies once; tests then run without network access."
            )
        return docker

    def snapshot(self, solution):
        runtime = specs.safe_solution(self.root, solution) / "implementation/runtime"
        files = source_snapshot(runtime)
        if not files:
            raise WorkbenchError("No generated runtime source exists for this solution yet.")
        target = self.state / "snapshots" / uuid.uuid4().hex
        target.mkdir(parents=True)
        for relative, content in files.items():
            output = local_path(target, relative)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
        return target, specs.digest(files)

    def sandbox_args(self, docker, snapshot, name):
        if "," in str(snapshot):
            raise WorkbenchError("Docker bind mounts require a checkout path without commas.")
        return [
            docker,
            "run",
            "--name",
            name,
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--read-only",
            "--user",
            "65534:65534",
            "--memory",
            "1g",
            "--cpus",
            "2",
            "--pids-limit",
            "128",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=256m",
            "--mount",
            f"type=bind,source={snapshot},target=/app,readonly",
            "--workdir",
            "/app",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--env",
            "PYTHONPATH=/app",
        ]

    def verify(self, solution):
        docker = self.runner_ready()
        snapshot, digest = self.snapshot(solution)
        if not list((snapshot / "tests").glob("test_*.py")):
            raise WorkbenchError(
                "Add real tests/test_*.py acceptance tests before verification. A generated explanation is not completion evidence."
            )
        name = f"blueprint-test-{self.owner}-{uuid.uuid4().hex[:8]}"
        args = self.sandbox_args(docker, snapshot, name) + [
            "--network",
            "none",
            "--rm",
            IMAGE,
            "python",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests",
        ]
        self.active_tests.add(name)
        try:
            output = self._bounded_command(args, 120)
        finally:
            command([docker, "rm", "--force", name], timeout=15)
            self.active_tests.discard(name)
        no_secrets(output["output"])
        return {
            **output,
            "source_digest": digest,
            "isolation": "Docker: no network, no credentials, readonly source, no host/repository mount, 1 GiB, 2 CPUs, 120-second timeout",
            "snapshot": snapshot.name,
        }

    def _bounded_command(self, args, timeout):
        # Spool to a bounded temporary file rather than accumulate untrusted output in RAM.
        output_path = self.state / f"output-{uuid.uuid4().hex}.txt"
        process = None
        try:
            with output_path.open("wb") as output:
                process = subprocess.Popen(
                    args,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                deadline = time.monotonic() + timeout
                while process.poll() is None:
                    if time.monotonic() > deadline or output_path.stat().st_size > 1000000:
                        process.kill()
                        process.wait(timeout=10)
                        raise WorkbenchError(
                            "Command exceeded its time/output budget. Inspect the task and retry with a smaller scope."
                        )
                    time.sleep(0.2)
            with output_path.open("rb") as data:
                text = data.read(24000).decode("utf-8", errors="replace")
            return {"exit_code": process.returncode, "output": text}
        finally:
            if process and process.poll() is None:
                process.kill()
            output_path.unlink(missing_ok=True)

    def action(self, body, event):
        if not body.confirmed:
            raise WorkbenchError(
                "Review the action and confirm it before installing, downloading or launching anything."
            )
        event(f"Authorized action: {body.action}")
        if body.action == "build-runner":
            docker = self.docker()
            result = self._bounded_command(
                [
                    docker,
                    "build",
                    "--file",
                    str(self.root / "infra/Dockerfile.runner"),
                    "--tag",
                    IMAGE,
                    str(self.root),
                ],
                600,
            )
            if result["exit_code"]:
                raise WorkbenchError(
                    "Runner build failed. Check Docker/network availability and run the documented build command; no generated code ran on the host."
                )
            return {
                "message": "Isolated Python runner is ready. Runtime tests have no network access."
            }
        if body.action == "install-ollama":
            if executable("ollama"):
                return {
                    "message": "Ollama is already installed. Choose Start Ollama or refresh setup."
                }
            if os.name == "nt" and executable("winget"):
                args = [
                    executable("winget"),
                    "install",
                    "--id",
                    "Ollama.Ollama",
                    "--exact",
                    "--source",
                    "winget",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                    "--silent",
                ]
            elif sys.platform == "darwin" and executable("brew"):
                args = [executable("brew"), "install", "ollama"]
            else:
                raise WorkbenchError(
                    "Install Ollama from https://ollama.com/download using its official instructions, then restart this workbench. The app does not pipe downloaded shell scripts into a host shell."
                )
            result = self._bounded_command(args, 600)
            if result["exit_code"]:
                raise WorkbenchError(
                    "The Ollama installer needs manual attention. Use https://ollama.com/download, reopen the terminal and verify `ollama --version`."
                )
            return {
                "message": "Installer finished. Refresh hardware detection; if needed restart the workbench so PATH updates are visible."
            }
        if body.action == "start-ollama":
            binary = executable("ollama")
            if not binary:
                raise WorkbenchError("Install Ollama first, then verify `ollama --version`.")
            if inspect_system(self.root)["tools"]["ollama_ready"]:
                return {
                    "message": "An Ollama server is already available on localhost:11434; it was not modified."
                }
            process = subprocess.Popen(
                [binary, "serve"],
                env={**os.environ, "OLLAMA_HOST": "127.0.0.1:11434"},
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            self.apps["ollama"] = {"process": process, "kind": "process"}
            return {
                "message": "Started Ollama on loopback. Refresh setup to verify readiness; this workbench will stop the server it started on shutdown."
            }
        if body.action == "pull-model":
            machine = inspect_system(self.root)
            model = next(m for m in machine["local_models"] if m["id"] == body.model)
            if not model["fits_estimate"]:
                raise WorkbenchError(
                    "The selected model exceeds the conservative RAM/disk budget. Choose a smaller model or use cloud inference."
                )
            try:
                response = httpx.post(
                    "http://127.0.0.1:11434/api/pull",
                    json={"model": body.model, "stream": False},
                    timeout=600,
                    trust_env=False,
                )
                if response.status_code != 200 or response.json().get("status") != "success":
                    raise WorkbenchError(
                        "Model download did not finish. Check Ollama and disk space, then retry."
                    )
            except httpx.HTTPError:
                raise WorkbenchError(
                    "Ollama is unavailable or the download timed out. Start it and retry the model download."
                ) from None
            return {
                "message": f"Downloaded {body.model}; select it in Model connection and run the probe. Hardware fit does not prove task quality."
            }
        if body.action == "launch-tender":
            return self.launch_tender()
        if body.action == "launch-generated":
            return self.launch_generated(body.solution)
        if body.action == "stop-app":
            self.stop(body.solution)
            return {
                "message": "Stopped the app managed by this workbench; no unrelated processes were touched."
            }
        raise WorkbenchError("Unknown action")

    @staticmethod
    def free_port():
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    def launch_tender(self):
        self.stop("government-tender-processing")
        tokens = {
            role: secrets.token_urlsafe(32) for role in ("admin", "evaluator", "reviewer", "viewer")
        }
        # Separate roles, including an independent reviewer. These are local synthetic-data identities.
        auth = [
            {
                "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                "user_id": f"local-{role}",
                "role": role,
                "tender_ids": ["*"],
            }
            for role, token in tokens.items()
        ]
        port = self.free_port()
        env = {
            key: value
            for key, value in os.environ.items()
            if key.upper()
            in {
                "PATH",
                "SYSTEMROOT",
                "WINDIR",
                "TEMP",
                "TMP",
                "HOME",
                "USERPROFILE",
                "LOCALAPPDATA",
            }
        }
        env.update(
            {
                "DATABASE_URL": "sqlite:///" + (self.state / "tender.sqlite").as_posix(),
                "APP_ENV": "development",
                "AUTH_USERS": json.dumps(auth),
                "ALLOW_DOCUMENT_LLM": "false",
                "ENABLE_DEMO_ROUTES": "false",
                "BLUEPRINT_LOAD_DOTENV": "false",
                "PYTHONUNBUFFERED": "1",
            }
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.api.server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-access-log",
            ],
            cwd=self.root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.apps["government-tender-processing"] = {
            "process": process,
            "kind": "process",
            "url": f"http://127.0.0.1:{port}",
            "tokens": tokens,
        }
        try:
            for _ in range(50):
                if process.poll() is not None:
                    break
                try:
                    response = httpx.get(
                        f"http://127.0.0.1:{port}/api/me",
                        headers={"Authorization": f"Bearer {tokens['admin']}"},
                        timeout=1,
                        trust_env=False,
                    )
                    if response.status_code == 200 and response.json()["role"] == "admin":
                        return {
                            "message": "Tender reference is running. Open Apps to reveal a local role token, then sign in to the portal. Provider keys were not shared with it.",
                            "url": f"http://127.0.0.1:{port}",
                            "solution": "government-tender-processing",
                        }
                except (httpx.HTTPError, ValueError, KeyError):
                    pass
                time.sleep(0.2)
        except Exception:
            self.stop("government-tender-processing")
            raise
        self.stop("government-tender-processing")
        raise WorkbenchError(
            "Tender server did not become healthy. Verify Python dependencies and port availability, then retry."
        )

    def launch_generated(self, solution):
        docker = self.runner_ready()
        path = specs.safe_solution(self.root, solution)
        specs.require_approval(path)
        ledger = self.state / "verified" / f"{solution}.json"
        if not ledger.exists():
            raise WorkbenchError(
                "Run isolated acceptance tests successfully before launching generated code."
            )
        record = json.loads(ledger.read_text())
        snapshot, digest = self.snapshot(solution)
        if record["source_digest"] != digest or record["spec_digest"] != specs.spec_digest(path):
            raise WorkbenchError(
                "Source/specs changed after verification. Re-run the selected implementation task and tests before launch."
            )
        if not (snapshot / "app.py").is_file():
            raise WorkbenchError(
                "This preview runtime requires app.py exporting a FastAPI `app`, with GET /api/health. Other stacks need a reviewed custom deployment."
            )
        self.stop(solution)
        network = f"blueprint-{self.owner}"
        if command([docker, "network", "inspect", network]).returncode:
            if command([docker, "network", "create", "--internal", network]).returncode:
                raise WorkbenchError("Could not create the private preview network.")
        name, port = f"blueprint-app-{self.owner}-{solution}", self.free_port()
        args = self.sandbox_args(docker, snapshot, name) + [
            "--detach",
            "--network",
            network,
            "--tmpfs",
            "/data:rw,noexec,nosuid,size=256m,mode=1777",
            IMAGE,
            "python",
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--no-access-log",
        ]
        proxy = f"blueprint-proxy-{self.owner}-{solution}"
        self.apps[solution] = {
            "kind": "container",
            "name": name,
            "proxy_name": proxy,
            "url": f"http://127.0.0.1:{port}",
        }
        try:
            started = command(args, timeout=20).returncode == 0
            if started:
                # Docker does not publish ports from internal-only networks. A trusted
                # relay joins both networks; generated code remains internal-only.
                # Never mount generated source or set PYTHONPATH=/app on the relay.
                started = (
                    command(
                        [
                            docker,
                            "run",
                            "--detach",
                            "--name",
                            proxy,
                            "--network",
                            "bridge",
                            "--publish",
                            f"127.0.0.1:{port}:8080",
                            "--cap-drop",
                            "ALL",
                            "--security-opt",
                            "no-new-privileges",
                            "--read-only",
                            "--user",
                            "65534:65534",
                            "--memory",
                            "256m",
                            "--cpus",
                            "1",
                            "--pids-limit",
                            "64",
                            "--tmpfs",
                            "/tmp:rw,noexec,nosuid,size=32m",
                            "--env",
                            f"UPSTREAM_HOST={name}",
                            "--env",
                            "PYTHONPATH=/opt",
                            IMAGE,
                            "python",
                            "-I",
                            "/opt/blueprint-preview-proxy.py",
                        ],
                        timeout=20,
                    ).returncode
                    == 0
                )
            if started:
                started = (
                    command([docker, "network", "connect", network, proxy], timeout=15).returncode
                    == 0
                )
        except (OSError, subprocess.TimeoutExpired):
            self.stop(solution)
            raise WorkbenchError(
                "Preview startup timed out or Docker became unavailable."
            ) from None
        if not started:
            self.stop(solution)
            raise WorkbenchError(
                "Preview container failed to start. Inspect the runtime contract and Docker availability."
            )
        for _ in range(40):
            try:
                response = httpx.get(
                    f"http://127.0.0.1:{port}/api/health", timeout=1, trust_env=False
                )
                if response.status_code == 200:
                    return {
                        "message": "Generated preview is healthy. This isolated preview has temporary /data storage and no provider keys; it is not a production deployment.",
                        "url": f"http://127.0.0.1:{port}",
                        "solution": solution,
                    }
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        self.stop(solution)
        raise WorkbenchError(
            "Generated app health check failed; fix /api/health and rerun verification."
        )

    def running(self, app):
        if app["kind"] == "process":
            return app["process"].poll() is None
        docker = executable("docker")
        if not docker:
            return False
        try:
            for name in (app["name"], app.get("proxy_name")):
                if name:
                    result = command(
                        [docker, "inspect", "--format", "{{.State.Running}}", name], timeout=5
                    )
                    if result.returncode != 0 or result.stdout.strip() != "true":
                        return False
            return True
        except (OSError, subprocess.TimeoutExpired):
            return False

    def stop(self, solution):
        app = self.apps.pop(solution, None)
        if app and app["kind"] == "process":
            process = app["process"]
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        elif app:
            if app.get("proxy_name"):
                command(
                    [executable("docker") or "docker", "rm", "--force", app["proxy_name"]],
                    timeout=15,
                )
            command([executable("docker") or "docker", "rm", "--force", app["name"]], timeout=15)

    def close(self):
        for solution in list(self.apps):
            try:
                self.stop(solution)
            except (OSError, subprocess.TimeoutExpired):
                pass
        docker = executable("docker")
        if docker:
            try:
                for name in list(self.active_tests):
                    command([docker, "rm", "--force", name], timeout=10)
                command([docker, "network", "rm", f"blueprint-{self.owner}"], timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                pass
