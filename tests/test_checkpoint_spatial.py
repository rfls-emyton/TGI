from itertools import permutations
from pathlib import Path
import tempfile
import unittest
from tgi.organization import RawOrganization
from tgi.organization_check import verify_resolution

class CheckpointSpatialTests(unittest.TestCase):
    def test_all_source_orders_preserve_geometry_and_certificates(self):
        for order in permutations(('z','a','m')):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as d:
                e=RawOrganization()
                for sid,value in zip(order,('A','B','C')): e.observe(sid,['<'+value+'>','['+value+']'])
                proof=e.resolve(['<Q>']);p=Path(d)/'s.json';e.save(p);r=RawOrganization.load(p)
                self.assertEqual(e.frames.view(),r.frames.view())
                self.assertEqual(e.episodes,r.episodes)
                self.assertEqual(list(e.episodes),list(r.episodes))
                self.assertTrue(verify_resolution(r,['<Q>'],proof))
                for x in (e,r):x.observe('next',['<D>','[D]']);x.form()
                self.assertEqual(e.frames.view(),r.frames.view())
                self.assertEqual(e.organizations,r.organizations)

    def test_revoked_witnesses_unicode_and_shared_frames_survive(self):
        e=RawOrganization()
        for sid,value in zip(('z','b','a'),('猫','e\u0301','🧪')):
            e.observe(sid,['context','<'+value+'>','['+value+']'])
        e.observe('0-counter',['context','<D>','!D!']);e.form()
        self.assertTrue(e.rejected_organizations)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s.json';q=Path(d)/'again.json';e.save(p);r=RawOrganization.load(p);r.save(q)
            self.assertEqual(e.frames.view(),r.frames.view())
            self.assertEqual(e.episodes,r.episodes)
            self.assertEqual(e.rejected_organizations,r.rejected_organizations)
            self.assertEqual(e.resolve(['context','<Q>']),r.resolve(['context','<Q>']))
            self.assertEqual(p.read_bytes(),q.read_bytes())

if __name__=='__main__':unittest.main()
