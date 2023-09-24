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

from severn.abc import Representable


def test_representable_no_slots():
    class Test(Representable):
        def __init__(self):
            self.x = 0
            self.y = 5

    t = Test()
    assert repr(t) == "Test(x=0, y=5)"


def test_representable_no_slots_ignore_private():
    class Test(Representable):
        def __init__(self):
            self.x = 0
            self.y = 5
            self._z = 10

    t = Test()
    assert repr(t) == "Test(x=0, y=5)"


def test_representable_slots():
    class Test(Representable):
        __slots__ = ("x", "y")

        def __init__(self):
            self.x = "never gonna"
            self.y = "give you up"

    t = Test()
    assert repr(t) == "Test(x='never gonna', y='give you up')"


def test_representable_slots_ignore_private():
    class Test(Representable):
        __slots__ = ("x", "y", "_z")

        def __init__(self):
            self.x = "never gonna"
            self.y = "give you up"
            self._z = "sandstorm"

    t = Test()
    assert repr(t) == "Test(x='never gonna', y='give you up')"
