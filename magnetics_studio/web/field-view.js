/* 3D postprocessing of actual tetrahedral FEM fields. No network/dependencies.
 * Fields are constant within lowest-order edge-element tetrahedra. Paths use
 * normalized midpoint integration of those values; no averaging across media.
 */
(function(root){
'use strict';
const sub=(a,b)=>a.map((x,k)=>x-b[k]),add=(a,b)=>a.map((x,k)=>x+b[k]),mul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((s,x,k)=>s+x*b[k],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],mag=a=>Math.hypot(...a),unit=a=>mul(a,1/(mag(a)||1));
const edges=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]],faceIds=[[0,2,1],[0,1,3],[0,3,2],[1,2,3]];
function colour(t){t=Math.max(0,Math.min(1,t));const stops=[[56,58,160],[28,129,213],[28,194,179],[151,219,87],[255,213,67],[239,70,62]],u=t*5,i=Math.min(4,Math.floor(u)),v=u-i;return stops[i].map((x,k)=>Math.round(x*(1-v)+stops[i+1][k]*v));}
function interval(g,x){if(x<g[0]-1e-12||x>g[g.length-1]+1e-12)return -1;let lo=0,hi=g.length-1;while(hi-lo>1){const mid=(lo+hi)>>1;if(x<g[mid])hi=mid;else lo=mid;}return Math.min(lo,g.length-2);}
class FieldVolume{
 constructor(result){
  this.result=result;this.mesh=result.mesh;const m=this.mesh;if(m.dimension!==3)throw Error('A tetrahedral 3D result is required');
  if(result.fields.B.length!==m.elements.length)throw Error('Field/element count mismatch');
  this.core=m.tags.map(t=>t>=0&&(result.project.materials.find(x=>x.id===result.project.regions[t].material)?.mu_r||1)>1);
  this.maxB=Math.max(...result.fields.B.map(mag));this.maxH=Math.max(...result.fields.H.map(mag));
  this.grids=m.grids||[0,1,2].map(k=>{const a=Math.min(...m.nodes.map(p=>p[k])),b=Math.max(...m.nodes.map(p=>p[k]));return Array.from({length:19},(_,i)=>a+(b-a)*i/18);});
  this.bins=new Map();this.tets=[];this.surface=null;
  this.step=Math.min(...this.grids.flatMap(g=>g.slice(1).map((v,i)=>v-g[i])))*.28;
  this.span=Math.max(...this.grids.map(g=>g[g.length-1]-g[0]));
  this.step=Math.max(this.step,this.span/1500);
  for(let i=0;i<m.elements.length;i++){
   const ids=m.elements[i],p=ids.map(n=>m.nodes[n]),a=sub(p[1],p[0]),b=sub(p[2],p[0]),c=sub(p[3],p[0]),det=dot(a,cross(b,c));
   if(Math.abs(det)<1e-30)throw Error('Degenerate tetrahedron');
   const inv=[cross(b,c),cross(c,a),cross(a,b)].map(v=>mul(v,1/det));
   const low=[0,1,2].map(k=>Math.min(...p.map(q=>q[k]))),high=[0,1,2].map(k=>Math.max(...p.map(q=>q[k]))),center=[0,1,2].map(k=>p.reduce((s,q)=>s+q[k]/4,0));
   this.tets.push({p,inv,center,low,high});const l=low.map((x,k)=>interval(this.grids[k],x+1e-13)),h=high.map((x,k)=>interval(this.grids[k],x-1e-13));
   for(let x=l[0];x<=h[0];x++)for(let y=l[1];y<=h[1];y++)for(let z=l[2];z<=h[2];z++){const key=x+','+y+','+z;if(!this.bins.has(key))this.bins.set(key,[]);this.bins.get(key).push(i);}
  }
 }
 locate(p){const q=p.map((x,k)=>interval(this.grids[k],x));if(q.some(x=>x<0))return -1;const bucket=this.bins.get(q.join(','))||[];for(const i of bucket){const t=this.tets[i],v=sub(p,t.p[0]),w=t.inv.map(row=>dot(row,v));if(w.every(x=>x>=-1e-9)&&w.reduce((a,b)=>a+b,0)<=1+1e-9)return i;}return -1;}
 sample(p,quantity='B'){const i=this.locate(p);return i<0?null:{i,value:this.result.fields[quantity][i]};}
 boundary(){if(this.surface)return this.surface;const faces=new Map();for(let i=0;i<this.tets.length;i++){if(!this.core[i])continue;const ids=this.mesh.elements[i],t=this.tets[i];for(const f of faceIds){const key=f.map(j=>ids[j]).sort((a,b)=>a-b).join(',');if(faces.has(key))faces.delete(key);else{let points=f.map(j=>t.p[j]);if(dot(cross(sub(points[1],points[0]),sub(points[2],points[0])),sub(t.center,points[0]))>0)points=points.slice().reverse();faces.set(key,{points,i});}}}return this.surface=[...faces.values()];}
 caps(plane){const out=[];for(let i=0;i<this.tets.length;i++){if(!this.core[i])continue;const t=this.tets[i];if(t.low[1]>plane+1e-12||t.high[1]<=plane+1e-12)continue;const pts=[];const push=p=>{if(!pts.some(q=>mag(sub(p,q))<1e-11))pts.push(p);};for(const p of t.p)if(Math.abs(p[1]-plane)<1e-12)push(p);for(const [a,b]of edges){const p=t.p[a],q=t.p[b];if((p[1]<plane&&q[1]>plane)||(q[1]<plane&&p[1]>plane)){const f=(plane-p[1])/(q[1]-p[1]);push(add(p,mul(sub(q,p),f)));}}if(pts.length>=3){const center=[0,1,2].map(k=>pts.reduce((s,p)=>s+p[k]/pts.length,0));pts.sort((a,b)=>Math.atan2(a[2]-center[2],a[0]-center[0])-Math.atan2(b[2]-center[2],b[0]-center[0]));if(cross(sub(pts[1],pts[0]),sub(pts[2],pts[0]))[1]>0)pts.reverse();out.push({points:pts,i});}}return out;}
 glyphs(scope='core',density=11){const seen=new Set(),out=[];for(let i=0;i<this.tets.length;i++){if(scope==='core'&&!this.core[i])continue;const p=this.tets[i].center,key=p.map((x,k)=>Math.floor((x-this.grids[k][0])/this.span*density)).join(',');if(!seen.has(key)){seen.add(key);out.push({p,i});}}return out;}
 seeds(count=32){
  // Prefer cross sections of long axial magnetic members; seeds fill X AND Y.
  const regs=this.result.project.regions.filter(r=>(this.result.project.materials.find(m=>m.id===r.material)?.mu_r||1)>1),long=regs.filter(r=>r.z1-r.z0>1.3*(r.x1-r.x0));
  const out=[];for(const r of (long.length?long:regs)){const n=Math.max(2,Math.round(Math.sqrt(count/Math.max(1,long.length||regs.length))));for(let a=0;a<n;a++)for(let b=0;b<n;b++){const p=[r.x0+(r.x1-r.x0)*(a+.5)/n,r.y0+(r.y1-r.y0)*(b+.5)/n,r.z0+(r.z1-r.z0)*.43];const s=this.sample(p);if(s&&this.core[s.i])out.push(p);}}
  return out.slice(0,120);
 }
 trace(seed,sign=1,maxSteps=1200){const path=[seed],visited=new Map();let p=seed;for(let j=0;j<maxSteps;j++){const s=this.sample(p);if(!s||mag(s.value)<this.maxB*1e-8)break;const h=this.step*sign,half=add(p,mul(unit(s.value),h/2)),mid=this.sample(half);if(!mid)break;const next=add(p,mul(unit(mid.value),h));if(!this.sample(next))break;const key=next.map(x=>Math.round(x/(this.step*2))).join(',');if(visited.has(key)&&j-visited.get(key)>40)break;if(!visited.has(key))visited.set(key,j);path.push(next);p=next;if(j>60&&mag(sub(p,seed))<this.step*1.7)break;}return path;}
 paths(count=32){return this.seeds(count).map(seed=>{const back=this.trace(seed,-1).reverse(),forward=this.trace(seed,1);return [...back.slice(0,-1),...forward];}).filter(p=>p.length>8);}
}
class MagneticsField3D extends root.MagneticsCAD{
 constructor(canvas,options={}){super(canvas,options);this.fieldOptions={surface:false,paths:true,vectors:true,scope:'core',density:20,quantity:'B',range:0,...options.fieldOptions};this.pathCache=null;}
 setResult(result){if(this.result===result)return this;this.result=result;this.volume=result?new FieldVolume(result):null;this.pathCache=null;this.capCache=null;this.setProject(result.project);return this;}
 setFieldOptions(values){Object.assign(this.fieldOptions,values);const d=this.project?.domain;this.viewBounds=this.fieldOptions.scope==='all'&&d?{x0:0,x1:d.width,y0:0,y1:d.height,z0:0,z1:d.depth}:null;this.requestRender();return this;}
 facesFor(body,plane){if(this.volume&&this.fieldOptions.surface&&body.role==='core')return [];return super.facesFor(body,plane);}
 drawFieldSurfaces(){
  if(!this.volume)return;const v=this.volume,o=this.fieldOptions,quantity=o.quantity==='H'?'H':'B';this.fieldMax=o.range>0?o.range:quantity==='B'?v.maxB:v.maxH;
  const visible=i=>{const tag=v.mesh.tags[i],reg=tag>=0?this.result.project.regions[tag]:null;return (!reg||!this.hidden.has(reg.id))&&(!this.isolated||reg?.id===this.isolated);};
  if(o.surface){let faces=v.boundary().map(f=>({...f,points:root.MagneticsCAD.geometry.clipPolygon(f.points,this.cutPlane)})).filter(f=>f.points.length>=3);if(this.cutPlane!==null){if(!this.capCache||this.capCache.plane!==this.cutPlane)this.capCache={plane:this.cutPlane,faces:v.caps(this.cutPlane)};faces=faces.concat(this.capCache.faces);}for(const f of faces){if(!visible(f.i))continue;const n=cross(sub(f.points[1],f.points[0]),sub(f.points[2],f.points[0]));if(dot(n,this.axes.n)<=0)continue;this.drawFace({points2:f.points.map(p=>this.projectPoint(p)),color:colour(mag(this.result.fields[quantity][f.i])/this.fieldMax),opacity:1},true);}}
 }
 drawField(){
  if(!this.volume)return;const v=this.volume,o=this.fieldOptions,quantity=o.quantity==='H'?'H':'B';this.fieldMax=o.range>0?o.range:quantity==='B'?v.maxB:v.maxH;
  const visible=i=>{const tag=v.mesh.tags[i],reg=tag>=0?this.result.project.regions[tag]:null;return (!reg||!this.hidden.has(reg.id))&&(!this.isolated||reg?.id===this.isolated);};

  if(o.paths){if(!this.pathCache||this.pathCache.density!==o.density)this.pathCache={density:o.density,paths:v.paths(o.density)};for(const path of this.pathCache.paths)for(let j=0;j<path.length-1;j+=2){let a=path[j],b=path[Math.min(j+2,path.length-1)];const s=v.sample(a);if(!s||!visible(s.i)||o.scope==='core'&&!v.core[s.i])continue;if(this.cutPlane!==null){if(a[1]<this.cutPlane&&b[1]<this.cutPlane)continue;if((a[1]<this.cutPlane)!==(b[1]<this.cutPlane)){const q=add(a,mul(sub(b,a),(this.cutPlane-a[1])/(b[1]-a[1])));if(a[1]<this.cutPlane)a=q;else b=q;}}this.drawLine(this.projectPoint(a),this.projectPoint(b),colour(mag(this.result.fields[quantity][s.i])/this.fieldMax),.84,1.3);}}
  if(o.vectors){const length=this.model.span*.035;for(const {p,i}of v.glyphs(o.scope,Math.round(8+o.density/5))){if(!visible(i)||this.cutPlane!==null&&p[1]<this.cutPlane)continue;const b=this.result.fields[quantity][i],strength=mag(b);if(strength<1e-8*(quantity==='B'?v.maxB:v.maxH))continue;const end=add(p,mul(unit(b),length)),a=this.projectPoint(p),q=this.projectPoint(end),col=colour(strength/this.fieldMax),dx=q[0]-a[0],dy=q[1]-a[1],l=Math.hypot(dx,dy);if(l<1)continue;this.drawLine(a,q,col,1,1.3);const ux=dx/l,uy=dy/l,s=4;this.drawLine(q,[q[0]-s*ux+s*.5*uy,q[1]-s*uy-s*.5*ux,q[2]],col,1,1.3);this.drawLine(q,[q[0]-s*ux-s*.5*uy,q[1]-s*uy+s*.5*ux,q[2]],col,1,1.3);}}
 }
 drawOverlay(bodies){super.drawOverlay(bodies);if(!this.volume)return;const c=this.ctx;c.fillStyle='#101b2c';c.fillRect(14,9,345,22);c.fillStyle='#c0d7ee';c.font='11px sans-serif';c.fillText('3D FEM FIELD  /  '+(this.fieldOptions.quantity==='H'?'|H| · A/m':'|B| · T'),20,25);const w=160,x=this.width-w-22,y=60;for(let j=0;j<w;j++){const col=colour(j/(w-1));c.fillStyle='rgb('+col.join(',')+')';c.fillRect(x+j,y,1,9);}c.fillStyle='#adc5df';c.font='10px sans-serif';c.fillText('0',x,y+24);c.fillText((this.fieldMax||0).toPrecision(4)+(this.fieldOptions.quantity==='H'?' A/m':' T'),x+w-68,y+24);c.fillText('Element values · linear scale',x,y-8);}
}
root.MagneticsField3D=MagneticsField3D;root.MagneticsFieldVolume=FieldVolume;root.magneticsFieldColour=colour;
})(typeof globalThis!=='undefined'?globalThis:window);
