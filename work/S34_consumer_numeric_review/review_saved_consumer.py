"""Independent S34 saved-map/cache/source-vote audit. No producer or renderer calls."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import math
import os
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE=Path(__file__).resolve().parent
ARMS=('old_fixed_zero','old_fixed_free_400','old_fixed_common_scale_400')
ROLES=('common_old',)+ARMS
POLICY=dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3,
    raw_vote_atol=1e-8,raw_vote_rtol=1e-10,normalized_atol=1e-10,normalized_rtol=1e-10,
    focal_mean_atol=1e-5,focal_mean_rtol=1e-6,pose_atol=1e-5,pose_rtol=1e-5,
    query_frame=7,render_shape=[288,512],scientific_generation_calls=0)

def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(x,msg):
    if not x:raise RuntimeError(msg)
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def integer(x):return isinstance(x,int) and not isinstance(x,bool)
def exact(a,b,msg):require(a.shape==b.shape and a.dtype==b.dtype and a.tobytes()==b.tobytes(),'Raw byte identity '+msg)
def close(a,b,atol,rtol,msg):require(math.isfinite(float(a)) and math.isfinite(float(b)) and math.isclose(float(a),float(b),abs_tol=atol,rel_tol=rtol),msg)

def main(path,expected):
    require(sha(path)==expected,'Frozen independent audit manifest SHA');m=read(path)
    require(m['schema']=='s34-independent-saved-consumer-review-v1' and m['status']=='FROZEN' and m['policy']==POLICY,'Prepared candidate cannot execute')
    out=Path(m['output']);require(out==HERE/'executed' and not out.exists(),'New bounded output only');out.mkdir()
    started=time.monotonic();rec=dict(status='RUNNING',started_utc=utc(),manifest_sha256=expected,
        new_model=0,new_GA=0,new_MST=0,new_clean=0,new_merge=0,new_renderer=0,sensor_GT_bytes=0,
        role='Different-author saved quantity/source-vote formula audit, not an independent renderer implementation')
    write(out/'receipt.json',rec)
    try:
        def budget():require(time.monotonic()-started<=120,'120second audit wall limit; no automatic retry')
        ids=dict(m['source_sha256']);ids[str(Path(path).resolve())]=expected
        cp=Path(m['consumer_receipt']);cm=Path(m['consumer_manifest'])
        require(cp==ROOT/'results/S34_original_consumer/receipt.json','Fixed original consumer result')
        require(sha(cp)==m['consumer_receipt_sha256'] and sha(cm)==m['consumer_manifest_sha256'],'Actual sealed consumer identities')
        ids[str(cp)]=m['consumer_receipt_sha256'];ids[str(cm)]=m['consumer_manifest_sha256']
        consumer=read(cp);cfg=read(cm)
        require(consumer['status']=='PASS_ORIGINAL_CONSUMER_COMPONENTS' and consumer['manifest_sha256']==m['consumer_manifest_sha256'],'Complete real consumer producer')
        require(consumer['old_map_builds']==1 and consumer['deepcopies']==consumer['append_calls']==consumer['render_calls']==consumer['vote_calls']==3,'Actual complete oldmap plus3 consumer scope')
        require(consumer['full_context_calls']==0 and consumer['final_context_ids_status']=='NOT_RUN_MISSING_NMS_AND_LATENT_HISTORY','No fabricated final context result')
        for rel,h in consumer['outputs'].items():
            p=cp.parent/rel;require(p.resolve().is_relative_to(cp.parent),'Local relative consumer output only');ids[str(p)]=h
        for p,h in consumer['input_sha256'].items():
            require(p not in ids or ids[p]==h,'Consistent recursive input identity');ids[p]=h
        for p,h in ids.items():require(sha(p)==h,'Changed recorded source/input/output '+p)
        write(out/'input_seal.json',dict(status='SEALED_BEFORE_ARRAY_DECODE',utc=utc(),sha256=ids,sensor_GT_bytes=0))
        require(os.path.realpath(sys.executable)==os.path.realpath(m['python']),'Existing scientific Python')
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
        import numpy as np
        require(np.__version__=='1.26.4','Existing NumPy1.26.4, no environment change')
        # No torch, scipy, geometry modules or original vote function are imported.
        def load(p):
            p=Path(p);require(str(p) in ids and sha(p)==ids[str(p)],'Every decoded artifact in barrier')
            with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
        def output(role,name):return load(cp.parent/role/name)
        def source_lists(role,count):
            d=read(cp.parent/role/'sources.json');require(d['color'] is None and set(d['sources'])=={str(i) for i in range(count)},'Contiguous source map '+role)
            entries={int(k):v for k,v in d['sources'].items()}
            for v in entries.values():require(v and len(v)==len(set(v)) and all(integer(i) and 0<=i<(4 if role=='common_old' else 8) for i in v),'Actual unique legal source IDs')
            return entries
        def map_schema(v):
            require(set(v)=={'positions','normals','radii'},'Exact stored geometry fields')
            n=len(v['radii'])
            for k,shape in [('positions',(n,3)),('normals',(n,3)),('radii',(n,))]:
                require(v[k].shape==shape and v[k].dtype==np.float32 and np.isfinite(v[k]).all(),'Original finite FP32 map '+k)
            return n
        def packet(role):
            entry=cfg['packets'][role];p=Path(entry['path']);v=load(p);n=4 if role=='common_old' else 8
            require(set(v)=={'depth','point_cloud','conf','focal','pp','c2w'},'Full producer packet')
            require(v['depth'].shape==(n,384,512) and v['focal'].shape==(n,1) and v['c2w'].shape==(n,4,4),'Producer packet dimensions')
            require(all(a.dtype==np.float32 and np.isfinite(a).all() for a in v.values()),'Producer packet FP32 finite')
            return v
        given_path=Path(cfg['given_optical_c2w']['path']);require(str(given_path) in ids,'Given original optical camera bytes sealed')
        given=np.load(given_path,allow_pickle=False);require(given.shape==(8,4,4) and given.dtype==np.float32,'Given control domain')
        pipeline=given.copy();pipeline[:,:,[1,2]]*=-1
        oldmap=output('common_old','map.npz');oldcount=map_schema(oldmap);require(oldcount>0,'Nonempty real old map')
        oldsources=source_lists('common_old',oldcount);oldpacket=packet('common_old');oldcache=output('common_old','cache.npz')
        exact(oldcache['pipeline_c2ws'],pipeline[:4],'common pipeline cameras')
        exact(oldcache['surfel_Ks'],oldpacket['focal'],'common4 focal cache')
        exact(oldcache['surfel_depths'],oldpacket['depth'],'common4 depth cache')

        def mapping_audit(role,geom,start_sources,start_count,frames):
            """Reconstruct source membership from saved candidate assignments only.

            Does not rerun matching geometry, Octree, normal tests, resize or merge.
            """
            expected_sources={i:list(v) for i,v in start_sources.items()};count=start_count
            trace=read(cp.parent/role/'store_trace.json')['frames'];require([r['frame'] for r in trace]==list(frames),'Only original fixed appended frame indices')
            reduced=output(role,'reduced.npz');require(reduced['point_cloud'].shape[1:]==(19,25,3),'Original saved reduced grid')
            totals=dict(candidates=0,matched_candidates=0,new_surfels=0,source_list_additions=0)
            for frame,row in zip(frames,trace):
                budget();v=output(role,f'frame_{frame}_candidates.npz')
                names={'valid_mask','candidate_reduced_flat_ids','candidate_positions','candidate_normals','candidate_radii','candidate_final_surfel_ids'}
                require(set(v)==names,'All saved candidate fields');mask=v['valid_mask'];flat=v['candidate_reduced_flat_ids'];target=v['candidate_final_surfel_ids']
                require(mask.shape==(19,25) and mask.dtype==np.bool_,'Full original valid mask')
                require(flat.dtype==target.dtype==np.int64 and target.ndim==1 and flat.shape==target.shape,'Complete int64 candidate mappings')
                exact(flat,np.flatnonzero(mask.ravel()),'Mask candidate C-order coverage')
                n=len(target);require(row['frame']==frame and row['map_before']==count and row['candidates']==n and row['reduced_cells']==475,'Observed per-frame counts')
                require(all(integer(int(x)) and 0<=int(x)<len(geom['radii']) for x in target),'Every candidate maps into final real map')
                for name,shape in [('candidate_positions',(n,3)),('candidate_normals',(n,3)),('candidate_radii',(n,))]:
                    require(v[name].shape==shape and v[name].dtype==np.float32 and np.isfinite(v[name]).all(),'Finite candidate geometry '+name)
                exact(v['candidate_positions'],reduced['point_cloud'][frame][mask],'Candidate belongs to actual reduced frame')
                new_indices=[i for i,x in enumerate(target) if int(x)>=count];matched=[int(x) for x in target if int(x)<count]
                new_ids=[int(target[i]) for i in new_indices]
                require(new_ids==list(range(count,count+len(new_ids))),'Every newly appended ID occurs exactly once in original candidate order')
                additions=0
                for i,x in enumerate(target):
                    x=int(x)
                    if x<count:
                        if frame not in expected_sources[x]:expected_sources[x].append(frame);additions+=1
                    else:
                        require(x not in expected_sources,'A new map ID cannot be reintroduced');expected_sources[x]=[frame]
                        for a,b in [('positions','candidate_positions'),('normals','candidate_normals'),('radii','candidate_radii')]:exact(geom[a][x:x+1],v[b][i:i+1],'Appended candidate final geometry '+a)
                require(row['matched_candidates']==len(matched) and row['added_surfels']==len(new_ids) and row['source_list_additions']==additions,'Matched/new/source-addition counters')
                require(row.get('unique_matched_existing_ids',0)==len(set(matched)),'Distinct match IDs separate from candidate count')
                count+=len(new_ids);totals['candidates']+=n;totals['matched_candidates']+=len(matched);totals['new_surfels']+=len(new_ids);totals['source_list_additions']+=additions
            require(count==len(geom['radii']) and set(expected_sources)==set(range(count)),'All final map IDs accounted for, not an empty-set test')
            require(expected_sources==source_lists(role,count),'Independent full ordered source reconstruction')
            return totals
        common_mapping=mapping_audit('common_old',oldmap,{},0,range(4))
        saved={};reports={};query_ref=None
        for role in ARMS:
            budget();geom=output(role,'map.npz');count=map_schema(geom);sources=source_lists(role,count)
            for k in oldmap:exact(geom[k][:oldcount],oldmap[k],'Committed old geometry '+role+'/'+k)
            for i,prefix in oldsources.items():require(sources[i][:len(prefix)]==prefix and all(4<=v<8 for v in sources[i][len(prefix):]),'Old source prefix and only4to7 additions')
            mapping=mapping_audit(role,geom,oldsources,oldcount,range(4,8));arm_summary=consumer['arms'][role]
            require(arm_summary['old_surfel_count']==oldcount and arm_summary['final_surfel_count']==count and arm_summary['total_candidates']==mapping['candidates'] and arm_summary['matched_candidates']==mapping['matched_candidates'] and arm_summary['newly_appended_surfels']==mapping['new_surfels'],'Actual consumer summary vs complete map accounting')
            p=packet(role);cache=output(role,'cache.npz');query=output(role,'query_inputs.npz');render=output(role,'render.npz')
            exact(cache['pipeline_c2ws'],pipeline,'Full8 given pipeline cameras')
            exact(cache['surfel_Ks'],np.concatenate([oldpacket['focal'],p['focal']]),'Original history4 plus own current8 focal bytes')
            exact(cache['surfel_depths'],p['depth'],'Full8 own depth cache bytes')
            require(np.allclose(p['depth'][:4],oldpacket['depth'],atol=1e-5,rtol=1e-5),'Fixed old depth original log/exp tolerance')
            exact(query['target_pipeline_c2w'],pipeline[7:8],'Exactly original same-input query7')
            require(query['average_pipeline_c2w'].shape==query['render_optical_c2w'].shape==(4,4),'Full saved averaged query')
            optical=query['average_pipeline_c2w'].copy();optical[:,[1,2]]*=-1
            exact(query['render_optical_c2w'],optical,'Original averaged pipeline to optical flip')
            require(np.allclose(optical,given[7],atol=1e-5,rtol=1e-5),'One-pose quaternion mean agrees with given7 within encoding tolerance')
            if query_ref is None:query_ref=query['render_optical_c2w'].copy()
            exact(query['render_optical_c2w'],query_ref,'Same actual query across all3')
            history_mean=math.fsum(float(x) for x in cache['surfel_Ks'].ravel())/12
            require(query['mean_history_focal'].shape==(1,) and query['render_focal'].shape==(2,1),'Actual focal shape')
            close(query['mean_history_focal'][0],history_mean,POLICY['focal_mean_atol'],POLICY['focal_mean_rtol'],'History mean fsum vs original FP32 mean')
            for f in query['render_focal'].ravel():close(f,history_mean*.65,POLICY['focal_mean_atol'],POLICY['focal_mean_rtol'],'Original virtual focal .65')
            exact(query['render_pp'],np.asarray([256,144],dtype=np.int64),'Fixed virtual principal point')
            require(set(render)=={'depth','surfel_index_map','cos_value_map'},'Complete original render saved fields')
            for key in ('depth','cos_value_map'):require(render[key].shape==(288,512) and render[key].dtype==np.float32 and np.isfinite(render[key]).all(),'Original render finite FP32 '+key)
            indices=render['surfel_index_map'];require(indices.shape==(288,512) and indices.dtype==np.int32 and ((indices>=-1)&(indices<count)).all(),'Each rendered index resolves within its own real map')
            votes=read(cp.parent/role/'votes.json');vote_report=vote_audit(render,sources,votes)
            reports[role]=dict(map_before=oldcount,map_after=count,old_geometry_raw_exact=True,mapping=mapping,
                focal_cache_length=12,depth_cache_length=8,history_focal_mean_fsum=history_mean,
                render_visible_pixels=int((indices>=0).sum()),render_total_pixels=147456,votes=vote_report,
                final_context_ids=None,scope='Saved physical map/source association and vote arithmetic, no renderer correctness or quality claim')
            saved[role]=dict(geom=geom,sources=sources,render=render,weights=dict(votes['normalized_weights']),candidates=votes['expanded_candidate_source_ids'])
        pairs=[]
        for left,right in itertools.combinations(ARMS,2):
            a,b=saved[left],saved[right];ia=a['render']['surfel_index_map'];ib=b['render']['surfel_index_map'];va=ia>=0;vb=ib>=0;both=va&vb
            depth_delta=np.abs(a['render']['depth'][both].astype(float)-b['render']['depth'][both].astype(float))
            world_delta=a['geom']['positions'][ia[both]].astype(float)-b['geom']['positions'][ib[both]].astype(float)
            distances=np.sqrt((world_delta*world_delta).sum(axis=1))
            membership_changed=sum(tuple(a['sources'][int(x)])!=tuple(b['sources'][int(y)]) for x,y in zip(ia[both],ib[both]))
            pairs.append(dict(left=left,right=right,visible_domain_xor_pixels=int((va^vb).sum()),joint_visible_pixels=int(both.sum()),
                render_depth_abs_difference_mean=None if not len(depth_delta) else float(depth_delta.mean()),
                render_depth_abs_difference_max=None if not len(depth_delta) else float(depth_delta.max()),
                resolved_world_position_distance_mean=None if not len(distances) else float(distances.mean()),
                resolved_world_position_distance_max=None if not len(distances) else float(distances.max()),
                joint_visible_source_list_differences=int(membership_changed),
                normalized_source_weight_L1=math.fsum(abs(a['weights'].get(i,0.)-b['weights'].get(i,0.)) for i in range(8)),
                candidate_sources_equal=a['candidates']==b['candidates'],
                interpretation='Own index maps only resolve own world/source objects; no direct integer-ID difference metric or accuracy claim'))
        write(out/'saved_quantity_report.json',dict(common_old_surfel_count=oldcount,common_old_mapping=common_mapping,arms=reports,pairwise_descriptive_differences=pairs,
            domain_warning='At most8 sources: requested=min(14,k)=k, hence original quota is1 per encountered source. This domain does not exercise remainder rounding.',
            excluded=['independent renderer/visibility correctness','new merge/Octree decision validation','sensor-depth rendering accuracy','final default context IDs','video generation']))
        for p,h in ids.items():require(sha(p)==h,'Identity changed during saved audit '+p)
        budget();rec.update(status='PASS_INDEPENDENT_SAVED_CONSUMER_REVIEW',completed_utc=utc(),wall_seconds=time.monotonic()-started,
            input_sha256=ids,all_three_saved_quantity_groups=True,pairwise_groups=3,
            different_author_formula='math.fsum per-source contribution lists + first term repeated, independent normalization/explicit domain quota',
            outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'})
        write(out/'receipt.json',rec)
    except BaseException as e:
        rec.update(status='FAILED_PRESERVED',completed_utc=utc(),error=repr(e),wall_seconds=time.monotonic()-started)
        write(out/'receipt.json',rec);(out/'traceback.txt').write_text(traceback.format_exc());raise


def vote_audit(render,sources,votes):
    """Independent accumulation; never import/call the original voting kernel."""
    contributions={};first_terms={};negative_cos=0;visible=0
    for sid,cos,depth in zip(render['surfel_index_map'].ravel(),render['cos_value_map'].ravel(),render['depth'].ravel()):
        sid=int(sid)
        if sid<0:continue
        visible+=1;cos=float(cos);depth=float(depth)
        if cos<0:negative_cos+=1;continue
        require(1.+depth>0,'Finite original vote denominator');value=cos/(1.+depth)
        for source in sources[sid]:
            if source not in contributions:contributions[source]=[];first_terms[source]=value
            contributions[source].append(value)
    raw={key:math.fsum(values+[first_terms[key]]) for key,values in contributions.items()}
    actual=votes['raw_votes_in_insertion_order'];require([x[0] for x in actual]==list(raw),'Original C-order/source-list insertion order')
    raw_max=0.
    for key,value in actual:
        close(value,raw[key],POLICY['raw_vote_atol'],POLICY['raw_vote_rtol'],'Fsum independent raw vote '+str(key));raw_max=max(raw_max,abs(value-raw[key]))
    total=math.fsum(raw.values());require(not raw or total>0,'Nonempty source votes need positive total')
    normalized={key:value/total for key,value in raw.items()} if raw else {}
    require([x[0] for x in votes['normalized_weights']]==sorted(normalized),'Original source-sorted normalized list')
    norm_max=0.
    for key,value in votes['normalized_weights']:
        close(value,normalized[key],POLICY['normalized_atol'],POLICY['normalized_rtol'],'Independent normalized source vote');norm_max=max(norm_max,abs(value-normalized[key]))
    count=len(raw);require(count<=8,'Actual legal source cardinality')
    # In THIS frozen experiment n=min(context4+10,k)=k. No remainder branch.
    quota=[[key,1] for key in sorted(raw)]
    require(votes['requested_candidates']==count and votes['candidate_quotas']==quota and votes['quota_sum']==count,'Original k<=8 quota domain')
    require(votes['expanded_candidate_source_ids']==sorted(raw),'Complete candidate expansion')
    require(votes['visible_pixels']==visible and votes['total_pixels']==147456 and votes['query_frame']==7,'Full recorded query/vote domain')
    require(votes['final_context_ids'] is None and votes['final_context_ids_status']=='NOT_RUN_MISSING_NMS_AND_LATENT_HISTORY','No final selection claim')
    return dict(raw_fsum=raw,normalized_fsum=normalized,source_insertion_order=list(raw),first_contribution_repeated=first_terms,
        source_contribution_counts={key:len(v) for key,v in contributions.items()},negative_cos_visible_pixels_skipped=negative_cos,
        raw_max_abs_difference=raw_max,normalized_max_abs_difference=norm_max,quota=quota,
        quota_branch='n=k<=8; one per present source, no remainder branch exercised')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--sha256',required=True)
    a=p.parse_args();main(a.manifest,a.sha256)
