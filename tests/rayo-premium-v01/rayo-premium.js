import * as pc from 'playcanvas';
const canvas=document.getElementById('viewport');
const appOptions=new pc.AppOptions();
appOptions.graphicsDevice=await pc.createGraphicsDevice(canvas,{deviceTypes:[pc.DEVICETYPE_WEBGL2],antialias:true,alpha:false});
appOptions.componentSystems=[pc.RenderComponentSystem,pc.CameraComponentSystem,pc.LightComponentSystem];
appOptions.resourceHandlers=[pc.TextureHandler,pc.ContainerHandler];
const app=new pc.AppBase(canvas);app.init(appOptions);
app.setCanvasResolution(pc.RESOLUTION_FIXED,1280,720);
app.start();
app.scene.ambientLight=new pc.Color(.40,.44,.53);
app.scene.exposure=1.25;
app.scene.toneMapping=pc.TONEMAP_ACES;
const camera=new pc.Entity('GENESIS_CINEMATIC_CAMERA');
camera.addComponent('camera',{fov:34,nearClip:.01,farClip:50,clearColor:new pc.Color(.014,.017,.025)});
camera.setPosition(0,.02,3.36);camera.lookAt(0,0,0);
app.root.addChild(camera);
function directional(name,euler,color,intensity){
  const e=new pc.Entity(name);e.addComponent('light',{type:'directional',color:new pc.Color(...color),intensity,castShadows:false});
  e.setEulerAngles(...euler);app.root.addChild(e);return e;
}
directional('PBR_STUDIO_WARM_KEY',[28,43,0],[1,.92,.79],3.35);
directional('PBR_BLADE_STRIP',[6,-54,0],[.68,.83,1],2.8);
directional('IRON_RIM',[-44,15,0],[1,1,1],1.8);
const pulseLight=new pc.Entity('ELECTRIC_EMISSIVE_REFLECTION');
pulseLight.addComponent('light',{type:'omni',color:new pc.Color(.12,.38,1),intensity:0,range:2,castShadows:false});
pulseLight.setPosition(.04,.40,.17);app.root.addChild(pulseLight);
// Real HDR CameraFrame bloom. No baked texture mask or simulated 3D tubes.
let bloomOK=false,framePost=null;
try{
 framePost=new pc.CameraFrame(app,camera.camera);
 framePost.bloom.intensity=.092;
 framePost.bloom.blurLevel=7;
 framePost.rendering.renderTargetScale=1;
 framePost.update();
 bloomOK=true;
 console.log('GENESIS_RAYO_CAMERA_FRAME_BLOOM',framePost.bloom.intensity);
}catch(err){console.error('GENESIS_BLOOM_INIT_ERROR',err)}
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
 const entity=new pc.Entity('GENESIS_RAYO_V06_INVISIBLE_HELIX_3D');
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

function loadSword(){
 app.assets.loadFromUrlAndFilename('/tests/rayo-premium-v01/source_original_v03.glb','Genesis_original_V03.glb','container',(err,asset)=>{
  if(err){window.__genesisError=String(err);console.error('SOURCE_V03_ERROR',err);return;}
  const e=asset.resource.instantiateRenderEntity();e.name='ORIGINAL_SOURCE_V03_UNMODIFIED';
  app.root.addChild(e);
  let meshes=0,tris=0;const mats=[];let bladeAabb=null;
  e.forEach(c=>{if(c.render){for(const mi of c.render.meshInstances){
    meshes++;tris+=(mi.mesh?.primitive?.[0]?.count||0)/3;
    mats.push(mi.material?.name||'?');
    if((mi.material?.name||'').includes('Iron_Blade_V175'))bladeAabb=mi.aabb;
  }}});
  if(!bladeAabb){window.__genesisError='V175_BLADE_BOUNDS_MISSING';throw Error(window.__genesisError);}
  const helix=buildHelicalLightning(bladeAabb);
  window.__genesisReady={source:'original_v03',loaded:true,meshes,triangles:tris,bloom:bloomOK,
     vfxMaterial:material.name,proceduralShader:true,uvMasks:false,effectsMeshTriangles:helix.triangles,helix,geometry:'actual-worldspace-3d-helix',visualCalibration:'60-of-100-legible-in-inventory',sourceGlbEdited:false,materials:mats,intensityRange:[0,100],defaultIntensity:60,bladeOnly:true,intensityAnimation:'0-to-100-in-32-frames'};
  document.getElementById('status').textContent='';
  console.log('GENESIS_RAYO_PREMIUM_READY',JSON.stringify(window.__genesisReady));
 });
}
window.__genesisIntensity=60;
window.__genesisSetIntensity=(v)=>{let n=Math.max(0,Math.min(100,Math.round(Number(v)||0)));window.__genesisIntensity=n;document.getElementById('intensityValue').textContent=n;document.getElementById('intensitySlider').value=n;return n;};
window.__genesisStep=async (frame,frames=32,forcedIntensity)=>{
 if(!window.__genesisReady)throw Error('GLB_NOT_LOADED');
 window.__genesisCaptureMode=true;
 const rampIntensity=forcedIntensity===undefined?Math.round(100*frame/Math.max(1,frames-1)):forcedIntensity;
 window.__genesisSetIntensity(rampIntensity);
 const time=Number(frame)*2.75/Number(frames);
 const intensity=Math.max(0,Math.min(100,Number(rampIntensity)));
 material.setParameter('uTime',time);
 material.setParameter('uIntensity',intensity);
 pulseLight.light.intensity=.53*(intensity/100)*(.62+.38*Math.pow(Math.max(0,Math.sin(time*5.1+1.0)),5));
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 if(!Number.isFinite(time))throw Error('INVALID_SHADER_TIME');
 return {frame,time,intensity,triangles:window.__genesisReady.triangles,bloom:bloomOK};
};
document.getElementById('intensitySlider').addEventListener('input',e=>window.__genesisSetIntensity(e.target.value));
app.on('update',dt=>{if(!window.__genesisReady||window.__genesisCaptureMode)return;const now=performance.now()/1000;material.setParameter('uTime',now);material.setParameter('uIntensity',window.__genesisIntensity);pulseLight.light.intensity=.53*(window.__genesisIntensity/100)*(.62+.38*Math.pow(Math.max(0,Math.sin(now*5.1+1.0)),5));});
loadSword();
