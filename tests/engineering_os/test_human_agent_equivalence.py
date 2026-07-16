import unittest

from engineering_os.merge import authorize_merge
from tests.engineering_os.test_merge import MergeTests


class HumanAgentEquivalenceTests(unittest.TestCase):
    def test_human_and_agent_submissions_use_the_same_merge_kernel(self):
        human_case = MergeTests()
        agent_case = MergeTests()
        human_case.setUp()
        agent_case.setUp()
        try:
            human = authorize_merge(
                submitter_kind="human", **human_case.context()
            )
            agent = authorize_merge(
                submitter_kind="agent", **agent_case.context()
            )
            self.assertEqual(human, agent)
        finally:
            human_case.tearDown()
            agent_case.tearDown()


if __name__ == "__main__":
    unittest.main()
