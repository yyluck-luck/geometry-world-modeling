import argparse, json, tarfile

def rows(text):
 out=[]
 for line in text.splitlines():
  line=line.split('#',1)[0].strip()
  if line: out.append((float(line.split()[0]), line.split()[1]))
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--archive',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 with tarfile.open(a.archive,'r:gz') as tf:
  names=tf.getnames(); root=next(n.rsplit('/',1)[0] for n in names if n.endswith('/rgb.txt'))
  def read(n): return tf.extractfile(tf.getmember(root+'/'+n)).read().decode()
  rgb=rows(read('rgb.txt')); dep=rows(read('depth.txt'))
 tol=0.02; cand=[]
 for i,(tr,_) in enumerate(rgb):
  for j,(td,_) in enumerate(dep):
   d=abs(tr-td)
   if d<tol: cand.append((d,tr,td,i,j))
 cand.sort(key=lambda x:(x[0],x[1],x[2]))
 usedr=set(); usedd=set(); acc=[]
 for x in cand:
  if x[3] not in usedr and x[4] not in usedd:
   usedr.add(x[3]); usedd.add(x[4]); acc.append(x)
 rc=[0]*len(rgb); dc=[0]*len(dep)
 for _,_,_,i,j in cand: rc[i]+=1; dc[j]+=1
 result={'schema':'tum-fr3-pairing-contract-v1','tolerance_seconds':tol,'strict_less_than':True,'tie_order':['abs_difference','rgb_timestamp','depth_timestamp'],'one_to_one':True,'rgb_rows':len(rgb),'depth_rows':len(dep),'candidate_edges':len(cand),'accepted_pairs':len(acc),'dropped_rgb':len(rgb)-len(usedr),'dropped_depth':len(dep)-len(usedd),'depth_nodes_multiple_candidates':sum(v>1 for v in dc),'rgb_nodes_multiple_candidates':sum(v>1 for v in rc),'max_depth_candidates':max(dc or [0]),'max_rgb_candidates':max(rc or [0]),'duplicate_assigned_depth':len(usedd)-len(set(x[4] for x in acc))}
 with open(a.out,'w') as f: json.dump(result,f,indent=2)
 print(json.dumps(result,indent=2))
if __name__=='__main__': main()
