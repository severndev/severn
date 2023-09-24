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

from math import inf

import pytest

from severn.api.constraint import Constraint


def test_defaults():
    c = Constraint("==")
    assert c.epoch == 0
    assert c.major == 0
    assert c.minor == 0
    assert c.patch == 0
    assert c.alpha == inf
    assert c.beta == inf
    assert c.rc == inf
    assert c.post1 == inf
    assert c.post2 == inf
    assert c.dev == inf


def test_as_tuple(constraint: Constraint):
    assert constraint.as_tuple == (0, 2, 8, 2, inf, inf, inf, inf, inf, inf)


def test_as_tuple_prerelease(prerelease_constraint: Constraint):
    assert prerelease_constraint.as_tuple == (0, 2, 8, 2, 5, inf, inf, inf, 3, inf)


def test_from_string(constraint: Constraint):
    assert Constraint.from_string(">=2.8.2").as_tuple == constraint.as_tuple


def test_from_string_prerelease(prerelease_constraint: Constraint):
    assert (
        Constraint.from_string(">=2.8.2a5.post3").as_tuple
        == prerelease_constraint.as_tuple
    )


def test_from_string_invalid_version():
    with pytest.raises(ValueError, match="version string must conform to SemVer"):
        Constraint.from_string(">=rickroll")


def test_from_string_star_operator():
    c = Constraint.from_string("==2.8.*")
    assert c.comparator == "~="
    assert c.major == 2
    assert c.minor == 8
    assert c.patch == 0


def test_likes_version_exactly_equals():
    c = Constraint.from_string("==2.8.2")
    assert c.likes_version("2.8.2")
    assert not c.likes_version("2.8.1")
    assert not c.likes_version("2.8.3")
    assert not c.likes_version("2.7.2")
    assert not c.likes_version("2.9.2")
    assert not c.likes_version("1.8.2")
    assert not c.likes_version("3.8.2")
    assert not c.likes_version("2.8.1rc9")
    assert not c.likes_version("2.8.2.dev0")
    assert not c.likes_version("2.8.3.dev0")


def test_likes_version_not_equals():
    c = Constraint.from_string("!=2.8.2")
    assert not c.likes_version("2.8.2")
    assert c.likes_version("2.8.1")
    assert c.likes_version("2.8.3")
    assert c.likes_version("2.7.2")
    assert c.likes_version("2.9.2")
    assert c.likes_version("1.8.2")
    assert c.likes_version("3.8.2")
    assert c.likes_version("2.8.1rc9")
    assert c.likes_version("2.8.2.dev0")
    assert c.likes_version("2.8.3.dev0")


def test_likes_version_greater_than():
    c = Constraint.from_string(">2.8.2")
    assert not c.likes_version("2.8.2")
    assert not c.likes_version("2.8.1")
    assert c.likes_version("2.8.3")
    assert not c.likes_version("2.7.2")
    assert c.likes_version("2.9.2")
    assert not c.likes_version("1.8.2")
    assert c.likes_version("3.8.2")
    assert not c.likes_version("2.8.1rc9")
    assert not c.likes_version("2.8.2.dev0")
    assert c.likes_version("2.8.3.dev0")


def test_likes_version_greater_than_or_equals():
    c = Constraint.from_string(">=2.8.2")
    assert c.likes_version("2.8.2")
    assert not c.likes_version("2.8.1")
    assert c.likes_version("2.8.3")
    assert not c.likes_version("2.7.2")
    assert c.likes_version("2.9.2")
    assert not c.likes_version("1.8.2")
    assert c.likes_version("3.8.2")
    assert not c.likes_version("2.8.1rc9")
    assert not c.likes_version("2.8.2.dev0")
    assert c.likes_version("2.8.3.dev0")


def test_likes_version_less_than():
    c = Constraint.from_string("<2.8.2")
    assert not c.likes_version("2.8.2")
    assert c.likes_version("2.8.1")
    assert not c.likes_version("2.8.3")
    assert c.likes_version("2.7.2")
    assert not c.likes_version("2.9.2")
    assert c.likes_version("1.8.2")
    assert not c.likes_version("3.8.2")
    assert c.likes_version("2.8.1rc9")
    assert c.likes_version("2.8.2.dev0")
    assert not c.likes_version("2.8.3.dev0")


def test_likes_version_less_than_or_equals():
    c = Constraint.from_string("<=2.8.2")
    assert c.likes_version("2.8.2")
    assert c.likes_version("2.8.1")
    assert not c.likes_version("2.8.3")
    assert c.likes_version("2.7.2")
    assert not c.likes_version("2.9.2")
    assert c.likes_version("1.8.2")
    assert not c.likes_version("3.8.2")
    assert c.likes_version("2.8.1rc9")
    assert c.likes_version("2.8.2.dev0")
    assert not c.likes_version("2.8.3.dev0")


def test_likes_version_fuzzy_equals():
    c = Constraint.from_string("~=2.8.2")
    assert c.likes_version("2.8.2")
    assert not c.likes_version("2.8.1")
    assert c.likes_version("2.8.3")
    assert not c.likes_version("2.7.2")
    assert not c.likes_version("2.9.2")
    assert not c.likes_version("1.8.2")
    assert not c.likes_version("3.8.2")
    assert not c.likes_version("2.8.1rc9")
    assert not c.likes_version("2.8.2.dev0")
    assert c.likes_version("2.8.3.dev0")


def test_likes_version_prerelease_alpha():
    c = Constraint.from_string(">=2.8.2a1")
    assert c.likes_version("2.8.2a1")
    assert c.likes_version("2.8.2b1")
    assert c.likes_version("2.8.2rc1")


def test_likes_version_prerelease_beta():
    c = Constraint.from_string(">=2.8.2b1")
    assert not c.likes_version("2.8.2a1")
    assert c.likes_version("2.8.2b1")
    assert c.likes_version("2.8.2rc1")


def test_likes_version_prerelease_rc():
    c = Constraint.from_string(">=2.8.2rc1")
    assert not c.likes_version("2.8.2a1")
    assert not c.likes_version("2.8.2b1")
    assert c.likes_version("2.8.2rc1")
