"""Independent original latest joint-state verification."""
from copy import deepcopy
from .identity import decode
from .acquisition_snapshot import acquisition_snapshot as snapshot
from .acquisition_witness import verify_raw_acquisition_witness as verify_acquisition_witness
from .measured_context_layout import layout
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_observed_joint_state(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','anchor_group','groups','observed_groups','learned_witness','state_witness','ports','points','state','inventory','result'} or c['policy']!='observed_joint_state_v1':return False
            if type(anchor_group) is not int or type(c['anchor_group']) is not int or c['anchor_group']!=anchor_group or canonical(c['groups'])!=canonical(groups) or canonical(c['observed_groups'])!=canonical(observed_groups):return False
            if not isinstance(groups,list) or not groups or not isinstance(groups[0],list) or not groups[0] or not isinstance(groups[0][0],dict):return False
            root_port=groups[0][0].get('port')
            trained=snapshot(model);observed=snapshot(observation)
            if not verify_acquisition_witness(trained,measurements,c['learned_witness']) or not verify_acquisition_witness(observed,observed_measurements,c['state_witness']):return False
            ports,learned_rows=layout(trained,groups,measurements,root_port,budget,allow_partial=True);op,rows=layout(observed,observed_groups,observed_measurements,root_port,budget,allow_partial=True)
            if ports!=op or not 0<=anchor_group<len(rows) or c['ports']!=ports:return False
            if set(rows[anchor_group]['cells'])!=set(ports):return False
            values={};points=[];latest=True;intervals=[]
            for port in ports:
                budget.consume();cell=rows[anchor_group]['cells'][port];r=cell['measurements'][2];values[port]=cell['frames'][2];intervals.append(r);good=True
                for index,row in enumerate(rows):
                    if port not in row['cells']:
                        budget.consume();operation=next(iter(row['cells'].values()))['measurements'][1]
                        good &= operation['clock']==r['clock'] and operation['upper']<r['lower']
                        continue
                    for fi in (0,2):
                        budget.consume()
                        if (index,fi)==(anchor_group,2):continue
                        other=row['cells'][port]['measurements'][fi]
                        good &= other['clock']==r['clock'] and other['upper']<r['lower']
                for row in learned_rows:
                    if port not in row['cells']:
                        budget.consume();operation=next(iter(row['cells'].values()))['measurements'][1]
                        good &= operation['clock']==r['clock'] and operation['upper']<r['lower']
                        continue
                    for fi in (0,2):
                        budget.consume();other=row['cells'][port]['measurements'][fi]
                        same=fi==2 and canonical(row['cells'][port])==canonical(cell)
                        if not same:good &= other['clock']==r['clock'] and other['upper']<r['lower']
                latest &= good;points.append({'port':port,'source':cell['source'],'occurrence':cell['occurrences'][2],'measurement':r,'latest_in_scope':bool(good)})
            if canonical(c['state'])!=canonical(values) or canonical(c['points'])!=canonical(points):return False
            coherent=len({r['clock'] for r in intervals})==1 and min(r['upper'] for r in intervals)>=max(r['lower'] for r in intervals)
            ready=latest and coherent and all(r['certain'] for r in rows);inventory=sorted({decode(f[1]) for f,_ in trained.episodes.values()})
            if c['inventory']!=inventory:return False
            result={'status':'JOINT_STATE_READY' if ready else 'JOINT_STATE_UNRESOLVED','latest_in_scope':bool(latest),'coherent_after':bool(coherent)}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False
