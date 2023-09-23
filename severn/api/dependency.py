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

from pathlib import Path
from typing import Dict, List, Optional, Union

from severn.abc import Representable
from severn.api.constraint import Constraint


class Dependency(Representable):
    def __init__(
        self,
        name: Optional[str] = None,
        *,
        constraints: Optional[List[str]] = None,
        env_markers: Optional[Dict[str, str]] = None,
        extras: Optional[List[str]] = None,
        location: Optional[Union[str, Path]] = None,
        editable: bool = False,
    ) -> None:
        self.name = name
        self.constraints = (
            [Constraint.from_string(c) for c in constraints] if constraints else []
        )
        self.env_markers = env_markers
        self.extras = extras
        self.location = location
        self.editable = editable

    def __str__(self) -> str:
        return self.name or "Undefined"

    def likes_version(self, version: str) -> bool:
        return all(c.likes_version(version) for c in self.constraints)
