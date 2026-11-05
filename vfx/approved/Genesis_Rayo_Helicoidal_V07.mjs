// Project Genesis: Rayo Helicoidal V07. VISUAL ART APPROVED BY USER.
// Snapshot extracted from the exact V07 PlayCanvas shader; GLB V03 and PBR V175 remain untouched.
// No external textures; shader is emissive and animates an otherwise invisible 3D helix.
// Do not change the look of this approved shader during tests of other channels.
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
const fragmentGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
float circleDistance(float a,float b){
  float d=abs(fract(a-b+.5)-.5);
  return d;
}
float travellingArc(float pos,float head,float radius){
  float d=circleDistance(pos,head);
  return 1.0-smoothstep(radius*.38,radius,d);
}
void main(void){
 float power=clamp(uIntensity*.01,0.0,1.0);
 if(power<.005) discard;
 float pos=vUv.x;
 float motion=fract(.14+uTime*.33);
 // Bright but contained 3D helicoidal discharge: 60/100 now reads as a powered channel.
 // The guiding spring remains invisible; only travelling core and soft emissive spill render.
 float primary=travellingArc(pos,motion,mix(.155,.295,power));
 float secondary=travellingArc(pos,fract(motion+.43),.165)*smoothstep(.18,.85,power)*.76;
 float tertiary=travellingArc(pos,fract(motion+.76),.082)*smoothstep(.74,1.0,power)*.38;
 float activity=clamp(primary+secondary+tertiary,0.0,1.0);
 float transverse=abs(2.0*vUv.y-1.0);
 float brightCore=pow(max(0.0,1.0-transverse),6.0);
 float halo=pow(max(0.0,1.0-transverse),1.65);
 float shimmer=.84+.16*sin(pos*230.0+uTime*19.0);
 float brightness=(1.35+1.9*power)*power*activity*shimmer;
 float lum=(.65*halo+2.05*brightCore)*brightness;
 if(lum<.012) discard;
 vec3 electric=vec3(.20,.66,1.90)*halo+vec3(.88,1.82,3.25)*brightCore;
 float alpha=clamp((.30*halo+.68*brightCore)*activity*(.58+.42*power),0.0,.84);
 gl_FragColor=vec4(electric*brightness,alpha);
}

`;

export const RAYO_V07_APPROVAL={id:'Genesis_Rayo_Helicoidal_V07',approvedVisual:true,
source:'experiment/v07-rayo-ciclo-completo-10-vs-100-20261104',
intensityMin:0,intensityMax:100,
originalSwordSha256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',
description:'3.15-turn 3D helical path, GLSL emissive travelling arcs; original geometry preserved'};
export function createRayoV07(pc,app,bladeAabb){
const material=new pc.ShaderMaterial({
 uniqueName:'Genesis_Rayo_Helice3D_V006_PresenceAt60',
 attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
 vertexGLSL,fragmentGLSL
});
material.blendType=pc.BLEND_ADDITIVEALPHA;
material.cull=pc.CULLFACE_NONE;
material.depthTest=true;
material.depthWrite=false;
material.setParameter('uTime',0);
material.setParameter('uIntensity',60);
material.update();


 const pulseLight=new pc.Entity('GENESIS_RAYO_V07_EMISSIVE_REFLECTION');
 pulseLight.addComponent('light',{type:'omni',color:new pc.Color(.12,.38,1),intensity:0,range:2,castShadows:false});
 app.root.addChild(pulseLight);
 let helixEntity=null;
 let helixStats=null;
function buildHelicalLightning(bladeAabb){
 const lo=bladeAabb.center.y-bladeAabb.halfExtents.y;
 const hi=bladeAabb.center.y+bladeAabb.halfExtents.y;
 const height=hi-lo;
 // Original V03 GLB AABB covers the whole sword, including guard and grip.
 // These fixed landmarks constrain VFX to its blade; source geometry remains unchanged.
 const yStart=Math.max(lo+height*.065,-.37);
 const yEnd=Math.min(hi-height*.085,.90);
 const radiusX=.063; // calibrated to actual blade silhouette, not whole-sword AABB
 const radiusZ=.064; // a little outside the blade surface for front/back depth occlusion
 const cx=bladeAabb.center.x,cz=bladeAabb.center.z;
 const turns=3.15,steps=580;
 const verts=[],uvs=[],indices=[];
 function point(t){
   const tt=Math.max(0,Math.min(1,t));
   const angle=2*Math.PI*(turns*tt+.18);
   const tipTaper=1.0-.46*Math.pow(Math.max(0,(tt-.76)/.24),1.45);
   const jag=.0021*Math.sin(tt*411.0)+.0011*Math.sin(tt*979.0);
   const radius=radiusX*tipTaper+jag;
   return [cx+radius*Math.cos(angle),yStart+(yEnd-yStart)*tt,cz+radiusZ*Math.sin(angle)];
 }
 const ribbonHalfWidth=.020;
 for(let i=0;i<=steps;i++){
   const t=i/steps,pt=point(t),before=point(t-.002),after=point(t+.002);
   let tx=after[0]-before[0],ty=after[1]-before[1];
   let norm=Math.hypot(tx,ty)||1;
   let perpX=-ty/norm,perpY=tx/norm;
   for(const side of [-1,1]){
     verts.push(pt[0]+perpX*ribbonHalfWidth*side,pt[1]+perpY*ribbonHalfWidth*side,pt[2]);
     uvs.push(t,side<0?0:1);
   }
   if(i<steps){
     let k=2*i;
     indices.push(k,k+1,k+2,k+1,k+3,k+2);
   }
 }
 const mesh=new pc.Mesh(app.graphicsDevice);
 mesh.setPositions(verts);mesh.setUvs(0,uvs);mesh.setIndices(indices);mesh.update();
 const entity=new pc.Entity('GENESIS_RAYO_V07_INVISIBLE_HELIX_3D');
 helixEntity=entity;
 entity.addComponent('render',{meshInstances:[new pc.MeshInstance(mesh,material)],castShadows:false,receiveShadows:false});
 app.root.addChild(entity);
 helixStats={turns,segments:steps,triangles:steps*2,depthTest:true,bladeHeight:height,
   radiusX,radiusZ,yStart,yEnd,placementBasis:'original-v03-blade-visual-landmarks',sourceBladeBounds:{
     center:[cx,bladeAabb.center.y,cz],
     half:[bladeAabb.halfExtents.x,bladeAabb.halfExtents.y,bladeAabb.halfExtents.z]
   }};
 pulseLight.setPosition(cx,(yStart+yEnd)/2,cz+.08);
 return helixStats;
}


 const stats=buildHelicalLightning(bladeAabb);
 function set(time,intensity){
  const level=Math.max(0,Math.min(100,Number(intensity)||0));
  material.setParameter('uTime',Number(time)||0);
  material.setParameter('uIntensity',level);
  pulseLight.light.intensity=.53*(level/100)*(.62+.38*Math.pow(Math.max(0,Math.sin(time*5.1+1.0)),5));
 }
 set(0,0);
 return {material,entity:helixEntity,light:pulseLight,stats,set,
  description:'Approved Rayo V07 as separate, reusable VFX; no base sword edits'};
}
