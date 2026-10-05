"""Source-bound midstream NMU substitution and falsifiers."""
import copy
import tempfile
import unittest
from pathlib import Path

from tgi.organization import RawOrganization
from tgi.source_bound_single_nmu_edit import (
    certify_source_bound_single_nmu_edit, commit_source_bound_single_nmu_edit,
    recover_source_bound_single_nmu_edit)
from tgi.source_bound_single_nmu_edit_check import verify_source_bound_single_nmu_edit


def system(*, support=2, opposition=False, duplicated=False,
           direct_conflict=False, recode=None, extra_neutral=0,
           alternate_pair=False, port_map=None):
    rows=[('◆','δ','stable'),('A0','δ','first'),('B0','δ','first')]
    if support>=3:
        rows.append(('D0','δ','first'))
    if opposition:
        rows.append(('E0','δ','stable'))
    if direct_conflict:
        rows.extend([('C0','δ','first'),('C0','δ','stable')])
    if alternate_pair:
        rows.extend((seed,'δ','first') for seed in ('X2','Y2','Z2'))
    rows.extend([('Q','κ','control'),('A0','γ','second'),
                 ('B0','γ','second'),('D0','γ','second')])
    rows.extend((f'N{i}','κ','stable') for i in range(extra_neutral))
    rows.append(('C00' if duplicated else 'C02' if alternate_pair else 'C0',
                 'γ','second'))
    old={'first':'old-f','second':'old-s','control':'old-c'}
    new={'first':'new-f','second':'new-s','control':'new-c'}
    port_map=port_map or {}
    old_ports={port_map.get(address,address):role for role,address in old.items()}
    new_ports={port_map.get(address,address):role for role,address in new.items()}
    inventories=[old_ports,{**old_ports,**new_ports},new_ports]
    epochs=[]
    for epoch,inventory in enumerate(inventories):
        model=RawOrganization();groups=[];measurements=[]
        for g,(seed,action,target) in enumerate(rows):
            group=[]
            for port,role in inventory.items():
                after=seed
                if target==role:
                    after=(seed.replace('0','1',1) if '0' in seed else
                           seed.replace('2','3',1)) if action=='δ' else seed+action
                source=f'{epoch}:{g}:{port}'
                frames=[seed,action,after]
                if recode:
                    frames=[''.join(recode.get(char,char) for char in raw)
                            for raw in frames]
                model.observe(source,frames)
                group.append({'port':port,'source':source})
                for frame,raw in enumerate(frames):
                    t=epoch*10000+g*100+frame*10
                    measurements.append({'source':source,'frame':frame,'start':0,
                        'stop':len(raw),'clock':'edit-clock','lower':t,'upper':t})
            groups.append(group)
        model.form();epochs.append((model,groups,measurements))
    anchor={'source':f"2:{len(rows)-1}:{port_map.get('new-f','new-f')}",'frame':2}
    return epochs,anchor


class SingleNMUEditTests(unittest.TestCase):
    def test_heldout_substitution_and_controls(self):
        epochs,anchor=system(support=3)
        c=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ')
        self.assertEqual(c['result']['output'],['C1'],c)
        self.assertEqual(c['result']['mode'],'HELDOUT_SUBSTITUTE')
        self.assertTrue(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',c))
        for mutation in ('output','pair','sources','lineage'):
            forged=copy.deepcopy(c)
            if mutation=='output':forged['result']['output']=['C2']
            elif mutation=='pair':forged['result']['pair_nmu'][1]+=1
            elif mutation=='sources':forged['result']['source_ids'].pop()
            else:forged['result']['lineage'][-1]['position']=999
            self.assertFalse(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',forged))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edit.json'
            digest=commit_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',c,path)['sha256']
            self.assertEqual(recover_source_bound_single_nmu_edit(
                *epochs,'old-f',anchor,'δ',path,digest),c)
            with self.assertRaises(ValueError):
                recover_source_bound_single_nmu_edit(
                    *epochs,'old-f',anchor,'δ',path,'0'*64)
    def test_insufficient_support_opposition_and_ambiguous_query(self):
        for kwargs in ({'support':2},{'support':3,'opposition':True},
                       {'support':3,'duplicated':True}):
            with self.subTest(kwargs=kwargs):
                epochs,anchor=system(**kwargs)
                c=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ')
                self.assertEqual(c['result']['output'],[],c)
                self.assertTrue(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',c))
    def test_direct_conflict_and_injective_unicode_recode(self):
        epochs,anchor=system(support=3,direct_conflict=True)
        c=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ')
        self.assertEqual(c['result']['status'],'OBSERVATION_CONTRADICTION')
        self.assertEqual(c['result']['output'],[])
        self.assertTrue(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',c))
        mapping={'A':'木','B':'砂','C':'光','D':'石','0':'零','1':'壹',
                 'δ':'ζ','γ':'θ','κ':'λ'}
        epochs,anchor=system(support=3,recode=mapping)
        c=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'ζ')
        self.assertEqual(c['result']['output'],['光壹'],c)
        self.assertTrue(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'ζ',c))
    def test_continual_neutral_append_and_source_mutation(self):
        epochs,anchor=system(support=3,extra_neutral=40)
        c=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ')
        self.assertEqual(c['result']['output'],['C1'])
        self.assertTrue(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',c))
        source=c['result']['source_ids'][0]
        model=epochs[2][0]
        frames,receipts=model.episodes[source]
        model.episodes[source]=(frames[:-1],receipts)
        self.assertFalse(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',c))
    def test_ambiguous_pair_and_port_relabeling(self):
        epochs,anchor=system(support=3,alternate_pair=True)
        c=certify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ')
        self.assertEqual(c['result']['output'],[])
        self.assertEqual(c['result']['status'],'NO_PATH')
        self.assertTrue(verify_source_bound_single_nmu_edit(*epochs,'old-f',anchor,'δ',c))
        mapping={'old-f':'p-82','old-s':'p-14','old-c':'p-57',
                 'new-f':'p-31','new-s':'p-96','new-c':'p-23'}
        epochs,anchor=system(support=3,port_map=mapping)
        c=certify_source_bound_single_nmu_edit(*epochs,mapping['old-f'],anchor,'δ')
        self.assertEqual(c['result']['output'],['C1'])
        self.assertTrue(verify_source_bound_single_nmu_edit(
            *epochs,mapping['old-f'],anchor,'δ',c))


if __name__=='__main__':unittest.main()
