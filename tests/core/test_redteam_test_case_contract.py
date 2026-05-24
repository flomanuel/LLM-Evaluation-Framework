#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from testframework.redteam.test_case import RTTestCase


def test_rt_test_case_defaults():
    tc = RTTestCase(vulnerability="x", input="prompt")
    assert tc.vulnerability_type is None
    assert tc.actual_output is None
    assert tc.metadata == {}
    assert tc.retrieval_context is None


def test_rt_test_case_accepts_metadata():
    tc = RTTestCase(vulnerability="x", input="prompt", metadata={"k": "v"})
    assert tc.metadata == {"k": "v"}
