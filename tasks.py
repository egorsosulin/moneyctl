#!/usr/bin/env python3

from invoke import task, Collection
from pathlib import Path
import os


# Tasks =====================================================================

@task
def poetry_lock(c):
    """Create poetry lockfile"""
    if not c.poetry.lock_file.exists():
        c.run("poetry lock")


@task(pre=[poetry_lock])
def poetry_install(c):
    """Install all project requirements to venv"""
    if not c.poetry.venv_dir.exists():
        c.run("poetry install")


@task(pre=[poetry_lock])
def docker_build_image(c):
    """Build docker image"""
    image = c.docker.image_name
    c.run(
        f"docker images | grep {image} 1>/dev/null 2>/dev/null" +
        f" || docker build -t {image} ."
    )


@task(pre=[docker_build_image])
def shell_update_completions(c):
    """Update shell completion files in repo"""
    for shell in c.shell.completions:
        completion_file = c.shell.completions[shell].absolute()
        if not completion_file.exists():
            c.run(
                "docker run --rm" +
                f" -e _MONEYCTL_COMPLETE={shell}_source" +
                f" {c.docker.image_name} moneyctl" +
                f"  >{completion_file}"
            )


@task(pre=[docker_build_image, shell_update_completions])
def install(c):
    """Install project to user home space"""
    wrapper_file_src = c.install.wrapper_file.absolute()
    wrapper_file_dest = "~/.bin/moneyctl"
    c.run(f"cp {wrapper_file_src} {wrapper_file_dest}")

    completion_file_src = c.shell.completions.fish.absolute() 
    completion_file_dest = "~/.config/fish/completions/moneyctl.fish"
    c.run(f"cp {completion_file_src} {completion_file_dest}")


@task(pre=[poetry_install])
def lint_python_code(c):
    """Run python code linter (ruff)"""
    os.execlp("poetry", "poetry", "run", "ruff", "check", ".")


### Namespaces ----------------------------------------------------------------

ns = Collection(
    poetry_lock,
    poetry_install,
    docker_build_image,
    shell_update_completions,
    install,
    lint_python_code,
)
ns.configure(
    {
        "run": {
            "echo": True,
        },
        "poetry": {
            "lock_file": Path(".") / "poetry.lock",
            "venv_dir": Path(".") / ".venv",
        },
        "docker": {
            "image_name": "localhost/moneyctl",
        },
        "shell": {
            "completions": {
                "fish": Path(".") / "misc" / "completions" / "moneyctl.fish",
            },
        },
        "install": {
            "wrapper_file": Path(".") / "misc" / "wrapper" / "moneyctl.fish",
        },
    }
)
