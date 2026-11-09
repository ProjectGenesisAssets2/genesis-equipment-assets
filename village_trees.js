/* Project Genesis v0.14c — approved foliage, warm bark, wind and geometry-accurate trunk collision.
 * Artwork: oak V017, ash V020, linden V022, burgundy maple V021.
 * The art masters are immutable. The v005 derivatives preserve ALL approved master geometry, plus native PNG/JPEG alpha.
 * 14 trunks over the 63x63-metre village: 4 in the plaza, 10 along the town and perimeter.
 */
import { Entity,Vec3,SHADERLANGUAGE_GLSL } from 'playcanvas';

const ORIGINALS = 'https://raw.githubusercontent.com/ProjectgenesisAssets/genesis-workshop-assets/94d2fe3262af163d9cd7277cc4e31e20acf3bcaa/';
const REPO = 'https://raw.githubusercontent.com/ProjectgenesisAssets/genesis-workshop-assets/1801cf9ac2394ac80bbe3f2d97dc00c8fd49e57d/';
const TYPES = Object.freeze({
 oak: { label: 'Roble', height: 9.1, master: 'assets/plaza_trees_v017/oak/oak_easytree_v017.glb' },
 ash: { label: 'Fresno', height: 9.7, master: 'assets/plaza_trees_v020/ash/ash_easytree_v020.glb' },
 linden: { label: 'Tilo', height: 8.7, master: 'assets/plaza_trees_v022/linden/linden_easytree_v022.glb' },
 maple: { label: 'Arce rojizo', height: 8.5, master: 'assets/plaza_trees_v021/maple/maple_easytree_v021.glb' }
});
// The square is deliberately one of each approved species. The other ten use a
// seeded shuffle: varied but stable across sessions so positions and collisions
// don't jump around on every page load.
const EXTERIOR_SPOTS = [
 [-19,-8,'sur'],[25,-8,'sur'],[-21,1,'oeste'],[-21,26,'oeste'],
 [-12,45,'norte'],[-3,45,'norte'],[35,44,'norte'],
 [22,6,'sur'],[-8,23,'oeste'],[19,24,'este']
];
function exteriorSpecies() {
 const pool=['oak','oak','ash','ash','ash','linden','linden','maple','maple','maple'];
 let seed=0x6a53c21d;
 for(let i=pool.length-1;i>0;i--){
  seed=(Math.imul(seed,1664525)+1013904223)>>>0;
  const j=seed%(i+1);
  [pool[i],pool[j]]=[pool[j],pool[i]];
 }
 return pool;
}
const EXTERIOR_SPECIES=exteriorSpecies();
const RAW_SITES = [
 // Shift southwest oak away from the fountain's light path, preserving trunk collision and shadows.
 ['oak',0.4,10.7,'plaza'],['maple',11.8,11.7,'plaza'],
 ['linden',2.2,20.3,'plaza'],['ash',11.8,20.3,'plaza'],
 ...EXTERIOR_SPOTS.map(([x,z,region],i)=>[EXTERIOR_SPECIES[i],x,z,region])
];
export const TREE_SITES = Object.freeze(RAW_SITES.map((item,index)=>Object.freeze({
 id: index+1, species: item[0], x:item[1], z:item[2], region:item[3],
 rotation: (index*137.508)%360, size: 0.90+((index*7)%9)*0.025,
 trunkRadius: 0.43 // safe fallback only; actual collision is derived from bark geometry
})));
// Applied only to the transparent botanical leaf cards. Bark, trunk and lower
// branches keep their original transforms. Shader motion costs no JS per leaf.
const WIND_TRANSFORM_VS=`
uniform float uGenesisWindTime;
uniform float uGenesisWindAmp;
uniform float uGenesisWindPhase;
vec4 evalWorldPosition(vec3 vertexPosition, mat4 modelMatrix) {
 vec3 localPos=getLocalPosition(vertexPosition);
 float t=uGenesisWindTime+uGenesisWindPhase;
 float height=smoothstep(1.1,4.8,localPos.y);
 float flutter=sin(t*1.45+localPos.x*1.31+localPos.z*.86);
 localPos.x+=height*uGenesisWindAmp*(flutter+.25*sin(t*.72+localPos.y*1.6));
 localPos.z+=height*uGenesisWindAmp*.62*sin(t*1.13+localPos.z*1.1-localPos.x*.77);
 return modelMatrix*vec4(localPos,1.0);
}
vec4 getPosition() {
 dModelMatrix=getModelMatrix();
 vec4 posW=evalWorldPosition(vertex_position.xyz,dModelMatrix);
 dPositionW=posW.xyz;
 return matrix_viewProjection*posW;
}
vec3 getWorldPosition(){return dPositionW;}
`;
function classifyAndTune(prototype,mobile,windMaterials) {
 const copies=new Map();
 const stack=[prototype];
 let bark=0,leaves=0;
 while(stack.length){
  const e=stack.pop();
  for(const child of e.children)stack.push(child);
  for(const mi of e.render?.meshInstances||[]){
   const src=mi.material;
   if(!src?.clone)continue;
   let m=copies.get(src);
   if(!m){
    const label=(src.name||'')+' '+(e.name||'');
    // GLB import assigns opacity maps even to opaque Bark materials.
    // Match the actual botanical material names / alpha cutoff, not opacityMap.
    const barkName=/bark|wood|trunk|corteza|twig|branch/i.test(label);
    const leaf=!barkName&&(/leaf|leaves|foliage|hoja|crown|canopy/i.test(label)
      || (src.alphaTest||0)>0.01);
    m=src.clone();
    if(leaf){
     m.getShaderChunks(SHADERLANGUAGE_GLSL).set('transformVS',WIND_TRANSFORM_VS);
     m.setParameter('uGenesisWindAmp',mobile?.040:.061);
     m.setParameter('uGenesisWindTime',0);
     m.setParameter('uGenesisWindPhase',0);
     windMaterials.add(m);leaves++;
    }else{
     // White sky bounce was washing brown trunks into gray. Keep the real
     // photographic albedo and normals; remove cool specular overexposure.
     const c=m.diffuse;
     if(c)c.set(c.r*.84,c.g*.70,c.b*.59);
     m.gloss=Math.min(m.gloss??.15,.12);
     if(m.specular)m.specular.set(.12,.095,.078);
     if(m.useMetalness)m.metalness=0;
     bark++;
    }
    m.update();copies.set(src,m);
   }
   mi.material=m;
  }
 }
 return {bark,leaves};
}

const assetPath = (species,lod) => lod===0
 ? ORIGINALS+TYPES[species].master
 : REPO+'assets/tree_webgl_v005/'+species+'/lod'+lod+'.glb';
function boundsOf(entity){
 const stack=[entity];let minX=Infinity,minY=Infinity,minZ=Infinity,maxX=-Infinity,maxY=-Infinity,maxZ=-Infinity;
 entity.syncHierarchy();
 while(stack.length){
  const node=stack.pop();
  for(const child of node.children)stack.push(child);
  const instances=node.render?.meshInstances || [];
  for(const mi of instances){
   const box=mi.aabb,center=box?.center,half=box?.halfExtents;
   if(!center||!half)continue;
   minX=Math.min(minX,center.x-half.x);minY=Math.min(minY,center.y-half.y);minZ=Math.min(minZ,center.z-half.z);
   maxX=Math.max(maxX,center.x+half.x);maxY=Math.max(maxY,center.y+half.y);maxZ=Math.max(maxZ,center.z+half.z);
  }
 }
 if(!Number.isFinite(minY)||maxY-minY<0.001)return {minX:0,minY:0,minZ:0,maxX:0,maxY:1,maxZ:0};
 return {minX,minY,minZ,maxX,maxY,maxZ};
}
// The GLB's bounding box is dominated by its off-center crown. Collision
// must come from the real bark at pedestrian height, not from the leaf canopy
// center or from a species-independent nominal radius.
function measureTrunk(prototype) {
 const points=[],local=new Vec3(),world=new Vec3();
 let minY=Infinity;
 const stack=[prototype];
 while(stack.length){
  const e=stack.pop();
  for(const child of e.children)stack.push(child);
  for(const mi of e.render?.meshInstances||[]){
   if(!/bark|trunk|wood|corteza/i.test(mi.material?.name||'') )continue;
   const positions=[];
   let count=0;
   try{count=mi.mesh?.getPositions(positions)||0;}catch(error){console.warn('Genesis trunk: cannot sample bark',error);continue;}
   const matrix=mi.node.getWorldTransform();
   for(let i=0;i<count;i++){
    local.set(positions[3*i],positions[3*i+1],positions[3*i+2]);
    matrix.transformPoint(local,world);
    if(!Number.isFinite(world.x+world.y+world.z))continue;
    points.push([world.x,world.y,world.z]);
    if(world.y<minY)minY=world.y;
   }
  }
 }
 if(!points.length||!Number.isFinite(minY))return null;
 const band=points.filter(p=>p[1]>=minY-.001 && p[1]<=minY+1.1);
 if(band.length<10)return null;
 const sortedX=band.map(p=>p[0]).sort((a,b)=>a-b);
 const sortedZ=band.map(p=>p[2]).sort((a,b)=>a-b);
 const cx=sortedX[Math.floor(sortedX.length*.5)];
 const cz=sortedZ[Math.floor(sortedZ.length*.5)];
 const radii=band.map(p=>Math.hypot(p[0]-cx,p[2]-cz)).sort((a,b)=>a-b);
 return {x:cx,z:cz,radius:Math.max(.1,radii[Math.floor(radii.length*.98)])};
}

export function mountVillageTrees(app, villageRoot, options={}){
 const safeMobile = globalThis.GenesisDevice?.safePreviews===true;
 const treeRoot=new Entity('Vegetación aprobada — 14 árboles · follaje íntegro PBR');
 villageRoot.addChild(treeRoot);
 const nodes=TREE_SITES.map(site=>{
  const anchor=new Entity('Árbol '+site.id+' · '+TYPES[site.species].label+' · '+site.region);
  anchor.setLocalPosition(site.x,0,site.z);anchor.setLocalEulerAngles(0,site.rotation,0);
  treeRoot.addChild(anchor);
  return {site,anchor,visual:null,lod:null,visible:false,collider:null};
 });
 const ready=new Map(),requested=new Set(),failed=new Set(),queue=[];
 const windMaterials=new Set();let windTime=0,windAccumulator=0;
 const windTick=dt=>{
  windTime+=Math.min(.07,Math.max(0,dt||0));windAccumulator+=dt||0;
  if(windAccumulator<(safeMobile?1/15:1/30))return;
  windAccumulator=0;
  for(const m of windMaterials)m.setParameter('uGenesisWindTime',windTime);
 };
 app.on('update',windTick);
 let active=0,focusX=0,focusZ=0,lastUpdate=0;
 const maxConcurrent=safeMobile?2:4;
 const initiallySettled=new Set();
 let resolveInitial;
 const initialReady=new Promise(resolve=>{resolveInitial=resolve;});
 const status=()=>({
  planned:nodes.length,plaza:TREE_SITES.filter(p=>p.region==='plaza').length,
  residentVariants:ready.size,failedVariants:failed.size,pendingVariants:queue.length+active,
  visible:nodes.filter(n=>n.visible&&n.visual).length,rendered:nodes.filter(n=>n.visible&&n.visual).length,
  mobile:safeMobile,windEnabled:windMaterials.size>0,windMaterials:windMaterials.size
 });
 function pump(){
  while(active<maxConcurrent&&queue.length){
   const task=queue.shift();active++;
   const url=task.legacy
    ? ORIGINALS+'assets/tree_webgl_v003/'+task.species+'/lod'+task.lod+'.glb'
    : assetPath(task.species,task.lod);
   app.assets.loadFromUrl(url,'container',(error,asset)=>{
    active--;
    if(error||!asset?.resource){
     if(!task.legacy&&task.lod>=1){
      console.warn('Genesis trees: reintentando GLB de respaldo',task.key,error);
      queue.unshift({...task,legacy:true});pump();return;
     }
     failed.add(task.key);
     console.warn('Genesis trees: no se pudo cargar',TYPES[task.species].label,'LOD'+task.lod,error||'sin recurso');
    }else{
     try{
      const prototype=asset.resource.instantiateRenderEntity();
      classifyAndTune(prototype,safeMobile,windMaterials);
      const dimensions=boundsOf(prototype);
      const trunk=measureTrunk(prototype);
      ready.set(task.key,{prototype,dimensions,trunk});
     }catch(err){
      if(!task.legacy&&task.lod>=1){
       queue.unshift({...task,legacy:true});pump();return;
      }
      failed.add(task.key);console.warn('Genesis trees: GLB inválido',task.key,err);
     }
    }
    if(task.lod===2&&!initiallySettled.has(task.species)){
     initiallySettled.add(task.species);
     if(ready.has(task.key))options.onResourceLoaded?.('tree:'+task.species+':lod2');
     if(initiallySettled.size===Object.keys(TYPES).length)resolveInitial({loaded:Object.keys(TYPES).length-failed.size,failed:failed.size});
    }
    update(focusX,focusZ,true);
    globalThis.__genesisTreeStatus=status();
    pump();
   });
  }
 }
 function request(species,lod){
  if(safeMobile&&lod!==2)return;
  if(lod===0)return; // Approved master kept offline: no 4K hero GLB in the village runtime.
  const key=species+':'+lod;
  if(ready.has(key)||requested.has(key)||failed.has(key))return;
  requested.add(key);queue.push({key,species,lod});pump();
 }
 function install(node,lod){
  if(node.lod===lod)return;
  const model=ready.get(node.site.species+':'+lod);
  if(!model)return;
  const {dimensions,prototype,trunk}=model,visual=prototype.clone();
  const sourceHeight=dimensions.maxY-dimensions.minY;
  const intended=TYPES[node.site.species].height*node.site.size*(node.site.region==='plaza'?.86:1);
  const scale=intended/Math.max(.01,sourceHeight);
  visual.setLocalScale(scale,scale,scale);
  visual.setLocalPosition(-(dimensions.minX+dimensions.maxX)*.5*scale,-dimensions.minY*scale,-(dimensions.minZ+dimensions.maxZ)*.5*scale);
  node.anchor.addChild(visual);
  if(node.visual)node.visual.destroy();
  node.visual=visual;node.lod=lod;
  // Transform the bark's measured ground center through the same visual
  // offset, individual tree scale and yaw used for rendering.
  if(trunk){
   const center=visual.getWorldTransform().transformPoint(new Vec3(trunk.x,0,trunk.z));
   node.collider={x:center.x,z:center.z,r:Math.max(.30,trunk.radius*scale+.04),measured:true};
  }else{
   node.collider={x:node.site.x,z:node.site.z,r:Math.max(.50,node.site.trunkRadius),measured:false};
  }
  const stack=[visual];while(stack.length){
   const entity=stack.pop();for(const child of entity.children)stack.push(child);
   if(entity.render){
    entity.render.castShadows=!safeMobile&&lod<2;
    for(const mi of entity.render.meshInstances||[])if(windMaterials.has(mi.material))
     mi.setParameter('uGenesisWindPhase',(node.site.id*1.71)%(Math.PI*2));
   }
  }
 }
 function update(x=focusX,z=focusZ,force=false){
  const now=performance.now();
  if(!force&&now-lastUpdate<450)return;
  lastUpdate=now;focusX=x;focusZ=z;
  const sorted=[...nodes].sort((a,b)=>Math.hypot(a.site.x-x,a.site.z-z)-Math.hypot(b.site.x-x,b.site.z-z));
  const maximum=safeMobile?37:56;
  for(const node of sorted){
   const d=Math.hypot(node.site.x-x,node.site.z-z);
   node.visible=d<maximum;
   node.anchor.enabled=node.visible;
   if(!node.visible)continue;
   const goal=safeMobile?2:d<23?1:2;
   request(node.site.species,2);
   if(ready.has(node.site.species+':2')&&goal<=1)request(node.site.species,1);
   const available=goal===1?[1,2]:[2];
   for(const candidate of available)if(ready.has(node.site.species+':'+candidate)){
    install(node,candidate);break;
   }
  }
  globalThis.__genesisTreeStatus=status();
 }
 // Fetch one visible baseline with full-approved master leaves per species before navigation.
 for(const species of Object.keys(TYPES))request(species,2);
 update(0,0,true);
 return Object.freeze({
  root:treeRoot,sites:TREE_SITES,update,status,initialReady,
  blocked(x,z,r=.33){return nodes.some(node=>node.visible&&node.visual&&node.anchor.enabled&&node.collider&&Math.hypot(node.collider.x-x,node.collider.z-z)<node.collider.r+r)},
  collisionSnapshot(){return nodes.filter(node=>node.collider).map(node=>({id:node.site.id,species:node.site.species,region:node.site.region,lod:node.lod,x:node.collider.x,z:node.collider.z,r:node.collider.r,measured:node.collider.measured,visible:node.visible,loaded:!!node.visual}))},
  release(){app.off('update',windTick);treeRoot.destroy();queue.length=0}
 });
}
