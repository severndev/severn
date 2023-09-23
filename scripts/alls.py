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

import sys
import typing as t

import severn


def should_include_module(module: str) -> bool:
    return (
        module != "annotations" and module[0] != "_" and module[0].upper() != module[0]
    )


def get_modules() -> t.List[str]:
    return [m for m in severn.__dict__ if should_include_module(m)]


def get_alls() -> t.Tuple[t.Set[str], t.Set[str]]:
    modules = get_modules()
    return {item for module in modules for item in severn.__dict__[module].__all__}, {
        i for i in severn.__all__ if i not in modules
    }


def validate_alls() -> None:
    modules, lib = get_alls()
    err = None

    if missing := modules - lib:
        err = "Missing exported items at top level:\n" + "\n".join(
            f" - {m}" for m in missing
        )
        print(err, file=sys.stderr)

    if missing := lib - modules:
        err = "Missing exported items at module level:\n" + "\n".join(
            f" - {m}" for m in missing
        )
        print(err, file=sys.stderr)

    if err:
        sys.exit(1)


if __name__ == "__main__":
    validate_alls()
