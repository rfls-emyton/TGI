"""Compare incremental C/L checker with the frozen exhaustive raw replay."""
import copy
import importlib.util
import random
import unittest
from pathlib import Path

from tgi.causal_port_classes import _event, form
from tgi.causal_port_classes_check import verify

REFERENCE = Path(__file__).with_name('reference_causal_port_classes_check_v1.py')
SPEC = importlib.util.spec_from_file_location('tgi._reference_causal_port_classes_check_v1', REFERENCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IncrementalCheckerParityTests(unittest.TestCase):
    def test_random_raw_streams_and_forged_certificates(self):
        names = ('p', 'q', 'r', 's')
        seeds = ('A', '水水', '🌋🌋🌋')
        actions = ('α', 'ββ', 'γ')
        for trial in range(24):
            rng = random.Random(41000 + trial)
            events = []
            for index in range(rng.randint(5, 30)):
                action = rng.choice(actions)
                ports = {}
                for name in names:
                    before = rng.choice(seeds)
                    ports[name] = (before, before + 'x' if rng.getrandbits(1) else before)
                events.append(_event(f'{trial}:{index}', action, ports))
            certificate = form(events)
            self.assertTrue(MODULE.verify(events, certificate), trial)
            self.assertTrue(verify(events, certificate), trial)
            forged = copy.deepcopy(certificate)
            forged['phases'][-1]['event_index'] += 1
            self.assertFalse(MODULE.verify(events, forged), trial)
            self.assertFalse(verify(events, forged), trial)


if __name__ == '__main__':
    unittest.main()
