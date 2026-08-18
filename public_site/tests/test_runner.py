from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from public_site.runner import OpenAIRepairRunner


class PublicRunnerTests(unittest.TestCase):
    def test_hosted_code_containers_are_deleted_once(self) -> None:
        response = SimpleNamespace(
            output=[
                SimpleNamespace(type="code_interpreter_call", container_id="container-1"),
                SimpleNamespace(type="message", container_id=None),
                SimpleNamespace(type="code_interpreter_call", container_id="container-1"),
                SimpleNamespace(type="code_interpreter_call", container_id="container-2"),
            ]
        )
        client = SimpleNamespace(containers=SimpleNamespace(delete=Mock()))

        OpenAIRepairRunner._delete_containers(client, response)

        self.assertEqual(
            [call.args[0] for call in client.containers.delete.call_args_list],
            ["container-1", "container-2"],
        )


if __name__ == "__main__":
    unittest.main()
