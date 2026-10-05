"""External package smoke fixtures without excluded research modules."""
import unittest

from tgi.identity import decode, encode
from tgi.organization import RawOrganization
from tgi.source_bound_endpoint_transport import certify_source_bound_endpoint_transport
from tgi.source_bound_endpoint_transport_check import verify_source_bound_endpoint_transport


def endpoint_system(bridge_count=2, direct_conflict=False):
    seeds=('🧊','水水','🌋🌋🌋')
    actions=('α','ββ','γ')
    experiences=[('◆',action,'control') for action in actions]
    experiences.append((seeds[2],'δ','control'))
    experiences.extend((seeds[i]+actions[0],actions[1],'first')
                       for i in range(bridge_count))
    experiences.extend((seed,action,'base')
                       for action in actions for seed in seeds)
    layouts=(('old-a','old-b','old-control'),
             ('old-a','old-b','new-b','new-a','old-control','new-control'),
             ('new-b','new-a','new-control'))
    epochs=[]
    for epoch_index,names in enumerate(layouts):
        model=RawOrganization();groups=[];measurements=[]
        epoch_experiences=(experiences+[(seeds[2],actions[1],'conflict')]
                           if direct_conflict and epoch_index==2 else experiences)
        for group_index,(seed,action,mode) in enumerate(epoch_experiences):
            group=[]
            for position,port in enumerate(names):
                role='first' if port.endswith('-a') else 'second' if port.endswith('-b') else 'control'
                changed=(mode=='control' and role=='control' and action=='δ' or
                         mode=='first' and role=='first' or
                         mode=='base' and role!='control' and (
                             action=='α' or action=='ββ' and role=='first' or
                             action=='γ' and role=='second'))
                after=seed+action if changed else seed
                source=f'{group_index}:{position}'
                frames=[seed,action,after]
                model.observe(source,frames)
                group.append({'port':port,'source':source})
                for frame,raw in enumerate(frames):
                    moment=group_index*10+frame
                    measurements.append({'source':source,'frame':frame,
                        'start':0,'stop':len(raw),'clock':'public-smoke-clock',
                        'lower':moment,'upper':moment})
            groups.append(group)
        model.form();epochs.append((model,groups,measurements))
    anchor={'source':f'{len(experiences)-1+int(direct_conflict)}:1','frame':2}
    return epochs,anchor


class PublicM2WheelSmokeTests(unittest.TestCase):
    def test_revoked_role_reports_exact_direct_conflict(self):
        epochs,anchor=endpoint_system(direct_conflict=True)
        c=certify_source_bound_endpoint_transport(
            *epochs,'old-a',anchor,['ββ'])
        self.assertEqual(c['result']['status'],'OBSERVATION_CONTRADICTION')
        self.assertEqual(c['steps'][0]['status'],'OBSERVED_CONFLICT')
        self.assertEqual(c['result']['output'],[])
        self.assertEqual(len(c['steps'][0]['source_ids']),2)
        self.assertTrue(verify_source_bound_endpoint_transport(
            *epochs,'old-a',anchor,['ββ'],c))

    def test_endpoint_heldout_and_null_with_package_only(self):
        for count,expected in ((2,['🌋🌋🌋αββ']),(1,[])):
            epochs,anchor=endpoint_system(count)
            c=certify_source_bound_endpoint_transport(
                *epochs,'old-a',anchor,['α','ββ'])
            self.assertEqual(c['result']['output'],expected)
            self.assertTrue(verify_source_bound_endpoint_transport(
                *epochs,'old-a',anchor,['α','ββ'],c))
    def test_nmu_unicode_identity(self):
        raw='🌋水αβ'
        self.assertEqual(len(encode(raw)),len(raw))
        self.assertEqual(decode(encode(raw)),raw)


if __name__=='__main__':unittest.main()
