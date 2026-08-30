"""Read-only hardware discovery and conservative, explicitly estimated local-model fit."""

import ctypes
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

import httpx

LOCAL_MODELS = [
    {
        "id": "qwen3:4b",
        "download_gb": 2.5,
        "working_gb": 6,
        "purpose": "Small local experiments and private spec drafts",
        "source": "https://ollama.com/library/qwen3:4b",
    },
    {
        "id": "qwen3:8b",
        "download_gb": 5.2,
        "working_gb": 10,
        "purpose": "Larger local drafts; measure latency and code quality first",
        "source": "https://ollama.com/library/qwen3:8b",
    },
]


def executable(name):
    found = shutil.which(name)
    if not found and name == "ollama" and os.name == "nt":
        candidate = Path(os.getenv("LOCALAPPDATA", "")) / "Programs/Ollama/ollama.exe"
        if candidate.is_file():
            found = str(candidate)
    return found


def command(args, timeout=6, cwd=None, env=None):
    """Only callers constructing fixed allowlisted argv may use this helper."""
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def memory():
    if os.name == "nt":

        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (key, ctypes.c_ulonglong)
                for key in (
                    "total",
                    "available",
                    "page_total",
                    "page_available",
                    "virtual_total",
                    "virtual_available",
                    "extended",
                )
            ]

        value = Memory()
        value.length = ctypes.sizeof(value)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):
            return value.total / 2**30, value.available / 2**30
    if Path("/proc/meminfo").exists():
        values = {
            line.split(":")[0]: int(line.split()[1]) / 1024**2
            for line in Path("/proc/meminfo").read_text().splitlines()
        }
        return values["MemTotal"], values.get("MemAvailable", values.get("MemFree", 0))
    if platform.system() == "Darwin":
        result = command(["sysctl", "-n", "hw.memsize"])
        if result.returncode == 0:
            return int(result.stdout.strip()) / 2**30, None
    return None, None


def inspect_system(root):
    total, available = memory()
    cpu, gpu = platform.processor() or platform.machine(), "Not detected; acceleration unverified"
    if os.name == "nt":
        try:
            value = command(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "@{cpu=(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name); gpu=@(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name)} | ConvertTo-Json -Compress",
                ],
                timeout=8,
            )
            hardware = json.loads(value.stdout)
            cpu, gpu = hardware["cpu"], ", ".join(hardware["gpu"])
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    docker, ollama = executable("docker"), executable("ollama")
    docker_ready = False
    if docker:
        try:
            docker_ready = (
                command([docker, "info", "--format", "{{.ServerVersion}}"], timeout=5).returncode
                == 0
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    ollama_ready, installed = False, []
    try:
        response = httpx.get("http://127.0.0.1:11434/api/tags", timeout=2, trust_env=False)
        response.raise_for_status()
        installed = [m["name"] for m in response.json().get("models", [])]
        ollama_ready = True
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    disk = shutil.disk_usage(root).free / 2**30
    budget = max(0, (total or 0) - 12)
    return {
        "os": platform.system(),
        "architecture": platform.machine(),
        "cpu": cpu,
        "logical_cpus": os.cpu_count(),
        "gpu": gpu,
        "ram_gb": round(total, 1) if total else None,
        "available_ram_gb": round(available, 1) if available is not None else None,
        "disk_free_gb": round(disk, 1),
        "tools": {
            "python": platform.python_version(),
            "git": bool(executable("git")),
            "docker": bool(docker),
            "docker_ready": docker_ready,
            "ollama": bool(ollama),
            "ollama_ready": ollama_ready,
            "winget": bool(executable("winget")),
            "brew": bool(executable("brew")),
        },
        "installed_models": installed,
        "local_models": [
            {
                **model,
                "fits_estimate": model["working_gb"] <= budget and disk >= model["download_gb"] + 3,
                "available_now_estimate": available is not None
                and model["working_gb"] + 4 <= available,
            }
            for model in LOCAL_MODELS
        ],
        "guidance": [
            "Reserve about 12 GiB for the OS, editor, browser and application services; model estimates are not benchmarks.",
            "Start with cloud inference for demanding implementation, or a small quantized local model for experiments. Verify structured output and task acceptance before trusting it.",
            "An Intel integrated GPU shares system memory. Ollama Vulkan support is experimental; GPU speed and compatibility are not guaranteed. CPU fallback can be slow.",
            "Model weights, context/KV cache, quantization and concurrent applications all affect memory. Check live available RAM before downloading or running.",
        ],
        "sources": ["https://docs.ollama.com/gpu", "https://docs.ollama.com/windows"],
    }
