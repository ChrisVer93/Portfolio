/* Original local solid-model viewer. No libraries, network requests or CAD kernel.
 * Orthographic projection, triangle depth buffer, ray picking, box subtraction,
 * cut caps, and display-only winding envelopes. SI model coordinates.
 */
(function(root){
'use strict';
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0), sub=(a,b)=>a.map((v,i)=>v-b[i]), add=(a,b)=>a.map((v,i)=>v+b[i]), mul=(a,s)=>a.map(v=>v*s);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>{const n=Math.hypot(...a)||1;return a.map(x=>x/n);};
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const rgb=s=>/^#[0-9a-f]{6}$/i.test(s||'')?[1,3,5].map(i=>parseInt(s.slice(i,i+2),16)):[114,136,158];
const key=b=>['x0','x1','y0','y1','z0','z1'].map(k=>b[k]);
const valid=b=>['x','y','z'].every(a=>Number.isFinite(b[a+'0'])&&Number.isFinite(b[a+'1'])&&b[a+'1']>b[a+'0']);
function corners(b){return [[b.x0,b.y0,b.z0],[b.x1,b.y0,b.z0],[b.x1,b.y1,b.z0],[b.x0,b.y1,b.z0],[b.x0,b.y0,b.z1],[b.x1,b.y0,b.z1],[b.x1,b.y1,b.z1],[b.x0,b.y1,b.z1]];}
function boxFaces(b){const p=corners(b);return [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]].map(ids=>({points:ids.map(i=>p[i])}));}
function subtractBox(a,b){
 const c={};for(const x of ['x','y','z']){c[x+'0']=Math.max(a[x+'0'],b[x+'0']);c[x+'1']=Math.min(a[x+'1'],b[x+'1']);}
 if(!valid(c))return [a];
 const out=[],push=b=>{if(valid(b))out.push(b);};
 push({...a,x1:c.x0});push({...a,x0:c.x1});
 const m={...a,x0:c.x0,x1:c.x1};push({...m,y1:c.y0});push({...m,y0:c.y1});
 const q={...m,y0:c.y0,y1:c.y1};push({...q,z1:c.z0});push({...q,z0:c.z1});return out;
}
function ringBoxes(o,i){return [{...o,y1:i.y0},{...o,y0:i.y1},{...o,x1:i.x0,y0:i.y0,y1:i.y1},{...o,x0:i.x1,y0:i.y0,y1:i.y1}].filter(valid);}
function ringFaces(o,i){
 const a=corners(o),b=corners({...i,z0:o.z0,z1:o.z1}),out=[];
 for(let k=0;k<4;k++){const j=(k+1)%4;out.push({points:[a[k+4],a[j+4],b[j+4],b[k+4]]},{points:[a[j],a[k],b[k],b[j]]},{points:[a[k],a[j],a[j+4],a[k+4]]},{points:[b[j],b[k],b[k+4],b[j+4]]});}return out;
}
function clipPolygon(points,plane){
 if(plane===null)return points;
 const out=[];for(let j=0;j<points.length;j++){const p=points[j],q=points[(j+1)%points.length],a=p[1]>=plane-1e-13,b=q[1]>=plane-1e-13;
  if(a)out.push(p);if(a!==b){const t=(plane-p[1])/(q[1]-p[1]);out.push(p.map((x,k)=>x+t*(q[k]-x)));}}
 const clean=[];for(const p of out)if(!clean.length||Math.hypot(...sub(p,clean[clean.length-1]))>1e-13)clean.push(p);if(clean.length>1&&Math.hypot(...sub(clean[0],clean[clean.length-1]))<1e-13)clean.pop();return clean;
}
function rayBox(origin,dir,b){let lo=-Infinity,hi=Infinity;for(let k=0;k<3;k++){const a='xyz'[k];if(Math.abs(dir[k])<1e-14){if(origin[k]<b[a+'0']||origin[k]>b[a+'1'])return null;}else{let u=(b[a+'0']-origin[k])/dir[k],v=(b[a+'1']-origin[k])/dir[k];if(u>v)[u,v]=[v,u];lo=Math.max(lo,u);hi=Math.min(hi,v);if(lo>hi)return null;}}return hi>=Math.max(lo,0)?Math.max(lo,0):null;}
function modelFromProject(project){
 if(project.mode!=='3d')throw Error('Solid view requires a 3D project');
 const mats=new Map(project.materials.map(m=>[m.id,m]));let pieces=[];
 for(const r of project.regions||[]){if(!valid(r))continue;pieces=pieces.flatMap(old=>subtractBox(old.bounds,r).map(bounds=>({...old,bounds})));
  if(r.material!=='air'){const m=mats.get(r.material)||{};pieces.push({id:r.id,kind:'regions',name:r.name||r.id,role:(m.mu_r||1)>1?'core':'material',color:rgb(m.color),bounds:{...r},shape:'box',source:r});}
  if(pieces.length>3000)throw Error('Solid display partition is too complex; simplify overlapping boxes');
 }
 const solidPoints=pieces.flatMap(p=>corners(p.bounds));
 const sourcePoints=(project.windings||[]).flatMap(w=>valid(w.window)?corners(w.window):[]);
 const all=[...solidPoints,...sourcePoints];if(!all.length)all.push([0,0,0],[project.domain.width,project.domain.height,project.domain.depth]);
 const bounds={};for(let k=0;k<3;k++){bounds['xyz'[k]+'0']=Math.min(...all.map(p=>p[k]));bounds['xyz'[k]+'1']=Math.max(...all.map(p=>p[k]));}
 const span=Math.max(...['x','y','z'].map(a=>bounds[a+'1']-bounds[a+'0']));
 const gaps=(project.regions||[]).filter(r=>r.material==='air'&&/gap/i.test(r.id+' '+r.name));
 const split=gaps.length?(gaps[0].z0+gaps[0].z1)/2:(bounds.z0+bounds.z1)/2;
 // Visual split at the E-half mating plane; material occupancy is unchanged.
 pieces=pieces.flatMap(p=>p.role==='core'&&p.bounds.z0<split-1e-12&&p.bounds.z1>split+1e-12?[{...p,bounds:{...p.bounds,z1:split},half:-1},{...p,bounds:{...p.bounds,z0:split},half:1}]:[{...p,half:(p.bounds.z0+p.bounds.z1)/2<split?-1:1}]);
 const windings=[];
 for(let index=0;index<(project.windings||[]).length;index++){
  const w=project.windings[index],win=w.window;if(!valid(win))continue;
  const explicit=Number.isFinite(w.display_build_m)&&w.display_build_m>0;
  const build=explicit?w.display_build_m:Math.min(win.x1-win.x0,win.y1-win.y0)*.035;
  const maxBuild=.45*Math.min(win.x1-win.x0,win.y1-win.y0),b=Math.min(build,maxBuild);
  const outer={...win,x0:win.x0-b/2,x1:win.x1+b/2,y0:win.y0-b/2,y1:win.y1+b/2},inner={...win,x0:win.x0+b/2,x1:win.x1-b/2,y0:win.y0+b/2,y1:win.y1-b/2};
  const color=rgb(w.display_color||(/secondary/i.test(w.id)?'#bf7448':index%2?'#ce884a':'#e1a16a'));
  windings.push({id:w.id,kind:'windings',role:'winding',name:w.name||w.id,color,bounds:outer,inner,shape:'ring',source:w,displayBuild:b,explicitBuild:explicit,index});
 }
 const bodies=[...pieces,...windings];const pts=bodies.flatMap(p=>corners(p.bounds));
 if(pts.length)for(let k=0;k<3;k++){bounds['xyz'[k]+'0']=Math.min(...pts.map(p=>p[k]));bounds['xyz'[k]+'1']=Math.max(...pts.map(p=>p[k]));}
 return {bodies,bounds,span,split,project};
}

class MagneticsCAD{
 constructor(canvas,options={}){
  this.canvas=canvas;this.ctx=canvas.getContext('2d',{alpha:false});this.onSelect=options.onSelect||(()=>{});this.onStatus=options.onStatus||(()=>{});
  this.options={coreOpacity:1,windingOpacity:1,showWindings:true,showSources:false,showDomain:false,edges:true,section:false,sectionPosition:.5,explode:0,labels:true,...options};
  this.camera={yaw:-.72,pitch:.55,zoom:1,pan:[0,0]};this.hidden=new Set();this.selection=null;this.isolated=null;this.project=null;this.width=900;this.height=650;this.pointers=new Map();this.pending=false;
  this.bind();if(typeof ResizeObserver!=='undefined'){this.observer=new ResizeObserver(()=>this.resize());this.observer.observe(canvas);}this.resize();
 }
 setProject(project){const signature=JSON.stringify(project);if(signature!==this.signature){this.model=modelFromProject(project);this.project=project;this.signature=signature;if(!this.hasFitted){this.fit(false);this.hasFitted=true;}}this.requestRender();return this;}
 setOptions(values){Object.assign(this.options,values);this.requestRender();return this;}
 setSelection(selection){this.selection=selection;this.requestRender();}
 hide(id,hidden=true){hidden?this.hidden.add(id):this.hidden.delete(id);this.requestRender();}
 isolate(id){this.isolated=id||null;this.requestRender();}
 showAll(){this.hidden.clear();this.isolated=null;this.requestRender();}
 preset(name){const values={iso:[-.72,.55],front:[0,0],back:[Math.PI,0],right:[-Math.PI/2,0],left:[Math.PI/2,0],top:[0,Math.PI/2],bottom:[0,-Math.PI/2]};const v=values[name]||values.iso;this.camera.yaw=v[0];this.camera.pitch=v[1];this.fit();}
 fit(render=true){this.camera.zoom=1;this.camera.pan=[0,0];if(render)this.requestRender();}
 resize(){const r=this.canvas.getBoundingClientRect();if(r.width>0&&r.height>0){this.width=r.width;this.height=r.height;}this.dpr=Math.min(1.25,root.devicePixelRatio||1);this.canvas.width=Math.round(this.width*this.dpr);this.canvas.height=Math.round(this.height*this.dpr);this.requestRender();}
 basis(){const {yaw:y,pitch:p}=this.camera;return {r:[Math.cos(y),-Math.sin(y),0],u:[Math.sin(y)*Math.sin(p),Math.cos(y)*Math.sin(p),Math.cos(p)],n:[-Math.sin(y)*Math.cos(p),-Math.cos(y)*Math.cos(p),Math.sin(p)]};}
 projectPoint(p){const q=sub(p,this.origin);return [this.width/2+this.camera.pan[0]+dot(q,this.axes.r)*this.scale,this.height/2+this.camera.pan[1]-dot(q,this.axes.u)*this.scale,dot(q,this.axes.n)];}
 offsetBody(body){const e=clamp(this.options.explode,0,1)*this.model.span;let delta=[0,0,0];
  if(body.role==='core')delta=[0,0,body.half*e*.22];
  if(body.role==='winding')delta=[0,0,0];
  const shift=b=>({...b,x0:b.x0+delta[0],x1:b.x1+delta[0],y0:b.y0+delta[1],y1:b.y1+delta[1],z0:b.z0+delta[2],z1:b.z1+delta[2]});
  return {...body,bounds:shift(body.bounds),inner:body.inner?shift(body.inner):null};
 }
 visibleBodies(){if(!this.model)return [];return this.model.bodies.filter(b=>!this.hidden.has(b.id)&&(!this.isolated||b.id===this.isolated)&&(b.role!=='winding'||this.options.showWindings)).map(b=>this.offsetBody(b));}
 facesFor(body,plane){
  let faces=body.shape==='ring'?ringFaces(body.bounds,body.inner):boxFaces(body.bounds);
  faces=faces.filter(f=>plane===null||!f.points.every(p=>Math.abs(p[1]-plane)<1e-12)||cross(sub(f.points[1],f.points[0]),sub(f.points[2],f.points[0]))[1]<=0).map(f=>({...f,points:clipPolygon(f.points,plane)})).filter(f=>f.points.length>=3);
  if(plane!==null&&plane>body.bounds.y0+1e-12&&plane<body.bounds.y1-1e-12){
   let segments=[[body.bounds.x0,body.bounds.x1]];
   if(body.shape==='ring'&&plane>=body.inner.y0-1e-12&&plane<=body.inner.y1+1e-12)segments=[[body.bounds.x0,body.inner.x0],[body.inner.x1,body.bounds.x1]];
   for(const [x0,x1]of segments)faces.push({cap:true,points:[[x0,plane,body.bounds.z0],[x1,plane,body.bounds.z0],[x1,plane,body.bounds.z1],[x0,plane,body.bounds.z1]]});
  }
  return faces.map(f=>({...f,body,opacity:body.role==='core'?this.options.coreOpacity:body.role==='winding'?this.options.windingOpacity:1}));
 }
 requestRender(){if(this.pending)return;this.pending=true;const schedule=root.requestAnimationFrame||((fn)=>setTimeout(fn,0));schedule(()=>{this.pending=false;this.render();});}
 render(){
  if(!this.model)return;
  const bodies=this.visibleBodies();this.axes=this.basis();let all=(bodies.length?bodies:this.model.bodies).flatMap(b=>corners(b.bounds));if(!all.length)all=corners(this.model.bounds);if(this.viewBounds)all=corners(this.viewBounds);
  this.origin=[0,1,2].map(k=>(Math.min(...all.map(p=>p[k]))+Math.max(...all.map(p=>p[k])))/2);
  const xy=all.map(p=>[dot(sub(p,this.origin),this.axes.r),dot(sub(p,this.origin),this.axes.u)]);
  const sx=Math.max(...xy.map(p=>p[0]))-Math.min(...xy.map(p=>p[0])),sy=Math.max(...xy.map(p=>p[1]))-Math.min(...xy.map(p=>p[1]));
  this.scale=Math.min((this.width-95)/(sx||1),(this.height-125)/(sy||1))*this.camera.zoom;
  const b=this.model.bounds;this.cutPlane=this.options.section?b.y0+(b.y1-b.y0)*clamp(this.options.sectionPosition,.001,.999):null;
  const w=this.canvas.width,h=this.canvas.height,count=w*h;
  if(!this.image||this.image.width!==w||this.image.height!==h){this.image=this.ctx.createImageData(w,h);this.depth=new Float32Array(count);}
  const data=this.image.data;this.depth.fill(-Infinity);
  for(let y=0;y<h;y++){const t=y/h;for(let x=0;x<w;x++){const i=4*(x+w*y);data[i]=Math.round(17-5*t);data[i+1]=Math.round(27-7*t);data[i+2]=Math.round(42-9*t);data[i+3]=255;}}
  const faces=bodies.flatMap(body=>this.facesFor(body,this.cutPlane)).filter(f=>f.opacity>.003);
  const opaque=[],transparent=[];
  const light=norm([-.45,-.7,1]);
  for(const f of faces){const n=norm(cross(sub(f.points[1],f.points[0]),sub(f.points[2],f.points[0])));f.normal=n;const facing=dot(n,this.axes.n);if(f.opacity>=.995&&facing<1e-10)continue;
   f.points2=f.points.map(p=>this.projectPoint(p));f.depth=f.points2.reduce((s,p)=>s+p[2],0)/f.points2.length;
   let shade=.45+.35*Math.max(0,dot(n,light))+.2*Math.max(0,facing);let base=f.cap?(f.body.role==='core'?[137,167,188]:[226,171,112]):f.body.color;
   if(this.selection&&f.body.id===this.selection.id&&f.body.kind===this.selection.kind)base=base.map((v,i)=>v*.6+[84,179,255][i]*.4);
   f.color=base.map(v=>Math.round(clamp(v*shade,0,255)));(f.opacity>=.995?opaque:transparent).push(f);
  }
  // Orthographic opaque geometry uses a true per-pixel depth buffer.
  for(const f of opaque)this.drawFace(f,true);
  if(this.drawFieldSurfaces)this.drawFieldSurfaces();
  transparent.sort((a,b)=>a.depth-b.depth);for(const f of transparent)this.drawFace(f,false);
  if(this.options.edges)for(const f of [...opaque,...transparent]){const selected=this.selection&&f.body.id===this.selection.id&&f.body.kind===this.selection.kind,col=selected?[129,207,255]:f.cap?[245,204,132]:[38,50,64];for(let j=0;j<f.points2.length;j++)this.drawLine(f.points2[j],f.points2[(j+1)%f.points2.length],col,selected?.95:.68,selected?1.5:.8);}
  if(this.options.showSources)for(const winding of this.project.windings||[]){
   if(this.hidden.has(winding.id)||this.isolated&&this.isolated!==winding.id)continue;
   const win=winding.window;for(const fraction of [0,.5,1]){const z=win.z0+(win.z1-win.z0)*fraction;let pts=[[win.x0,win.y0,z],[win.x1,win.y0,z],[win.x1,win.y1,z],[win.x0,win.y1,z]];pts=clipPolygon(pts,this.cutPlane);for(let j=0;j<pts.length;j++)this.drawLine(this.projectPoint(pts[j]),this.projectPoint(pts[(j+1)%pts.length]),[122,219,242],.9,1.3,true);}
  }
  if(this.options.showDomain){const d=this.project.domain;for(const f of boxFaces({x0:0,x1:d.width,y0:0,y1:d.height,z0:0,z1:d.depth})){const p=f.points.map(x=>this.projectPoint(x));for(let j=0;j<p.length;j++)this.drawLine(p[j],p[(j+1)%p.length],[88,119,151],.45,.7,true);}}
  if(this.drawField)this.drawField();
  this.ctx.putImageData(this.image,0,0);this.ctx.setTransform(this.dpr,0,0,this.dpr,0,0);this.drawOverlay(bodies);
  this.lastFaces=faces;this.onStatus({faces:faces.length,bodies:bodies.length,sectionY:this.cutPlane,explode:this.options.explode});
 }
 drawFace(f,writeDepth){for(let k=1;k<f.points2.length-1;k++)this.triangle(f.points2[0],f.points2[k],f.points2[k+1],f.color,f.opacity,writeDepth);}
 triangle(a,b,c,color,alpha,writeDepth){
  const d=this.dpr;a=[a[0]*d,a[1]*d,a[2]];b=[b[0]*d,b[1]*d,b[2]];c=[c[0]*d,c[1]*d,c[2]];
  const area=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);if(Math.abs(area)<1e-10)return;
  const w=this.canvas.width,h=this.canvas.height,x0=Math.max(0,Math.floor(Math.min(a[0],b[0],c[0]))),x1=Math.min(w-1,Math.ceil(Math.max(a[0],b[0],c[0]))),y0=Math.max(0,Math.floor(Math.min(a[1],b[1],c[1]))),y1=Math.min(h-1,Math.ceil(Math.max(a[1],b[1],c[1])));
  const inv=1/area,ax=(b[1]-c[1])*inv,ay=(c[0]-b[0])*inv,bx=(c[1]-a[1])*inv,by=(a[0]-c[0])*inv;
  for(let y=y0;y<=y1;y++){let u=ax*(x0+.5-c[0])+ay*(y+.5-c[1]),v=bx*(x0+.5-c[0])+by*(y+.5-c[1]);for(let x=x0;x<=x1;x++,u+=ax,v+=bx){const q=1-u-v;if(u>=-1e-8&&v>=-1e-8&&q>=-1e-8){const z=u*a[2]+v*b[2]+q*c[2],i=x+w*y;if(z>=this.depth[i]-1e-8){const p=i*4;for(let k=0;k<3;k++)this.image.data[p+k]=writeDepth?color[k]:Math.round(this.image.data[p+k]*(1-alpha)+color[k]*alpha);if(writeDepth)this.depth[i]=z;}}}}
 }
 drawLine(a,b,color,alpha,width=1,xray=false){const ratio=this.dpr,dx=(b[0]-a[0])*ratio,dy=(b[1]-a[1])*ratio,steps=Math.max(1,Math.ceil(Math.hypot(dx,dy))),w=this.canvas.width,h=this.canvas.height,r=width>1.2?1:0;
  for(let j=0;j<=steps;j++){const t=j/steps,x=Math.round(a[0]*ratio+dx*t),y=Math.round(a[1]*ratio+dy*t),z=a[2]+(b[2]-a[2])*t;
   for(let v=-r;v<=r;v++)for(let u=-r;u<=r;u++){const xx=x+u,yy=y+v;if(xx<0||yy<0||xx>=w||yy>=h)continue;const i=xx+w*yy;if(xray||z>=this.depth[i]-this.model.span*.0015){const p=i*4;for(let k=0;k<3;k++)this.image.data[p+k]=Math.round(this.image.data[p+k]*(1-alpha)+color[k]*alpha);}}}
 }
 drawOverlay(bodies){const c=this.ctx,w=this.width,h=this.height;c.font='11px sans-serif';c.fillStyle='#a9bfd8';c.fillText('3D SOLID MODEL  /  mm',20,25);c.font='10px sans-serif';c.fillStyle='#6f89a8';c.fillText('Drag to rotate · Shift-drag to pan · Scroll / pinch to zoom · Click to inspect',20,44);
  const bb=this.model.bounds;c.fillStyle='#8ea8c4';c.fillText('Envelope '+['x','y','z'].map(a=>((bb[a+'1']-bb[a+'0'])*1000).toFixed(1)).join(' × ')+' mm',20,h-38);
  c.fillText(this.options.explode>.001?'Exploded display — solver coordinates unchanged':this.cutPlane!==null?'Cutaway at Y = '+(this.cutPlane*1000).toFixed(2)+' mm — display only':'Assembled geometry · Orthographic camera',20,h-20);
  const o=[w-62,h-64],axes=[[1,0,0],[0,1,0],[0,0,1]],colors=['#ed9785','#8fcdb2','#88b6f2'];
  axes.forEach((a,i)=>{const dx=dot(a,this.axes.r)*32,dy=-dot(a,this.axes.u)*32;c.strokeStyle=colors[i];c.lineWidth=1.8;c.beginPath();c.moveTo(...o);c.lineTo(o[0]+dx,o[1]+dy);c.stroke();c.fillStyle=colors[i];c.fillText('XYZ'[i],o[0]+dx+4,o[1]+dy+3);});
  if(this.selection&&this.options.labels){const bs=bodies.filter(b=>b.id===this.selection.id&&b.kind===this.selection.kind);if(bs.length){const b=bs[0],q=this.projectPoint([(b.bounds.x0+b.bounds.x1)/2,(b.bounds.y0+b.bounds.y1)/2,b.bounds.z1]);const text=b.name;c.font='11px sans-serif';const tw=c.measureText(text).width;c.fillStyle='#17384be8';c.fillRect(clamp(q[0]-tw/2-8,5,w-tw-20),clamp(q[1]-27,48,h-90),tw+16,22);c.fillStyle='#b5e3ff';c.fillText(text,clamp(q[0]-tw/2,13,w-tw-12),clamp(q[1]-12,63,h-75));}}
 }
 pick(x,y){if(!this.model||!this.axes)return null;const screen=[(x-this.width/2-this.camera.pan[0])/this.scale,-(y-this.height/2-this.camera.pan[1])/this.scale];const origin=add(add(add(this.origin,mul(this.axes.r,screen[0])),mul(this.axes.u,screen[1])),mul(this.axes.n,this.model.span*6));const direction=mul(this.axes.n,-1);let best=null,dist=Infinity;
  for(const body of this.visibleBodies()){const opacity=body.role==='core'?this.options.coreOpacity:this.options.windingOpacity;if(opacity<.04)continue;
   const boxes=body.shape==='ring'?ringBoxes(body.bounds,body.inner):[body.bounds];for(let b of boxes){if(this.cutPlane!==null)b={...b,y0:Math.max(b.y0,this.cutPlane)};if(!valid(b))continue;const t=rayBox(origin,direction,b);if(t!==null&&t<dist){best=body;dist=t;}}}
  return best?{id:best.id,kind:best.kind,name:best.name,role:best.role,source:best.source,displayBuild:best.displayBuild,explicitBuild:best.explicitBuild}:null;
 }
 bind(){const c=this.canvas;c.style.touchAction='none';const point=e=>{const r=c.getBoundingClientRect();return [e.clientX-r.left,e.clientY-r.top];};
  c.addEventListener('pointerdown',e=>{c.setPointerCapture(e.pointerId);const p=point(e);this.pointers.set(e.pointerId,p);if(this.pointers.size===2){const a=[...this.pointers.values()];this.pinch={distance:Math.hypot(a[1][0]-a[0][0],a[1][1]-a[0][1]),zoom:this.camera.zoom};}else this.drag={start:p,point:p,yaw:this.camera.yaw,pitch:this.camera.pitch,pan:this.camera.pan.slice(),moved:0,panMode:e.shiftKey||e.button===1||e.button===2};});
  c.addEventListener('pointermove',e=>{if(!this.pointers.has(e.pointerId))return;const p=point(e);this.pointers.set(e.pointerId,p);if(this.pointers.size>=2&&this.pinch){const a=[...this.pointers.values()];this.camera.zoom=clamp(this.pinch.zoom*Math.hypot(a[1][0]-a[0][0],a[1][1]-a[0][1])/Math.max(1,this.pinch.distance),.15,12);if(this.drag)this.drag.moved=99;}else if(this.drag){const g=this.drag,dx=p[0]-g.start[0],dy=p[1]-g.start[1];g.moved=Math.max(g.moved,Math.hypot(dx,dy));if(g.panMode)this.camera.pan=[g.pan[0]+dx,g.pan[1]+dy];else{this.camera.yaw=g.yaw+dx*.009;this.camera.pitch=clamp(g.pitch+dy*.009,-Math.PI/2,Math.PI/2);}}this.requestRender();});
  c.addEventListener('pointerup',e=>{const g=this.drag;if(this.pointers.size===1&&g&&g.moved<4){const p=point(e),hit=this.pick(...p);this.selection=hit;this.onSelect(hit);}this.pointers.delete(e.pointerId);this.drag=null;this.pinch=null;this.requestRender();});
  c.addEventListener('pointercancel',e=>{this.pointers.delete(e.pointerId);this.drag=null;this.pinch=null;});
  c.addEventListener('wheel',e=>{e.preventDefault();this.camera.zoom=clamp(this.camera.zoom*Math.exp(-e.deltaY*.001),.15,12);this.requestRender();},{passive:false});
  c.addEventListener('dblclick',()=>this.fit());c.addEventListener('contextmenu',e=>e.preventDefault());
 }
 exportOBJ(){const lines=['# Magnetics Studio solid display geometry','# Units: millimetres. Winding volumes are display envelopes, not solved copper.'];let index=1;
  for(const b of this.model.bodies){const faces=b.shape==='ring'?ringFaces(b.bounds,b.inner):boxFaces(b.bounds);lines.push('g '+b.id.replace(/[^a-zA-Z0-9_-]/g,'_'));for(const f of faces){for(const p of f.points)lines.push('v '+p.map(v=>(v*1000).toPrecision(12)).join(' '));lines.push('f '+f.points.map((_,i)=>index+i).join(' '));index+=f.points.length;}}
  return lines.join('\n')+'\n';
 }
 destroy(){if(this.observer)this.observer.disconnect();}
}
MagneticsCAD.geometry={modelFromProject,subtractBox,boxFaces,ringFaces,ringBoxes,clipPolygon,rayBox,corners};root.MagneticsCAD=MagneticsCAD;
})(typeof globalThis!=='undefined'?globalThis:window);
