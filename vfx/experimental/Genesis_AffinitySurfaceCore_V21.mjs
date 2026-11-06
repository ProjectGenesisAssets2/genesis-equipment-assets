// Genesis V21 - shared procedural surface geometry for five NEW affinities.
// Prototype: sword V03 only. Not universal object/mesh projection.
// Independent of approved Genesis_Rayo_Helicoidal_V07 and Genesis_Fuego_V20C.
// Every effect owns one distinct y-band and central blade-face volume.
// No original mesh/material writes; not yet proven collision-free WITH fire / lightning.
export const V21_ZONE_BANDS=Object.freeze({
 luz:[.015,.105],
 tierra:[.145,.265],
 naturaleza:[.315,.475],
 sombra:[.535,.690],
 hielo:[.755,.925]
});
export const V21_NEW_CHANNELS=Object.freeze(['hielo','luz','sombra','naturaleza','tierra']);
const vertexGLSL=`
attribute vec3 aPosition;
attribute vec2 aUv0;
uniform mat4 matrix_model;
uniform mat4 matrix_viewProjection;
varying vec2 vUv;
void main(void){
 vUv=aUv0;
 gl_Position=matrix_viewProjection*matrix_model*vec4(aPosition,1.0);
}
`;
export const v21NoiseGLSL=`
float genesisHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
float genesisNoise(vec2 p){
 vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
 return mix(mix(genesisHash(i),genesisHash(i+vec2(1.,0.)),f.x),
            mix(genesisHash(i+vec2(0.,1.)),genesisHash(i+vec2(1.,1.)),f.x),f.y);
}
float genesisFbm(vec2 p){
 float v=0.,a=.5;
 for(int k=0;k<3;k++){v+=a*genesisNoise(p);p*=2.01;a*=.5;}
 return v/.875;
}
`;
export function createV21SurfaceChannel(pc,app,bladeAabb,config){
 if(!V21_NEW_CHANNELS.includes(config.id))throw Error('V21_UNKNOWN_CHANNEL_'+config.id);
 const zone=V21_ZONE_BANDS[config.id];
 if(!zone)throw Error('V21_MISSING_BAND_'+config.id);
 const material=new pc.ShaderMaterial({
  uniqueName:'Genesis_'+config.id+'_V21_Experimental_Independent',
  attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
  vertexGLSL,fragmentGLSL:config.fragmentGLSL
 });
 material.blendType=pc.BLEND_ADDITIVEALPHA;
 material.cull=pc.CULLFACE_NONE;
 material.depthTest=true;material.depthWrite=false;
 material.setParameter('uTime',0);
 material.setParameter('uIntensity',0);
 material.update();
 const lo=bladeAabb.center.y-bladeAabb.halfExtents.y;
 const hi=bladeAabb.center.y+bladeAabb.halfExtents.y;
 const yStart=Math.max(lo+.13,-.38),yEnd=Math.min(hi-.095,.865);
 const full=yEnd-yStart,cx=bladeAabb.center.x,cz=bladeAabb.center.z;
 const p=[],uv=[],idx=[];
 let minY=Infinity,maxY=-Infinity,maxAbsX=0;
 const segments=12;
 for(let i=0;i<config.patches.length;i++){
  const patch=config.patches[i];
  if(patch.y-zone[0]<-.0001||patch.y+patch.height>zone[1]+.0001)
   throw Error('V21_OUTSIDE_RESERVED_BAND_'+config.id+'_'+i);
  const start=p.length/3;
  for(let j=0;j<=segments;j++){
   const t=j/segments;
   const v=patch.y+t*patch.height;
   const y=yStart+v*full;
   const smooth=Math.pow(Math.max(0.,Math.sin(Math.PI*t)),patch.shape==='glint'?.45:.55);
   const jagged=patch.shape==='crystal'?(1.+.16*Math.sin(t*27.+i*2.4)):1.;
   const centerX=(patch.x||0)+(patch.curve||0)*Math.sin(t*Math.PI*1.3+i*.82)*smooth;
   const width=Math.min(patch.halfWidth*smooth*jagged,Math.max(.0004,.0385-Math.abs(centerX)));
   if(Math.abs(centerX)+width>.039)throw Error('V21_OUT_OF_CENTER_METAL_'+config.id+'_'+i);
   const z=cz+(patch.z||.085);
   p.push(cx+centerX-width,y,z,cx+centerX+width,y,z);
   uv.push(i+t*.998,0,i+t*.998,1);
   minY=Math.min(minY,v);maxY=Math.max(maxY,v);
   maxAbsX=Math.max(maxAbsX,Math.abs(centerX)+width);
   if(j<segments){const k=start+j*2;idx.push(k,k+1,k+2,k+1,k+3,k+2);}
  }
 }
 const mesh=new pc.Mesh(app.graphicsDevice);
 mesh.setPositions(p);mesh.setUvs(0,uv);mesh.setIndices(idx);mesh.update();
 const entity=new pc.Entity('GENESIS_V21_'+config.id.toUpperCase()+'_SWORD_BAND');
 entity.addComponent('render',{
  meshInstances:[new pc.MeshInstance(mesh,material)],
  castShadows:false,receiveShadows:false
 });
 app.root.addChild(entity);
 const light=new pc.Entity('GENESIS_V21_'+config.id.toUpperCase()+'_LIGHT');
 light.addComponent('light',{
  type:'omni',
  color:new pc.Color(...config.lightColor),
  intensity:0,range:config.lightRange||.55,castShadows:false
 });
 const lightY=yStart+((zone[0]+zone[1])*.5)*full;
 light.setPosition(cx,lightY,cz+.12);app.root.addChild(light);
 function set(time,intensity){
  const sec=Number.isFinite(Number(time))?Math.max(0,Number(time)):0;
  const level=Number.isFinite(Number(intensity))?Math.max(0,Math.min(100,Number(intensity))):0;
  material.setParameter('uTime',sec);
  material.setParameter('uIntensity',level);
  light.light.intensity=(config.lightIntensity||.16)*(level/100)*(.88+.12*Math.sin(sec*3.+config.patches.length)**2);
 }
 set(0,0);
 return {entity,material,light,set,stats:{
  channel:config.id,patches:config.patches.length,triangles:idx.length/3,
  zoneRange:[...zone],occupiedY:[minY,maxY],maxAbsX,
  centerOnly:true,bladeFace:true,onlySwordPrototype:true,
  originalMeshEdited:false,originalMaterialEdited:false,
  otherFiveSpatiallySeparatedByBand:true,
  fireAndRayoCoexistenceTested:false,intensityRange:[0,100]
 }};
}
export function verifyNewChannelBands(){
 const entries=Object.entries(V21_ZONE_BANDS).sort((a,b)=>a[1][0]-b[1][0]);
 for(let i=0;i<entries.length;i++){
  const [key,zone]=entries[i];
  if(zone[0]<0||zone[1]>1||zone[1]<=zone[0])throw Error('BAD_BAND_'+key);
  if(i&&zone[0]<=entries[i-1][1][1])throw Error('OVERLAPPING_BANDS_'+key+'_'+entries[i-1][0]);
 }
 return entries.map(([id,band])=>({id,band,exclusiveWithinFive:true}));
}
