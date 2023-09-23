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

import logging
import re
import warnings
from pathlib import Path
from typing import List, Union

from severn.api.dependency import Dependency

ENV_MARKER_PATTERN = re.compile(r"([^<>~=!]+)(.*)")
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

_log = logging.getLogger(__name__)


class RequirementsFile:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = path if isinstance(path, Path) else Path(path)

    def __enter__(self) -> "RequirementsFile":
        return self

    def __exit__(self, *_) -> None:
        ...

    def parse(self) -> List[Dependency]:
        dependencies: List[Dependency] = []

        for i, line in enumerate(
            self.path.read_text().replace(" ", "").splitlines(), start=1
        ):
            if not line or line.startswith("#"):
                # This is quicker and more accurate than making the
                # regex handle it.
                continue

            if not (match := REQUIREMENT_PATTERN.match(line)):
                continue

            attrs = match.groupdict()

            for k in ("con_file", "editable", "wheel", "dist_url", "package_url"):
                if attrs[k]:
                    warnings.warn(
                        f"{k!r} not supported ({self.path}:{i})", stacklevel=4
                    )

            if req_file := attrs["req_file"]:
                _log.info("Scanning nested requirements file (%s)", req_file)
                dependencies.extend(RequirementsFile(req_file).parse())
                continue

            env_markers = {}
            if attrs["env_markers"]:
                for marker in attrs["env_markers"].split(","):
                    marker = marker.replace("'", "").replace('"', "")

                    if not (match := ENV_MARKER_PATTERN.match(marker)):
                        continue

                    env_markers[match.group(1)] = match.group(2)

            dependencies.append(
                d := Dependency(
                    name=attrs["package"],
                    constraints=v.split(",") if (v := attrs["version"]) else None,
                    env_markers=env_markers,
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

            if _log.isEnabledFor(logging.DEBUG):
                _log.debug(
                    "Found dependency %r (constraints = %r) in %s",
                    d.name,
                    [c.as_tuple for c in d.constraints],
                    self.path,
                )

        _log.info("Found %i dependencies in %s", len(dependencies), self.path)
        return dependencies
