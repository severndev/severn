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

__all__ = ("Constraint",)

import re
from dataclasses import KW_ONLY, InitVar, dataclass
from functools import partial
from typing import Optional, Tuple, Union

# Based on packaging.version._VERSION_PATTERN, licensed as:
#
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
CONSTRAINT_PATTERN = re.compile(
    r"""
    (?P<comparator>[<>~=!@]{1,2})                         # comparator
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
MAX_VERSION = 0xFFFFFFF


@dataclass()
class Constraint:
    comparator: str
    _: KW_ONLY
    epoch: int = 0
    major: int = 0
    minor: int = 0
    patch: int = 0
    alpha: int = MAX_VERSION
    beta: int = MAX_VERSION
    rc: int = MAX_VERSION
    post1: int = MAX_VERSION
    post2: int = MAX_VERSION
    dev: int = MAX_VERSION
    release_specificity: InitVar[int] = 3

    def __post_init__(self, release_specificity: int) -> None:
        comparator_mapping = {
            "==": self.as_tuple.__eq__,
            "!=": self.as_tuple.__ne__,
            ">": self.as_tuple.__lt__,
            ">=": self.as_tuple.__le__,
            "<": self.as_tuple.__gt__,
            "<=": self.as_tuple.__ge__,
            "~=": partial(self._fuzzy_callback, release_specificity, self.as_tuple),
        }
        self._cfunc = comparator_mapping[self.comparator]

    @property
    def as_tuple(self) -> Tuple[int, ...]:
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
            raise ValueError("version string must conform to PEP 440")

        version = match.groupdict()
        raw_release = version["release"]

        if "*" in raw_release:
            version["comparator"] = "~="
            raw_release = raw_release.replace("*", "0")

        release = [int(v) for v in raw_release.split(".")]
        n_parts = len(release)
        release += [0] * (3 - n_parts)

        def safe_int(value: Optional[str], default: int = 0) -> int:
            return int(value) if value is not None else default

        label_mapping = {"a": "alpha", "b": "beta"}
        label = version["pre_l"]
        kwargs = (
            {label_mapping.get(label, label): safe_int(version["pre_n"])}
            if version["pre"]
            else {}
        )

        return cls(
            version["comparator"],
            epoch=safe_int(version["epoch"]),
            major=release[0],
            minor=release[1],
            patch=release[2],
            post1=safe_int(version["post_n1"], default=MAX_VERSION),
            post2=safe_int(version["post_n2"], default=MAX_VERSION),
            dev=safe_int(version["dev_n"], default=MAX_VERSION),
            release_specificity=n_parts,
            **kwargs,
        )

    def _fuzzy_callback(
        self,
        specificity: int,
        constraint: Tuple[int, ...],
        requirement: Tuple[int, ...],
    ) -> bool:
        return (
            requirement >= constraint
            and requirement[:specificity] == constraint[:specificity]
        )

    def likes_version(self, version: str, /) -> bool:
        # Pyright figured this out, Mypy couldn't. Such a shame.
        return self._cfunc(  # type: ignore[no-any-return, operator]
            Constraint.from_string(f"=={version}").as_tuple
        )
