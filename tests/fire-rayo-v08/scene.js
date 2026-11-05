import * as pc from 'playcanvas';
import {createRayoV07,RAYO_V07_APPROVAL} from '../../vfx/approved/Genesis_Rayo_Helicoidal_V07.mjs';
import {createFuegoFiloV01,FUEGO_V01_SPEC} from '../../vfx/experimental/Genesis_Fuego_Filo_V01.mjs';
const canvas=document.getElementById('viewport');
const appOptions=new pc.AppOptions();
appOptions.graphicsDevice=await pc.createGraphicsDevice(canvas,{deviceTypes:[pc.DEVICETYPE_WEBGL2],antialias:true,alpha:false});
appOptions.componentSystems=[pc.RenderComponentSystem,pc.CameraComponentSystem,pc.LightComponentSystem];
appOptions.resourceHandlers=[pc.TextureHandler,pc.ContainerHandler];
const app=new pc.AppBase(canvas);app.init(appOptions);app.setCanvasResolution(pc.RESOLUTION_FIXED,1280,720);
app.start();
app.scene.ambientLight=new pc.Color(.40,.44,.53);
app.scene.exposure=1.25;app.scene.toneMapping=pc.TONEMAP_ACES;
const camera=new pc.Entity('GENESIS_V08_REFERENCE_CAMERA');
camera.addComponent('camera',{fov:34,nearClip:.01,farClip:50,clearColor:new pc.Color(.014,.017,.025)});
camera.setPosition(0,.02,3.36);camera.lookAt(0,0,0);app.root.addChild(camera);
function directional(name,rot,color,intensity){
 const e=new pc.Entity(name);e.addComponent('light',{type:'directional',color:new pc.Color(...color),intensity,castShadows:false});
 e.setEulerAngles(...rot);app.root.addChild(e);
}
directional('PBR_STUDIO_WARM_KEY',[28,43,0],[1,.92,.79],3.35);
directional('PBR_BLADE_STRIP',[6,-54,0],[.68,.83,1],2.8);
directional('IRON_RIM',[-44,15,0],[1,1,1],1.8);
let bloom=false;
try{
 const framePost=new pc.CameraFrame(app,camera.camera);
 framePost.bloom.intensity=.092;framePost.bloom.blurLevel=7;framePost.rendering.renderTargetScale=1;
 framePost.update();bloom=true;
}catch(e){console.error('GENESIS_V08_BLOOM_ERROR',e);}
let rayo=null,fuego=null;
function getElement(id){return document.getElementById(id);}
function setTitle(fire,ray){
 getElement('levelFire').textContent=String(fire);
 getElement('levelRay').textContent=String(ray);
 getElement('sceneCaption').textContent=fire&&ray?'FUEGO + RAYO':fire?'FUEGO SOBRE EL FILO':ray?'RAYO HELICOIDAL V07':'HIERRO V175 SIN CANALES';
}
function set(time,fire,ray){
 const f=Math.max(0,Math.min(100,Number(fire)||0)),r=Math.max(0,Math.min(100,Number(ray)||0));
 fuego.set(time,f);
 rayo.set(time,r);
 setTitle(f,r);
 return {time,fire:f,ray:r,source:'V03 original + V175'};
}
function loadSword(){
 app.assets.loadFromUrlAndFilename('/tests/fire-rayo-v08/source_original_v03.glb','Genesis_original_V03.glb','container',(err,asset)=>{
  if(err){window.__genesisError=String(err);console.error('GENESIS_V08_SOURCE_ERROR',err);return;}
  const e=asset.resource.instantiateRenderEntity();e.name='ORIGINAL_SOURCE_V03_UNMODIFIED';app.root.addChild(e);
  let meshes=0,tris=0,bladeAabb=null;const materials=[];
  e.forEach(c=>{if(c.render)for(const mi of c.render.meshInstances){
    meshes++;tris+=(mi.mesh?.primitive?.[0]?.count||0)/3;
    const name=mi.material?.name||'?';materials.push(name);
    if(name.includes('Iron_Blade_V175'))bladeAabb=mi.aabb;
  }});
  if(!bladeAabb){window.__genesisError='GENESIS_BLADE_V175_MISSING';console.error(window.__genesisError);return;}
  rayo=createRayoV07(pc,app,bladeAabb);
  fuego=createFuegoFiloV01(pc,app,bladeAabb);
  set(0,0,0);
  getElement('status').textContent='';
  window.__genesisReady={
   originalLoaded:true,sourceSha256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',
   triangles:tris,meshes,materials,
   rayoApproved:RAYO_V07_APPROVAL, fuegoSpec:FUEGO_V01_SPEC,
   rayoTriangles:rayo.stats.triangles,fireTriangles:fuego.stats.triangles,
   rayoHelix:rayo.stats,fireVeins:fuego.stats,
   sourceGLBEdited:false,bloom,fireStandalone:true,composable:true
  };
  console.log('GENESIS_V08_READY',JSON.stringify(window.__genesisReady));
 });
}
window.__genesisStep=async ({time=0,fire=0,ray=0})=>{
 if(!window.__genesisReady)throw Error(window.__genesisError||'NOT_READY');
 window.__genesisCaptureMode=true;
 const result=set(time,fire,ray);
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 if(!Number.isFinite(result.time))throw Error('NON_FINITE_TIME');
 return result;
};
app.on('update',()=>{if(!window.__genesisReady||window.__genesisCaptureMode)return;
 const t=performance.now()/1000;
 const f=Number(getElement('fireSlider').value),r=Number(getElement('raySlider').value);
 set(t,f,r);
});
getElement('fireSlider').addEventListener('input',e=>{getElement('levelFire').textContent=e.target.value;});
getElement('raySlider').addEventListener('input',e=>{getElement('levelRay').textContent=e.target.value;});
loadSword();
