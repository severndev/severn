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
from dataclasses import KW_ONLY, dataclass
from functools import partial
from typing import List, Optional, Tuple

CONSTRAINT_PATTERN = re.compile(
    r"""^
    (?P<comparator>[<>~=!]{1,2})       # Comparator
    (?:(?P<epoch>[1-9][0-9]*)!)?       # Epoch
    (?P<release>[0-9]+(?:\.[0-9*]+)*)  # Major, minor, patch, etc.
    (?:                                # Pre-release
        (?P<pre_l>(?:a|b|rc))
        (?P<pre_n>[0-9]+)?
    )?
    (?:.post(?P<post>[0-9]+))?         # Post-release
    (?:.dev(?P<dev>[0-9]+))?           # Development release
    $""",
    re.VERBOSE | re.IGNORECASE,
)
MAX_VERSION = 0x3FFFFFFF
PRE_LABEL_MAPPING = {"a": "alpha", "b": "beta"}


def _eq_comparator(theirs: Tuple[int, ...], ours: Tuple[int, ...]) -> bool:
    return theirs == ours


def _ne_comparator(theirs: Tuple[int, ...], ours: Tuple[int, ...]) -> bool:
    return theirs != ours


def _gt_comparator(theirs: Tuple[int, ...], ours: Tuple[int, ...]) -> bool:
    return theirs > ours


def _ge_comparator(theirs: Tuple[int, ...], ours: Tuple[int, ...]) -> bool:
    return theirs >= ours


def _lt_comparator(theirs: Tuple[int, ...], ours: Tuple[int, ...]) -> bool:
    return theirs < ours


def _le_comparator(theirs: Tuple[int, ...], ours: Tuple[int, ...]) -> bool:
    return theirs <= ours


def _fuzzy_comparator(
    specificity: int, theirs: Tuple[int, ...], ours: Tuple[int, ...]
) -> bool:
    return theirs >= ours and theirs[:specificity] == ours[:specificity]


@dataclass()
class Constraint:
    comparator: str
    release: List[int]
    _: KW_ONLY
    epoch: int = 0
    alpha: int = MAX_VERSION
    beta: int = MAX_VERSION
    rc: int = MAX_VERSION
    post: int = MAX_VERSION
    dev: int = MAX_VERSION

    def __post_init__(self) -> None:
        comparator_mapping = {
            "==": _eq_comparator,
            "!=": _ne_comparator,
            ">": _gt_comparator,
            ">=": _ge_comparator,
            "<": _lt_comparator,
            "<=": _le_comparator,
            "~=": partial(_fuzzy_comparator, len(self.release)),
        }
        self._cfunc = comparator_mapping[self.comparator]

    @classmethod
    def from_string(cls, raw: str, /) -> "Constraint":
        if not (match := CONSTRAINT_PATTERN.match(raw)):
            raise ValueError("constraint version must conform to PEP 440")

        version = match.groupdict()
        raw_release = version["release"]

        if "*" in raw_release:
            version["comparator"] = "~="
            raw_release = raw_release.replace("*", "0")
        release = [int(v) for v in raw_release.split(".")]

        def safe_int(value: Optional[str], default: int = MAX_VERSION) -> int:
            return int(value) if value is not None else default

        label = version["pre_l"]
        kwargs = (
            {PRE_LABEL_MAPPING.get(label, label): safe_int(version["pre_n"])}
            if label
            else {}
        )

        return cls(
            version["comparator"],
            release,
            epoch=safe_int(version["epoch"], default=0),
            post=safe_int(version["post"]),
            dev=safe_int(version["dev"]),
            **kwargs,
        )

    def as_tuple(self, release_specificity: Optional[int] = None) -> Tuple[int, ...]:
        if release_specificity:
            release = self.release + [0] * (release_specificity - len(self.release))
        else:
            release = self.release

        return (
            self.epoch,
            *release,
            self.alpha,
            self.beta,
            self.rc,
            self.post,
            self.dev,
        )

    def likes_version(self, version: str, /) -> bool:
        other = Constraint.from_string(f"=={version}")
        specificity = (
            max(sl, ol)
            if (sl := len(self.release)) != (ol := len(other.release))
            else None
        )
        return self._cfunc(  # type: ignore[no-any-return, operator]
            other.as_tuple(specificity), self.as_tuple(specificity)
        )
