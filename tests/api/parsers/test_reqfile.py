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

import warnings
from math import inf
from pathlib import Path
from unittest import mock

import aiofiles
import pytest

from severn.api.parsers.reqfile import RequirementsFile
from tests import MockAsyncFile


def test_path(reqfile: RequirementsFile):
    assert reqfile.path == Path("rickroll.txt")


def test_path_no_conversion():
    r = RequirementsFile(Path("rickroll.txt"))
    assert r.path == Path("rickroll.txt")


async def test_context_manager(reqfile: RequirementsFile):
    async with reqfile as f:
        assert f.path == Path("rickroll.txt")


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("pytest"))
async def test_parse_name_only_single(mock_open, reqfile: RequirementsFile):
    deps = await reqfile.parse()
    assert len(deps) == 1
    assert deps[0].name == "pytest"


@mock.patch.object(
    aiofiles,
    "open",
    return_value=MockAsyncFile(
        """pytest
pytest-cov
beautifulsoup4"""
    ),
)
async def test_parse_name_only_multiple(mock_open, reqfile: RequirementsFile):
    deps = await reqfile.parse()
    assert len(deps) == 3
    assert deps[0].name == "pytest"
    assert deps[1].name == "pytest-cov"
    assert deps[2].name == "beautifulsoup4"


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("docopt == 0.6.1"))
async def test_parse_with_constraint(mock_open, reqfile: RequirementsFile):
    deps = await reqfile.parse()
    assert len(deps) == 1
    assert deps[0].name == "docopt"
    assert deps[0].constraints[0].as_tuple == (0, 0, 6, 1, inf, inf, inf, inf, inf, inf)


@mock.patch.object(
    aiofiles,
    "open",
    return_value=MockAsyncFile("requests [security] >= 2.8.1, == 2.8.*"),
)
async def test_parse_with_extras(mock_open, reqfile: RequirementsFile):
    deps = await reqfile.parse()
    assert len(deps) == 1
    assert deps[0].name == "requests"
    assert deps[0].constraints[0].as_tuple == (0, 2, 8, 1, inf, inf, inf, inf, inf, inf)
    assert deps[0].constraints[1].as_tuple == (0, 2, 8, 0, inf, inf, inf, inf, inf, inf)
    assert deps[0].extras == ["security"]


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("# comment"))
async def test_parse_comment(mock_open, reqfile: RequirementsFile):
    deps = await reqfile.parse()
    assert len(deps) == 0


# @mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("<>"))
# async def test_parse_invalid_requirement(mock_open, reqfile: RequirementsFile):
#     deps = await reqfile.parse()
#     assert len(deps) == 0


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("-c meme"))
async def test_parse_constraints_files_not_supported(
    mock_open, reqfile: RequirementsFile
):
    with warnings.catch_warnings(record=True) as warns:
        await reqfile.parse()
        assert "'con_file' not supported (rickroll.txt:1)" in str(warns[0].message)


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("-e ."))
async def test_parse_editable_installs_not_supported(
    mock_open, reqfile: RequirementsFile
):
    with warnings.catch_warnings(record=True) as warns:
        await reqfile.parse()
        assert "'editable' not supported (rickroll.txt:1)" in str(warns[0].message)


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("./meme"))
async def test_parse_wheel_not_supported(mock_open, reqfile: RequirementsFile):
    with warnings.catch_warnings(record=True) as warns:
        await reqfile.parse()
        assert "'wheel' not supported (rickroll.txt:1)" in str(warns[0].message)


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("https://example.com"))
async def test_parse_dist_url_not_supported(mock_open, reqfile: RequirementsFile):
    with warnings.catch_warnings(record=True) as warns:
        await reqfile.parse()
        assert "'dist_url' not supported (rickroll.txt:1)" in str(warns[0].message)


@mock.patch.object(
    aiofiles,
    "open",
    return_value=MockAsyncFile(
        "urllib3 @ https://github.com/urllib3/urllib3/archive/refs/tags/1.26.8.zip"
    ),
)
async def test_parse_constraints_files_not_supported(
    mock_open, reqfile: RequirementsFile
):
    with warnings.catch_warnings(record=True) as warns:
        await reqfile.parse()
        assert "'package_url' not supported (rickroll.txt:1)" in str(warns[0].message)


# @mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("https://example.com"))
# async def test_parse_nested_files(mock_open, reqfile: RequirementsFile):
#     with warnings.catch_warnings(record=True) as warns:
#         await reqfile.parse()
#         assert "'dist_url' not supported (rickroll.txt:1)" in str(warns[0].message)


@mock.patch.object(
    aiofiles, "open", return_value=MockAsyncFile("example; python_version >= '3.8'")
)
async def test_parse_env_markers(mock_open, reqfile: RequirementsFile):
    deps = await reqfile.parse()
    assert len(deps) == 1
    assert deps[0].env_markers == {"python_version": ">=3.8"}


@mock.patch.object(aiofiles, "open", return_value=MockAsyncFile("example; <"))
async def test_parse_invalid_env_markers(mock_open, reqfile: RequirementsFile):
    deps = await reqfile.parse()
    assert len(deps) == 1
    assert deps[0].env_markers == {}
