"""Tiny artificial tensors only. No model, GA, experiment arrays, RGB or GT reads."""
from pathlib import Path
import ast, hashlib, json, math
from datetime import datetime, timezone
import torch
import torch.nn as nn

HERE=Path(__file__).resolve().parent
SOURCE=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py')

def main():
    output=HERE/'artificial_checks.json'
    assert not output.exists(),'No overwrite'
    torch.set_num_threads(1)
    started=datetime.now(timezone.utc).isoformat()
    raw=SOURCE.read_bytes()
    tree=ast.parse(raw)
    chosen=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'ParameterStack','_ravel_hw'}]
    assert {n.name for n in chosen}=={'ParameterStack','_ravel_hw'}
    ns={'torch':torch,'nn':nn}
    exec(compile(ast.Module(body=chosen,type_ignores=[]),str(SOURCE)+'::two-pure-helper-definitions','exec'),ns)
    gradient=[]
    for flags in ((True,True),(False,True)):
        params=nn.ParameterList([nn.Parameter(torch.tensor([[0.0,math.log(2)]],dtype=torch.float32),requires_grad=flag) for flag in flags])
        stacked=ns['ParameterStack'](params,is_param=False)
        restored=stacked.exp()
        loss=restored.sum()
        if loss.requires_grad:loss.backward()
        row={'original_requires_grad':list(flags),'stacked_requires_grad':stacked.requires_grad,
             'stacked_is_new_leaf':stacked.is_leaf,'stacked_is_registered_original':any(stacked is p for p in params),
             'original_grad_is_none':[p.grad is None for p in params],
             'temporary_stacked_grad':None if stacked.grad is None else stacked.grad.tolist(),
             'backward_executed':loss.requires_grad}
        assert all(row['original_grad_is_none'])
        gradient.append(row)

    D=torch.float64
    depth=torch.tensor([[2.,3.],[4.,5.]],dtype=D)
    ray=torch.tensor([[[0.,0.,1.],[.2,.1,1.]],[[-.2,.1,1.],[.1,-.3,1.]]],dtype=D)
    local=depth[...,None]*ray
    z=torch.tensor([[[.1,0.,1.7],[.5,.3,2.7]],[[-.6,.2,3.7],[.2,-1.2,4.3]]],dtype=D)
    weights=torch.tensor([[1.,2.],[3.,.5]],dtype=D)
    def objective(x,y):return float((torch.linalg.vector_norm(x-y,dim=-1)*weights).sum()/2)
    center=torch.tensor([1.,2.,3.],dtype=D)
    scale=1.2;translation=center+torch.tensor([.2,-.1,.4],dtype=D)
    x=center+local;y=scale*z+translation
    base=objective(x,y)
    homogeneity=[]
    for alpha in [.25,.5,1.,2.]:
        scaled_x=center+alpha*local
        scaled_y=alpha*scale*z+center+alpha*(translation-center)
        loss=objective(scaled_x,scaled_y)
        assert math.isclose(loss,alpha*base,rel_tol=1e-13,abs_tol=1e-13)
        tau=translation/scale
        tau_prime=tau+(1-alpha)*center/(alpha*scale)
        assert torch.allclose(alpha*scale*(z+tau_prime),scaled_y,rtol=1e-13,atol=1e-13)
        homogeneity.append({'alpha':alpha,'loss':loss,'alpha_times_original':alpha*base,
                            'raw_translation_reparameterization_max_abs':float((alpha*scale*(z+tau_prime)-scaled_y).abs().max())})
    alpha=.5
    fixed_x=x.clone();fixed_x[1]=center+alpha*local[1]
    scaled_y=alpha*scale*z+center+alpha*(translation-center)
    residual=fixed_x-scaled_y
    expected=alpha*(x-y)
    expected[0]+=(1-alpha)*(x[0]-center)
    assert torch.allclose(residual,expected,rtol=1e-13,atol=1e-13)
    fixed_old={'alpha':alpha,'loss_with_old_depth_fixed':objective(fixed_x,scaled_y),'invalid_full_scale_prediction':alpha*base,
               'old_residual_extra_max_abs':float(((1-alpha)*(x[0]-center)).abs().max())}

    centers=center+torch.tensor([[0.,0.,0.],[.01,0.,0.]],dtype=D)
    xb=centers[:,None,:]+local
    yb=xb.clone()  # Artificial exact initial fit, positive but small baseline.
    xs=centers[:,None,:]+alpha*local
    ys=center+alpha*(yb-center)
    actual_residual=xs-ys
    formula_residual=alpha*(xb-yb)+(1-alpha)*(centers[:,None,:]-center)
    assert torch.allclose(actual_residual,formula_residual,rtol=1e-13,atol=1e-13)
    before=objective(xb,yb);after=objective(xs,ys)
    assert before==0. and after>0.
    # Positive fixed weights give a baseline-controlled additive bound.
    baseline_bound=float((weights*torch.linalg.vector_norm(centers[:,None,:]-center,dim=-1)).sum()/2)
    assert abs(after-alpha*before)<=abs(1-alpha)*baseline_bound+1e-13
    nonzero={'baseline_m':.01,'initial_loss':before,'alpha':alpha,'after_loss':after,
             'bound_B':baseline_bound,'conclusion':'Even a short positive baseline does not universally imply shrinking lowers loss.'}

    logs=torch.tensor([math.log(.8),math.log(1.7)],dtype=D)
    norm=lambda l:torch.exp(l)*torch.exp(math.log(.5)-l.mean())
    before_scale=norm(logs);after_scale=norm(logs+math.log(.5))
    assert torch.allclose(before_scale,after_scale,rtol=1e-13,atol=1e-13)
    normalization={'scales_before':before_scale.tolist(),'scales_after_common_log_shift':after_scale.tolist(),
                   'meaning':'norm_pw_scale=True cancels a common pair log-scale shift; not proof that this is a correct metric calibration.'}
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
    result={'status':'PASS_ARTIFICIAL_MATH_AND_HELPER_CHECKS_ONLY','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha256':hashlib.sha256(raw).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'autograd_from_exact_extracted_source_helpers':gradient,'common_center_homogeneity':homogeneity,
            'fixed_old_depth_breaks_full_scaling':fixed_old,'short_nonzero_baseline_counterexample':nonzero,'normalization_check':normalization,
            'true_model_runs':0,'GA_runs':0,'optimizer_steps':0,'sensor_GT_reads':0,'true_output_array_reads':0,
            'scope':'Small deterministic artificial tensors; no claim of observed collapse or of any real run gradient history.'}
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
