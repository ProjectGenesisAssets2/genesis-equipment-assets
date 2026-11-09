// Project Genesis — one repairable blacksmith workshop wall, isolated gameplay proof V001.
// Procedural 14-part reconstruction. No Ammo WASM or new texture downloads.
import {
  Entity as RepairEntity, Mesh as RepairMesh, MeshInstance as RepairMeshInstance,
  StandardMaterial as RepairStandardMaterial, Color as RepairColor,
  Vec3 as RepairVec3, calculateNormals
} from 'playcanvas';

const SAVE_KEY='genesis.preview.workshop-wall-repair.v001';
const WALL_X=-5.52*.75, WALL_Z=-5.05*.75;
const SECONDS=3.15;
const smooth=t=>t*t*t*(t*(t*6-15)+10);
const mix=(a,b,t)=>a+(b-a)*t;
const rnd=(a,b)=>{const x=Math.sin(a*92.61+b*31.7)*43758.5453;return x-Math.floor(x)};

function stoneGeometry(device,sx,sy,sz,seed) {
  const corners=[
    [-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
    [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]
  ].map(([x,y,z],i)=>{
    const chip=.07;
    return [x*sx*.5*(1-chip*rnd(seed,i)),y*sy*.5*(1-chip*rnd(seed+11,i)),
            z*sz*.5*(1-chip*rnd(seed+23,i))];
  });
  const faces=[[4,5,6,7],[1,0,3,2],[5,1,2,6],
               [0,4,7,3],[7,6,2,3],[0,1,5,4]];
  const positions=[],uvs=[],indices=[];
  faces.forEach((face,fi)=>{
    const k=positions.length/3;
    for(let j=0;j<4;j++){positions.push(...corners[face[j]]);uvs.push(j===1||j===2?1:0,j>=2?1:0)}
    indices.push(k,k+1,k+2,k,k+2,k+3);
  });
  const mesh=new RepairMesh(device);
  mesh.setPositions(positions);
  mesh.setNormals(calculateNormals(new Float32Array(positions),indices));
  mesh.setUvs(0,uvs);
  mesh.setIndices(indices);
  mesh.update();
  return mesh;
}
function findMaterial(modelEl,matcher) {
  const root=modelEl?.contentEntity;
  if(!root)return null;
  for(const r of root.findComponents('render')){
    for(const mi of r.meshInstances){
      if(mi.material && (!matcher||matcher(mi.material.name||'')))return mi.material;
    }
  }
  return null;
}
function makeVariants(source,fallback,wood=false){
  const shades=wood?[.86,1.00]:[.88,.96,1.03];
  return shades.map((v,i)=>{
    const m=source?.clone?.()||new RepairStandardMaterial();
    m.name=(wood?'Repair aged timber ':'Repair quarry-stone ')+i;
    if(!source){m.diffuse=new RepairColor(...fallback);m.gloss=wood?.18:.12;}
    else if(m.diffuse){m.diffuse.r*=v;m.diffuse.g*=v;m.diffuse.b*=v;}
    m.update();return m;
  });
}
function dustBurst(at,cam,layer){
  const c=cam?.component||document.querySelector('#cameraRig pc-camera')?.component;
  if(!c||!layer)return;
  // Project the fracture's world position with a real PlayCanvas Vec3.
  try{
    const position=new RepairVec3(at.x,at.y,at.z);
    const screen=c.worldToScreen(position);
    if(!screen||screen.z<=0)return;
    for(let i=0;i<7;i++){
      const el=document.createElement('i');el.className='genesisRepairDust';
      el.style.left=(screen.x-12+(rnd(i,2)-.5)*42)+'px';
      el.style.top=(screen.y-12+(rnd(i,3)-.5)*28)+'px';
      el.style.setProperty('--driftX',((rnd(i,4)-.5)*100)+'px');
      el.style.setProperty('--driftY',(-18-rnd(i,5)*55)+'px');
      layer.appendChild(el);
      setTimeout(()=>el.remove(),1100);
    }
  }catch(e){console.warn('Repair dust disabled',e)}
}
export function mountRepairableWorkshop({gameApp,root,notify,onDone,onImpact,cameraElement,fxLayer}) {
  if(!gameApp?.graphicsDevice||!root)throw Error('Repair needs live PlayCanvas root and graphics device');
  const oldPanel=document.querySelector('pc-model[name="Left wall middle"]');
  const source=findMaterial(oldPanel)||findMaterial(document.getElementById('workshopShellModel'));
  const shell=document.getElementById('workshopShellModel')?.contentEntity;
  const stone=makeVariants(source,[.28,.265,.24]);
  const timberSource=findMaterial(document.getElementById('workshopShellModel'),name=>/timber|wood/i.test(name));
  const timber=makeVariants(timberSource,[.15,.088,.04],true);
  const group=new RepairEntity('Genesis Repair V001 · left wall masonry reconstruction',gameApp);
  root.addChild(group);
  const hidden=[];
  const hide=node=>{if(node&&node.enabled){hidden.push(node);node.enabled=false}};
  // Remove the old authored mid-panel and the overlapping old shell courses.
  // All other walls / rafters / collisions remain unchanged.
  if(oldPanel?.entity)hide(oldPanel.entity);
  if(shell){
    for(const node of shell.findComponents('render').map(c=>c.entity)){
      if(!/^left\d+_\d+$/.test(node.name||''))continue;
      const bounds=node.render.meshInstances?.[0]?.aabb;
      const c=bounds?.center;
      if(c&&Math.abs(c.x-WALL_X)<.60&&Math.abs(c.z-WALL_Z)<1.22&&c.y<2.5)hide(node);
    }
  }
  const chunks=[];
  const layout=[];
  // 4 staggered rows of stone / 3 levels, along the long side of the room.
  for(let row=0;row<3;row++)for(let col=0;col<4;col++){
    const id=row*4+col;
    const z=WALL_Z+(col-1.5)*.52+(row%2?.06:-.03);
    const y=.36+row*.58;
    const sx=.26+.04*rnd(id,1),sy=.52+.06*rnd(id,2),sz=.47+.05*rnd(id,3);
    layout.push({id,z,y,sx,sy,sz,material:stone[id%stone.length],wood:false});
  }
  // Two structural braces return with the stones; they are NOT textured boxes.
  layout.push({id:12,z:WALL_Z-1.04,y:1.12,sx:.31,sy:2.16,sz:.19,material:timber[0],wood:true});
  layout.push({id:13,z:WALL_Z+1.04,y:1.12,sx:.31,sy:2.16,sz:.19,material:timber[1],wood:true});
  for(const p of layout){
    const obj=new RepairEntity((p.wood?'Recovered oak brace ':'Chipped quarry wall stone ')+p.id,gameApp);
    const mesh=stoneGeometry(gameApp.graphicsDevice,p.sx,p.sy,p.sz,p.id+79);
    obj.addComponent('render',{meshInstances:[new RepairMeshInstance(mesh,p.material)],
      castShadows:true,receiveShadows:true});
    group.addChild(obj);
    const end={x:WALL_X,y:p.y,z:p.z};
    const start={x:WALL_X+.40+rnd(p.id,9)*.55,
      y:p.wood ? .13+p.id*.015 : p.sy*.30,
      z:p.z+(rnd(p.id,10)-.5)*1.35};
    const angles={x:(rnd(p.id,11)-.5)*96,y:(rnd(p.id,12)-.5)*150,z:(rnd(p.id,13)-.5)*88};
    chunks.push({entity:obj,mesh,start,end,angles,
      startAt:.035*p.id,duration:p.wood?1.6:2.25});
    obj.setPosition(start.x,start.y,start.z);
    obj.setEulerAngles(angles.x,angles.y,angles.z);
  }
  let saved=false;
  try{saved=localStorage.getItem(SAVE_KEY)==='repaired'}catch(_){}
  let state=saved?'repaired':'rubble',clock=0;
  const previewHUD=document.getElementById('repairHudV001');
  const resetButton=document.getElementById('repairResetV001');
  const status=document.getElementById('repairStateV001');
  function setHUD(){
    if(previewHUD)previewHUD.hidden=false;
    if(status)status.textContent=state==='repaired'?'Pared consolidada':state==='moving'?'Reconstruyendo mampostería…':'Sección derrumbada · pared izquierda';
    if(resetButton)resetButton.disabled=state==='moving';
  }
  function applyEnd(){
    for(const c of chunks){c.entity.setPosition(c.end.x,c.end.y,c.end.z);c.entity.setEulerAngles(0,0,0)}
  }
  if(saved)applyEnd();
  function reset(){
    state='rubble';clock=0;
    try{localStorage.removeItem(SAVE_KEY)}catch(_){}
    for(const c of chunks){c.entity.setPosition(c.start.x,c.start.y,c.start.z);c.entity.setEulerAngles(c.angles.x,c.angles.y,c.angles.z)}
    setHUD();
    notify?.('Pared nuevamente derrumbada para repetir la prueba.',2300);
  }
  function repair(){
    if(state!=='rubble')return;
    state='moving';clock=0;setHUD();
    onImpact?.();
    notify?.('Consolidando piedras y vigas del taller…',2100);
  }
  if(resetButton)resetButton.onclick=reset;
  function update(dt){
    if(state!=='moving')return;
    clock+=Math.min(Math.max(dt,0),.06);
    for(const c of chunks){
      const t=Math.max(0,Math.min(1,(clock-c.startAt)/c.duration));
      const e=smooth(t);
      const p=c.start,q=c.end;
      const jump=Math.sin(Math.PI*t)*.34;
      c.entity.setPosition(mix(p.x,q.x,e),mix(p.y,q.y,e)+jump,mix(p.z,q.z,e));
      c.entity.setEulerAngles((1-e)*c.angles.x,(1-e)*c.angles.y,(1-e)*c.angles.z);
    }
    if(clock>=SECONDS){
      state='repaired';applyEnd();setHUD();
      try{localStorage.setItem(SAVE_KEY,'repaired')}catch(_){}
      onDone?.();
      if(cameraElement)dustBurst({x:WALL_X,y:1.15,z:WALL_Z},cameraElement,fxLayer);
      notify?.('Pared reconstruida. La colisión volvió a su lugar.',2800);
    }
  }
  const action={
    id:'repairWallV001',radius:2.25,
    prompt:()=>state==='moving'?'Reconstruyendo…':'Recomponer pared derrumbada',
    position:()=>({x:WALL_X+.78,y:1.06,z:WALL_Z}),
    interact:repair
  };
  function isOpenAt(x,z){
    return state!=='repaired'&&Math.abs(x-WALL_X)<.85&&Math.abs(z-WALL_Z)<1.02;
  }
  setHUD();
  const result={update,repair,reset,isOpenAt,action, get state(){return state;},
     get chunks(){return chunks.length;}, get hiddenShellPieces(){return hidden.length;},
     destroy(){resetButton&&(resetButton.onclick=null);group.destroy();hidden.forEach(n=>n.enabled=true);[...stone,...timber].forEach(m=>m.destroy?.())}};
  window.__genesisRepairPreview=result;
  return result;
}
