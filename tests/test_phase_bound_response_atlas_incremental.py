"""Exact phase parity between incremental and full-prefix atlas formation."""
import random
import copy
import importlib.util
import unittest
from pathlib import Path

from tgi.frame_engine import canonical
from tgi.phase_bound_response_atlas import _atlas, _atlas_reference
from tgi.phase_bound_response_atlas_check import verify

REFERENCE = Path(__file__).with_name('reference_phase_bound_response_atlas_check_v1.py')
SPEC = importlib.util.spec_from_file_location('tgi._reference_phase_bound_response_atlas_check_v1', REFERENCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IncrementalAtlasTests(unittest.TestCase):
    def test_random_chronological_streams_preserve_every_phase(self):
        ports=('p-9','p-2','p-7')
        for trial in range(24):
            rng=random.Random(7100+trial)
            events=[]
            for index in range(rng.randint(4,32)):
                action=rng.choice(('α','ββ','γ'))
                raw=rng.choice(('🧊','水水','🌋🌋🌋','◆'))
                changed={port:bool(rng.getrandbits(1)) for port in ports}
                events.append({'source':f'{trial}:{index}','action':action,
                               'ports':{port:[raw,raw+action if changed[port] else raw]
                                        for port in ports}})
            fast=_atlas(events)
            full=_atlas_reference(events)
            self.assertEqual(canonical(fast),canonical(full),trial)
            self.assertTrue(verify(events,fast),trial)
            self.assertTrue(MODULE.verify(events,fast),trial)
            forged=copy.deepcopy(fast)
            forged['phases'][-1]['event_index']+=1
            self.assertFalse(verify(events,forged),trial)
            self.assertFalse(MODULE.verify(events,forged),trial)

    def test_empty_and_explicit_fracture_revoke(self):
        self.assertEqual(canonical(_atlas([])),canonical(_atlas_reference([])))
        events=[]
        for index,seed in enumerate(('A','B','C','◆')):
            events.append({'source':str(index),'action':'δ','ports':{
                'p': [seed,seed+'δ' if seed!='◆' else seed],
                'q': [seed,seed], 'r': [seed,seed]}})
        events.append({'source':'comparator','action':'κ','ports':{
            'p':['X','X'],'q':['X','Xκ'],'r':['X','X']}})
        events.append({'source':'opposition','action':'δ','ports':{
            'p':['A','A'],'q':['A','A'],'r':['A','A']}})
        fast=_atlas(events)
        self.assertEqual(canonical(fast),canonical(_atlas_reference(events)))
        self.assertTrue(verify(events,fast))
        self.assertTrue(MODULE.verify(events,fast))
        self.assertTrue(fast['phases'][-1]['revoked'])


if __name__=='__main__':unittest.main()
