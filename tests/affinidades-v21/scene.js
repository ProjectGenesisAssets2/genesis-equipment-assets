// Genesis V21 — five NEW independent experiments on the actual sword V03 and original V175 PBR.
// Neither Rayo V07 nor approved Fuego V20C.1 are instantiated or modified.
import * as pc from 'playcanvas';
import {verifyNewChannelBands} from '../../vfx/experimental/Genesis_AffinitySurfaceCore_V21.mjs';
import {createHieloV21,HIELO_V21_SPEC} from '../../vfx/experimental/Genesis_Hielo_V21_Cristalizacion.mjs';
import {createLuzV21,LUZ_V21_SPEC} from '../../vfx/experimental/Genesis_Luz_V21_Destellos.mjs';
import {createSombraV21,SOMBRA_V21_SPEC} from '../../vfx/experimental/Genesis_Sombra_V21_Brumas.mjs';
import {createNaturalezaV21,NATURALEZA_V21_SPEC} from '../../vfx/experimental/Genesis_Naturaleza_V21_Filamentos.mjs';
import {createTierraV21,TIERRA_V21_SPEC} from '../../vfx/experimental/Genesis_Tierra_V21_Mineral.mjs';
const specs={hielo:HIELO_V21_SPEC,luz:LUZ_V21_SPEC,
 sombra:SOMBRA_V21_SPEC,naturaleza:NATURALEZA_V21_SPEC,tierra:TIERRA_V21_SPEC};
const factory={hielo:createHieloV21,luz:createLuzV21,sombra:createSombraV21,
 naturaleza:createNaturalezaV21,tierra:createTierraV21};
const e=id=>document.getElementById(id);
const canvas=e('viewport');
const appOptions=new pc.AppOptions();
appOptions.graphicsDevice=await pc.createGraphicsDevice(canvas,{deviceTypes:[pc.DEVICETYPE_WEBGL2],antialias:true,alpha:false});
appOptions.componentSystems=[pc.RenderComponentSystem,pc.CameraComponentSystem,pc.LightComponentSystem];
appOptions.resourceHandlers=[pc.TextureHandler,pc.ContainerHandler];
const app=new pc.AppBase(canvas);app.init(appOptions);
app.setCanvasResolution(pc.RESOLUTION_FIXED,1280,720);app.start();
app.scene.ambientLight=new pc.Color(.40,.44,.53);
app.scene.exposure=1.25;app.scene.toneMapping=pc.TONEMAP_ACES;
const camera=new pc.Entity('GENESIS_V21_REFERENCE_CAMERA');
camera.addComponent('camera',{fov:34,nearClip:.01,farClip:50,clearColor:new pc.Color(.014,.017,.025)});
camera.setPosition(0,.02,3.36);camera.lookAt(0,0,0);app.root.addChild(camera);
function directional(name,rot,color,intensity) {
 const x=new pc.Entity(name);
 x.addComponent('light',{type:'directional',color:new pc.Color(...color),intensity,castShadows:false});
 x.setEulerAngles(...rot);app.root.addChild(x);
}
directional('PBR_STUDIO_WARM_KEY',[28,43,0],[1,.92,.79],3.35);
directional('PBR_BLADE_STRIP',[6,-54,0],[.68,.83,1],2.8);
directional('IRON_RIM',[-44,15,0],[1,1,1],1.8);
let bloom=false;
try{
 const framePost=new pc.CameraFrame(app,camera.camera);
 framePost.bloom.intensity=.092;framePost.bloom.blurLevel=7;
 framePost.rendering.renderTargetScale=1;framePost.update();bloom=true;
}catch(err){console.error('GENESIS_V21_BLOOM_ERROR',err);}
const active={};
let current='hielo',value=60;
const limits=verifyNewChannelBands();
function set(time,channel,intensity){
 if(!Object.prototype.hasOwnProperty.call(active,channel))throw Error('UNSUPPORTED_CHANNEL_'+channel);
 const t=Math.max(0,Number(time)||0),v=Math.min(100,Math.max(0,Number(intensity)||0));
 for(const [name,fx] of Object.entries(active))fx.set(t,name===channel?v:0);
 current=channel;value=v;
 e('channelSelect').value=channel;
 e('intensitySlider').value=String(v);
 e('levelValue').textContent=String(v);
 e('sceneCaption').textContent='AFINIDAD '+specs[channel].affinity.toUpperCase();
 e('channelInfo').textContent=specs[channel].visual;
 return {time:t,channel,intensity:v,slider:Number(e('intensitySlider').value),
  active:Object.keys(active).filter(k=>k===channel&&v>0),
  othersZero:Object.keys(active).every(k=>k===channel||active[k].light.light.intensity===0)};
}
function loadOriginal(){
 app.assets.loadFromUrlAndFilename('/tests/affinidades-v21/source_original_v03.glb','Genesis_original_V03.glb','container',(err,asset)=>{
  if(err){window.__genesisError=String(err);console.error('GENESIS_V21_SOURCE_ERROR',err);return;}
  const root=asset.resource.instantiateRenderEntity();root.name='SOURCE_SWORD_V03_ORIGINAL';app.root.addChild(root);
  let meshes=0,tris=0,bladeAabb=null;const materials=[];
  root.forEach(child=>{if(child.render)for(const mi of child.render.meshInstances){
   meshes++;tris+=(mi.mesh?.primitive?.[0]?.count||0)/3;
   const mat=mi.material?.name||'?';materials.push(mat);
   if(mat.includes('Iron_Blade_V175'))bladeAabb=mi.aabb;
  }});
  if(!bladeAabb){window.__genesisError='GENESIS_V21_ORIGINAL_BLADE_PBR_V175_NOT_FOUND';console.error(window.__genesisError);return;}
  try{
   for(const [name,create] of Object.entries(factory))active[name]=create(pc,app,bladeAabb);
   const renderStats=Object.fromEntries(Object.entries(active).map(([k,v])=>[k,v.stats]));
   set(0,'hielo',60);
   e('status').textContent='';
   window.__genesisReady={originalLoaded:true,
    originalSha256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',
    originalTriangles:tris,originalMeshes:meshes,materials,
    channelIDs:Object.keys(active),effects:renderStats,zones:limits,
    noRayoInstantiated:true,noFuegoInstantiated:true,
    sourceGLBEdited:false,sourceMaterialsEdited:false,
    allFiveInSingleScene:true,shaderSpecs:specs,bloom
   };
   console.log('GENESIS_V21_READY',JSON.stringify(window.__genesisReady));
  }catch(error){window.__genesisError=String(error);console.error('GENESIS_V21_EFFECT_CREATION_FAILED',error);}
 });
}
window.__genesisStep=async ({time=0,channel='hielo',intensity=60})=>{
 if(!window.__genesisReady)throw Error(window.__genesisError||'NOT_READY');
 window.__genesisCaptureMode=true;
 const result=set(time,channel,intensity);
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 return result;
};
app.on('update',()=>{
 if(!window.__genesisReady||window.__genesisCaptureMode)return;
 set(performance.now()/1000,e('channelSelect').value,Number(e('intensitySlider').value));
});
e('intensitySlider').addEventListener('input',event=>{e('levelValue').textContent=event.target.value;});
loadOriginal();
