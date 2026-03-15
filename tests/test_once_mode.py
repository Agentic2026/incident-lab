import os
import subprocess
import sys
import unittest


class OnceModeTests(unittest.TestCase):
    def test_profile_can_exit_in_once_mode(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        env["INCIDENT_PROFILE"] = "beacon_periodic"
        env["INCIDENT_ONCE"] = "1"
        env["TARGET_URL"] = "http://127.0.0.1:9/"
        proc = subprocess.run(
            [sys.executable, "-m", "incident_lab"],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
