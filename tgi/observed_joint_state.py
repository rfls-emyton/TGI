"""Fresh complete acquired state; no caller-designated semantic target."""
from copy import deepcopy
from .identity import decode
from .frame_engine import canonical
from .acquisition_snapshot import acquisition_snapshot as snapshot
from .acquisition_witness import certify_raw_acquisition_witness as certify_acquisition_witness
from .measured_context_layout import layout
from .role_work import RoleSearchBudget


def certify_observed_joint_state(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();groups,measurements,observed_groups,observed_measurements=deepcopy((groups,measurements,observed_groups,observed_measurements))
        if not isinstance(groups,list) or not groups or not isinstance(groups[0],list) or not groups[0] or not isinstance(groups[0][0],dict):raise ValueError('Complete original groups required')
        root_port=groups[0][0].get('port')
        trained=snapshot(model);observed=snapshot(observation);learned_witness=certify_acquisition_witness(trained,measurements);state_witness=certify_acquisition_witness(observed,observed_measurements)
        ports,learned_rows=layout(trained,groups,measurements,root_port,budget,allow_partial=True);observed_ports,rows=layout(observed,observed_groups,observed_measurements,root_port,budget,allow_partial=True)
        if ports!=observed_ports:raise ValueError('Original interface inventories must match')
        if type(anchor_group) is not int or not 0<=anchor_group<len(rows):raise ValueError('Original group index required')
        anchor=rows[anchor_group]
        if set(anchor['cells'])!=set(ports):raise ValueError('Complete current original anchor required')
        points=[];values={};latest=True;bounds=[]
        for port in ports:
            budget.consume();cell=anchor['cells'][port];point=cell['measurements'][2];bounds.append(point);values[port]=cell['frames'][2]
            point_latest=True
            for index,row in enumerate(rows):
                if port not in row['cells']:
                    budget.consume();operation=next(iter(row['cells'].values()))['measurements'][1]
                    if operation['clock']!=point['clock'] or operation['upper']>=point['lower']:point_latest=False
                    continue
                for frame in (0,2):
                    budget.consume()
                    if index==anchor_group and frame==2:continue
                    other=row['cells'][port]['measurements'][frame]
                    if other['clock']!=point['clock'] or other['upper']>=point['lower']:point_latest=False
            for row in learned_rows:
                if port not in row['cells']:
                    budget.consume();operation=next(iter(row['cells'].values()))['measurements'][1]
                    if operation['clock']!=point['clock'] or operation['upper']>=point['lower']:point_latest=False
                    continue
                for frame in (0,2):
                    budget.consume();other=row['cells'][port]['measurements'][frame]
                    same=frame==2 and canonical(row['cells'][port])==canonical(cell)
                    if same:continue
                    if other['clock']!=point['clock'] or other['upper']>=point['lower']:point_latest=False
            latest &= point_latest
            points.append({'port':port,'source':cell['source'],'occurrence':cell['occurrences'][2],'measurement':point,'latest_in_scope':bool(point_latest)})
        coherent=len({p['clock'] for p in bounds})==1 and max(p['lower'] for p in bounds)<=min(p['upper'] for p in bounds)
        ready=latest and coherent and all(row['certain'] for row in rows)
        inventory=sorted({decode(frames[1]) for frames,_ in trained.episodes.values()})
        return {'policy':'observed_joint_state_v1','anchor_group':anchor_group,'groups':groups,'observed_groups':observed_groups,'learned_witness':learned_witness,'state_witness':state_witness,'ports':ports,'points':points,'state':values,'inventory':inventory,'result':{'status':'JOINT_STATE_READY' if ready else 'JOINT_STATE_UNRESOLVED','latest_in_scope':bool(latest),'coherent_after':bool(coherent)}}
