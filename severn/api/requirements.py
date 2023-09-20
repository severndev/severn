# Copyright (c) 2023-present, Parafoxia, Jonxslays
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
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

### Except for CONSTRAINT_PATTERN, a variant of VERSION_PATTERN,
### which is licensed as follows.

# Copyright (c) Donald Stufft and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

REQUIREMENT_PATTERN = re.compile(
    r"""
    (?:-r(?P<req_file>.*))?         # Requirements file
    (?:-c(?P<con_file>.*))?         # Constraints file
    (?:-e(?P<editable>.*))?         # Editable
    (?P<wheel>(?:./).*)?            # Path to local distribution
    (?P<dist_url>(?:https?://).*)?  # URL to hosted distribution
    (?P<package>[^\[<>~=!@;]+)?     # The name of the dependency
    (?:\[(?P<extras>.*)\])?         # Any extras the dependency specifies
    (?:@(?P<package_url>.*))?       # The URL to a particular package's distribution
    (?P<version>[^;]*)?             # Constraint string
    (?:;(?P<env_markers>.*))?       # Environment markers
    """,
    re.VERBOSE,
)

CONSTRAINT_PATTERN = re.compile(
    r"""
    (?P<comparitor>[<>~=!@]{1,2})                         # comparitor
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9*]+)*)                 # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
    """,
    re.VERBOSE,
)

MAX_VERSION = float("inf")


class Constraint:
    def __init__(
        self,
        comparitor: str,
        *,
        epoch: Optional[int] = None,
        major: int = 0,
        minor: Optional[int] = None,
        patch: Optional[int] = None,
        a: Optional[int] = None,
        b: Optional[int] = None,
        rc: Optional[int] = None,
        post1: Optional[int] = None,
        post2: Optional[int] = None,
        dev: Optional[int] = None,
        release_specificity: int = 3,
    ) -> None:
        self.comparitor = comparitor
        self.epoch = epoch or 0
        self.major = major
        self.minor = minor or 0
        self.patch = patch or 0
        self.alpha = a or MAX_VERSION
        self.beta = b or MAX_VERSION
        self.rc = rc or MAX_VERSION
        self.post1 = post1 or MAX_VERSION
        self.post2 = post2 or MAX_VERSION
        self.dev = dev or MAX_VERSION
        self._release_specificity = release_specificity

    @property
    def as_tuple(self) -> Tuple[Union[int, float], ...]:
        return (
            self.epoch,
            self.major,
            self.minor,
            self.patch,
            self.alpha,
            self.beta,
            self.rc,
            self.post1,
            self.post2,
            self.dev,
        )

    @classmethod
    def from_string(cls, raw: str, /) -> "Constraint":
        if not (match := CONSTRAINT_PATTERN.match(raw)):
            raise ValueError("invalid version string")

        version = match.groupdict()
        raw_release = version["release"]

        if "*" in raw_release:
            version["comparitor"] = "~="
            raw_release = raw_release.replace("*", "0")

        release = [int(v) for v in raw_release.split(".")]
        n_parts = len(release)
        release += [0] * (3 - n_parts)

        def maybe_int(value: Optional[str]) -> Optional[int]:
            return int(value) if value else None

        kwargs = (
            {version["pre_l"]: maybe_int(version["pre_n"])} if version["pre"] else {}
        )

        return cls(
            version["comparitor"],
            epoch=maybe_int(version["epoch"]),
            major=release[0],
            minor=release[1],
            patch=release[2],
            post1=maybe_int(version["post_n1"]),
            post2=maybe_int(version["post_n2"]),
            dev=maybe_int(version["dev_n"]),
            release_specificity=n_parts,
            **kwargs,
        )

    def _tilde_callback(
        self,
        constraint: Tuple[Union[int, float], ...],
        requirement: Tuple[Union[int, float], ...],
    ) -> bool:
        rs = self._release_specificity
        return constraint[:rs] == requirement[:rs] and requirement[rs] >= constraint[rs]

    def likes_version(self, version: str, /) -> bool:
        other = Constraint.from_string(f"=={version}")
        COMPARITOR_MAPPING = {
            "==": self.as_tuple.__eq__,
            "!=": self.as_tuple.__ne__,
            ">": self.as_tuple.__lt__,
            ">=": self.as_tuple.__le__,
            "<": self.as_tuple.__gt__,
            "<=": self.as_tuple.__ge__,
            "~=": partial(self._tilde_callback, self.as_tuple),
        }
        return COMPARITOR_MAPPING[self.comparitor](other.as_tuple)


class Dependency:
    def __init__(
        self,
        name: Optional[str] = None,
        *,
        constraints: Optional[List[str]] = None,
        env_markers: Optional[List[str]] = None,
        extras: Optional[List[str]] = None,
        location: Optional[Union[str, Path]] = None,
        editable: bool = False,
    ) -> None:
        self.name = name
        self.constraints = (
            [Constraint.from_string(c) for c in constraints] if constraints else None
        )
        self.env_markers = env_markers  # TODO: Convert to a dict.
        self.extras = extras
        self.location = location
        self.editable = editable

    def likes_version(self, version: str) -> bool:
        return (
            all(c.likes_version(version) for c in self.constraints)
            if self.constraints
            else True
        )


class RequirementsFile:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = path if isinstance(path, Path) else Path(path)

    def parse(self) -> List[Dependency]:
        dependencies: List[Dependency] = []

        for line in self.path.read_text().replace(" ", "").splitlines():
            if not line or line.startswith("#"):
                # This is quicker and more accurate than making the
                # regex handle it.
                continue

            if not (match := REQUIREMENT_PATTERN.match(line)):
                continue

            attrs = match.groupdict()

            if req_file := attrs["req_file"]:
                dependencies.extend(RequirementsFile(req_file).parse())

            dependencies.append(
                Dependency(
                    name=attrs["package"],
                    constraints=v.split(",") if (v := attrs["version"]) else None,
                    env_markers=em.split(",") if (em := attrs["env_markers"]) else None,
                    extras=e.split(",") if (e := attrs["extras"]) else None,
                    location=(
                        attrs["editable"]
                        or attrs["wheel"]
                        or attrs["dist_url"]
                        or attrs["package_url"]
                    ),
                    editable=bool(attrs["editable"]),
                )
            )

        return dependencies
