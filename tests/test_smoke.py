import os
import unittest

from incident_lab.main import Config, PROFILE_RUNNERS


class SmokeTests(unittest.TestCase):
    def test_profiles_registered(self) -> None:
        expected = {
            "cpu_periodic",
            "memory_random",
            "beacon_periodic",
            "exfil_burst",
            "io_staging",
            "mixed_intrusion",
        }
        self.assertEqual(expected, set(PROFILE_RUNNERS))

    def test_config_uses_env(self) -> None:
        old_profile = os.environ.get("INCIDENT_PROFILE")
        old_name = os.environ.get("INCIDENT_NAME")
        os.environ["INCIDENT_PROFILE"] = "beacon_periodic"
        os.environ["INCIDENT_NAME"] = "unit-test"
        try:
            cfg = Config()
            self.assertEqual("beacon_periodic", cfg.profile)
            self.assertEqual("unit-test", cfg.name)
        finally:
            if old_profile is None:
                os.environ.pop("INCIDENT_PROFILE", None)
            else:
                os.environ["INCIDENT_PROFILE"] = old_profile
            if old_name is None:
                os.environ.pop("INCIDENT_NAME", None)
            else:
                os.environ["INCIDENT_NAME"] = old_name


if __name__ == "__main__":
    unittest.main()
