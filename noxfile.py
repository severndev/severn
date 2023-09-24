# Copyright (c) 2023-present, Parafoxia, Jonxslays
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice, this
#        list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright notice,
#        this list of conditions and the following disclaimer in the documentation
#        and/or other materials provided with the distribution.
#
#     3. Neither the name of the copyright holder nor the names of its
#        contributors may be used to endorse or promote products derived from
#        this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import typing as t
from functools import wraps
from pathlib import Path

import nox

REPO_DIR = Path(__file__).parent
PROJECT_NAME = REPO_DIR.stem
PROJECT_DIR = REPO_DIR / PROJECT_NAME
TEST_DIR = REPO_DIR / "tests"
NOX_FILE = REPO_DIR / "noxfile.py"
SETUP_FILE = REPO_DIR / "setup.py"
REQUIREMENTS_FILE = REPO_DIR / "requirements/nox.txt"

SessFT = t.Callable[[nox.Session], None]


def install(
    *, meta: bool = False, rfiles: list[str] | None = None
) -> t.Callable[[SessFT], SessFT]:
    def decorator(func: SessFT) -> SessFT:
        @wraps(func)
        def wrapper(session: nox.Session) -> None:
            deps: list[str] = []
            processing = False

            with Path(REQUIREMENTS_FILE).open() as f:
                for line in f:
                    if line.startswith("#") and line[2:].strip() == func.__name__:
                        processing = True
                        continue

                    if processing:
                        if line == "\n":
                            processing = False
                            break

                        deps.append(line.strip())

            args = ["-U", *deps]
            if meta:
                args.append(".")
            for x in rfiles or []:
                args.extend(["-r", f"requirements/{x}.txt"])

            session.install(*args)
            func(session)

        return wrapper

    return decorator


def sp(*paths: Path) -> list[str]:
    return [str(p) for p in paths]


@nox.session(reuse_venv=True)
@install(meta=True)
def tests(session: nox.Session) -> None:
    session.run(
        "coverage",
        "run",
        "--source",
        PROJECT_NAME,
        "--omit",
        "tests/*",
        "-m",
        "pytest",
        "--log-level=1",
    )
    session.run("coverage", "report", "-m")


@nox.session(reuse_venv=True)
@install(meta=True)
def alls(session: nox.Session) -> None:
    session.run("python", "scripts/alls.py")


@nox.session(reuse_venv=True)
@install()
def dependencies(session: nox.Session) -> None:
    session.run("deputil", "update", "requirements")


@nox.session(reuse_venv=True)
@install()
def formatting(session: nox.Session) -> None:
    session.run(
        "black",
        "--check",
        *sp(PROJECT_DIR, TEST_DIR, NOX_FILE, SETUP_FILE),
    )


@nox.session(reuse_venv=True)
def licensing(session: nox.Session) -> None:
    expd = "# Copyright (c) 2023-present, Parafoxia, Jonxslays"
    errors: t.List[Path] = []

    for path in (
        *PROJECT_DIR.rglob("*.py"),
        *TEST_DIR.rglob("*.py"),
        NOX_FILE,
        SETUP_FILE,
    ):
        with Path(path).open() as f:
            if not f.read().startswith(expd):
                errors.append(path)

    if errors:
        session.error(
            f"\n{len(errors):,} file(s) are missing their licenses:\n"
            + "\n".join(f" - {file}" for file in errors)
        )


@nox.session(reuse_venv=True)
@install()
def linting(session: nox.Session) -> None:
    session.run("ruff", "check", *sp(PROJECT_DIR, NOX_FILE))


@nox.session(reuse_venv=True)
@install(rfiles=["dev"])
def safety(session: nox.Session) -> None:
    session.run("safety", "check", "--full-report")


@nox.session(reuse_venv=True)
@install(meta=True)
def slots(session: nox.Session) -> None:
    session.run("slotscheck", "-m", PROJECT_NAME)


@nox.session(reuse_venv=True)
@install()
def spelling(session: nox.Session) -> None:
    session.run(
        "codespell", *sp(PROJECT_DIR, TEST_DIR, NOX_FILE, SETUP_FILE), "-L", "alls"
    )


@nox.session(reuse_venv=True)
@install(rfiles=["types"])
def typing(session: nox.Session) -> None:
    session.run("mypy", *sp(PROJECT_DIR, SETUP_FILE))
    session.run("pyright", *sp(PROJECT_DIR, SETUP_FILE))
