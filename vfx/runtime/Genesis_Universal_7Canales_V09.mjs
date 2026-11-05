// Project Genesis — generic attachment layers for seven elemental VFX.
// Base is physical damage/protection, never an elemental VFX.
// Original mesh and PBR materials are read only. VFX use separate render entities.
import {createRayoV07} from '../approved/Genesis_Rayo_Helicoidal_V07.mjs';
import {createFuegoFiloV01} from '../experimental/Genesis_Fuego_Filo_V01.mjs';
import {createOtherChannel} from '../experimental/Genesis_Cinco_Canales_V01.mjs';
export const ELEMENTAL_CHANNELS=['Luz','Sombra','Fuego','Hielo','Naturaleza','Tierra','Rayo'];
function cross(a,b,o){return (a.x-o.x)*(b.y-o.y)-(a.y-o.y)*(b.x-o.x);}
function hull(points){
 const a=[...new Map(points.map(p=>[p.x.toFixed(5)+','+p.y.toFixed(5),p])).values()]
   .sort((p,q)=>p.x-q.x||p.y-q.y);
 if(a.length<3)throw Error('SHIELD_SILHOUETTE_HAS_FEWER_THAN_3_POINTS');
 const lo=[],hi=[];
 for(const p of a){while(lo.length>=2&&cross(lo[lo.length-2],lo[lo.length-1],p)<=0)lo.pop();lo.push(p);}
 for(const p of a.slice().reverse()){while(hi.length>=2&&cross(hi[hi.length-2],hi[hi.length-1],p)<=0)hi.pop();hi.push(p);}
 lo.pop();hi.pop();return lo.concat(hi);
}
export function readWorldVertices(pc,root){
 const out=[];
 root.forEach(e=>{if(e.render)for(const mi of e.render.meshInstances){
   const coords=[];mi.mesh.getPositions(coords);
   const matrix=mi.node.getWorldTransform();
   for(let i=0;i<coords.length;i+=3){
     const v=matrix.transformPoint(new pc.Vec3(coords[i],coords[i+1],coords[i+2]));
     if(Number.isFinite(v.x)&&Number.isFinite(v.y)&&Number.isFinite(v.z))
       out.push({x:v.x,y:v.y,z:v.z});
   }
 }});
 if(out.length<3)throw Error('MESH_GEOMETRY_NO_CPU_VERTICES');
 return out;
}
function aabbOf(points){
 const min={x:Infinity,y:Infinity,z:Infinity},max={x:-Infinity,y:-Infinity,z:-Infinity};
 for(const p of points)for(const a of ['x','y','z']){min[a]=Math.min(min[a],p[a]);max[a]=Math.max(max[a],p[a]);}
 return {min,max,cx:(min.x+max.x)/2,cy:(min.y+max.y)/2,cz:(min.z+max.z)/2,
         width:max.x-min.x,height:max.y-min.y,depth:max.z-min.z};
}
function pathFromHull(points,side=1,offset=.018,inset=1){
 const h=hull(points),c={x:h.reduce((a,b)=>a+b.x,0)/h.length,y:h.reduce((a,b)=>a+b.y,0)/h.length};
 const box=aabbOf(points);const z=side>0?box.max.z+offset:box.min.z-offset;
 return [...h,...h.slice(0,1)].map(p=>({x:c.x+(p.x-c.x)*inset,y:c.y+(p.y-c.y)*inset,z}));
}
function ribbonMesh(pc,app,paths,width){
 const pos=[],uv=[],indices=[];let n=0;
 for(const path of paths){
   if(path.length<2)continue;
   const ds=[0];for(let i=1;i<path.length;i++){
     ds[i]=ds[i-1]+Math.hypot(path[i].x-path[i-1].x,path[i].y-path[i-1].y,path[i].z-path[i-1].z);
   }
   const total=ds[ds.length-1]||1;
   for(let i=0;i<path.length;i++){
     const a=path[Math.max(0,i-1)],b=path[Math.min(path.length-1,i+1)],p=path[i];
     const dx=b.x-a.x,dy=b.y-a.y,norm=Math.hypot(dx,dy)||1;
     const px=-dy/norm*width,py=dx/norm*width;
     pos.push(p.x+px,p.y+py,p.z,p.x-px,p.y-py,p.z);
     uv.push(ds[i]/total,0,ds[i]/total,1);
     if(i<path.length-1){const j=n+2*i;indices.push(j,j+1,j+2,j+1,j+3,j+2);}
   }
   n+=path.length*2;
 }
 const mesh=new pc.Mesh(app.graphicsDevice);
 mesh.setPositions(pos);mesh.setUvs(0,uv);mesh.setIndices(indices);mesh.update();
 return {mesh,triangles:indices.length/3,vertexCount:pos.length/3};
}
function attachMesh(pc,app,paths,material,name,thickness){
 const data=ribbonMesh(pc,app,paths,thickness);
 const entity=new pc.Entity('GENESIS_VFX_'+name);
 entity.addComponent('render',{meshInstances:[new pc.MeshInstance(data.mesh,material)],
  castShadows:false,receiveShadows:false});
 app.root.addChild(entity);
 return {entity,...data};
}
function swordEdgePaths(points){
 const bounds=aabbOf(points);
 const lo=Math.max(bounds.min.y+.13,bounds.cy-.38);
 const hi=Math.min(bounds.max.y-.095,bounds.cy+.865);
 const positive=[],negative=[];
 const rings=44;
 for(let k=0;k<=rings;k++){
   const t=k/rings,y=lo+(hi-lo)*t;
   const band=points.filter(p=>Math.abs(p.y-y)<Math.max(.035,bounds.height/rings*1.4));
   const all=band.length>=2?band:points;
   let minX=Math.min(...all.map(p=>p.x)),maxX=Math.max(...all.map(p=>p.x));
   // Restrict from guard towards tip and within the blade profile; never bind to handle.
   const maxWidth=.095*(1-.45*Math.max(0,(t-.76)/.24));
   minX=Math.max(minX,bounds.cx-maxWidth);maxX=Math.min(maxX,bounds.cx+maxWidth);
   if(maxX-minX<.006){minX=bounds.cx-.032;maxX=bounds.cx+.032;}
   const front=Math.max(...all.map(p=>p.z))+.022;
   negative.push({x:minX,y,z:front});
   positive.push({x:maxX,y,z:front});
 }
 return [negative,positive];
}
export function createSevenChannelRig(pc,app,targetEntity,{kind='sword',bladeAabb=null}={}){
 if(!['sword','shield'].includes(kind))throw Error('VFX_TARGET_MUST_BE_SWORD_OR_SHIELD');
 const vertices=readWorldVertices(pc,targetEntity);
 const box=aabbOf(vertices);
 if(kind==='sword'&&!bladeAabb)throw Error('SWORD_BLADE_AABB_REQUIRED');
 // For shields the silhouette is computed from actual mesh vertices rather than
 // assuming a circle, hexagon or pre-made UV mask. Front and reverse are separate.
 const paths=kind==='shield'
   ?[pathFromHull(vertices,1,.023,.985),pathFromHull(vertices,-1,.023,.985)]
   :swordEdgePaths(vertices);
 const dummy=bladeAabb||new pc.BoundingBox(new pc.Vec3(box.cx,box.cy,box.cz),
  new pc.Vec3(box.width/2,box.height/2,box.depth/2));
 const effects={};const attachments={};
 for(const channel of ELEMENTAL_CHANNELS){
   let instance;
   if(channel==='Rayo'){
     instance=createRayoV07(pc,app,dummy);
     if(kind==='shield'){
       instance.entity.enabled=false;
       attachments.Rayo=attachMesh(pc,app,paths,instance.material,'RAYO_SHIELD_CONTOUR',.015);
     }else attachments.Rayo={entity:instance.entity,triangles:instance.stats.triangles};
   }else if(channel==='Fuego'){
     instance=createFuegoFiloV01(pc,app,dummy);
     if(kind==='shield'){
       instance.entity.enabled=false;
       attachments.Fuego=attachMesh(pc,app,paths,instance.material,'FUEGO_SHIELD_EDGE',.013);
     }else attachments.Fuego={entity:instance.entity,triangles:instance.stats.triangles};
   }else {
     instance=createOtherChannel(pc,channel);
     attachments[channel]=attachMesh(pc,app,paths,instance.material,channel.toUpperCase()+'_'+kind.toUpperCase(),.012);
   }
   effects[channel]=instance;
 }
 let active={};
 let disposed=false;
 function apply(time,levels){
   if(disposed)throw Error('GENESIS_VFX_RIG_DISPOSED');
   for(const channel of ELEMENTAL_CHANNELS){
     const value=Math.max(0,Math.min(100,Number(levels?.[channel]||0)));
     effects[channel].set(time,value);
     active[channel]=value;
   }
   return {...active};
 }
 apply(0,{});
 function destroy(){
   if(disposed)return;
   disposed=true;
   // Dispose only ephemeral shader carriers/lights. The source GLB's meshes, textures
   // and PBR materials belong to the game's asset manager and are NEVER destroyed.
   const entities=new Set();
   for(const a of Object.values(attachments))if(a.entity)entities.add(a.entity);
   for(const fx of Object.values(effects)){
     if(fx.entity)entities.add(fx.entity);
     if(fx.light)entities.add(fx.light);
   }
   for(const entity of entities)if(entity.parent)entity.destroy();
   for(const fx of Object.values(effects))if(fx.material)fx.material.destroy();
 }
 return {
  destroy,
  kind,rig:'Genesis Universal Seven Channels V09',effects,attachments,
  inputMeshVertices:vertices.length,silhouetteVertices:kind==='shield'?hull(vertices).length:null,
  carrierTriangles:Object.values(attachments).reduce((n,a)=>n+(a.triangles||0),0),
  baseMaterialUntouched:true,
  levels:()=>({...active}),apply
 };
}
