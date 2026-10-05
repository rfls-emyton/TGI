"""Checker input immutability and full source/lineage rejection."""
import copy
import unittest

from tests.test_source_bound_single_nmu_edit import system
from tgi.frame_engine import canonical
from tgi.source_bound_single_nmu_edit import certify_source_bound_single_nmu_edit
from tgi.source_bound_single_nmu_edit_check import verify_source_bound_single_nmu_edit


class CheckerReadOnlyTests(unittest.TestCase):
    def test_inputs_unchanged_on_success_and_forgery(self):
        epochs,anchor=system(support=3,extra_neutral=40)
        certificate=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ')
        before=canonical({'groups':[epoch[1] for epoch in epochs],
                          'measurements':[epoch[2] for epoch in epochs],
                          'certificate':certificate})
        self.assertTrue(verify_source_bound_single_nmu_edit(
            *epochs,'old-f',anchor,'δ',certificate))
        after=canonical({'groups':[epoch[1] for epoch in epochs],
                         'measurements':[epoch[2] for epoch in epochs],
                         'certificate':certificate})
        self.assertEqual(before,after)
        forged=copy.deepcopy(certificate)
        forged['state']['lineage']['result']['status']='FORGED'
        forged_before=canonical(forged)
        self.assertFalse(verify_source_bound_single_nmu_edit(
            *epochs,'old-f',anchor,'δ',forged))
        self.assertEqual(forged_before,canonical(forged))
        self.assertEqual(before,canonical({'groups':[epoch[1] for epoch in epochs],
                          'measurements':[epoch[2] for epoch in epochs],
                          'certificate':certificate}))

    def test_tampered_measurement_and_live_source_rejected(self):
        epochs,anchor=system(support=3)
        c=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ')
        measured=copy.deepcopy(epochs)
        measured[2][2][0]['lower']+=1
        tampered_before=canonical(measured[2][2])
        self.assertFalse(verify_source_bound_single_nmu_edit(
            *measured,'old-f',anchor,'δ',c))
        self.assertEqual(tampered_before,canonical(measured[2][2]))
        source=c['result']['source_ids'][0]
        frames,receipts=epochs[2][0].episodes[source]
        epochs[2][0].episodes[source]=(frames[:-1],receipts)
        self.assertFalse(verify_source_bound_single_nmu_edit(
            *epochs,'old-f',anchor,'δ',c))


if __name__=='__main__':unittest.main()
