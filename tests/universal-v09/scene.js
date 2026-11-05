import * as pc from 'playcanvas';
import {createSevenChannelRig,ELEMENTAL_CHANNELS} from '../../vfx/runtime/Genesis_Universal_7Canales_V09.mjs';
const canvas=document.getElementById('viewport'),options=new pc.AppOptions();
options.graphicsDevice=await pc.createGraphicsDevice(canvas,{deviceTypes:[pc.DEVICETYPE_WEBGL2],antialias:true,alpha:false});
options.componentSystems=[pc.RenderComponentSystem,pc.CameraComponentSystem,pc.LightComponentSystem];
options.resourceHandlers=[pc.TextureHandler,pc.ContainerHandler];
const app=new pc.AppBase(canvas);app.init(options);app.setCanvasResolution(pc.RESOLUTION_FIXED,1280,720);app.start();
app.scene.exposure=1.25;app.scene.toneMapping=pc.TONEMAP_ACES;
app.scene.ambientLight=new pc.Color(.42,.46,.56);
const camera=new pc.Entity('V09_CAMERA');
camera.addComponent('camera',{fov:36,nearClip:.01,farClip:25,clearColor:new pc.Color(.014,.018,.027)});
camera.setPosition(0,0,3.55);camera.lookAt(0,0,0);app.root.addChild(camera);
function light(name,rotation,color,intensity){
 const e=new pc.Entity(name);e.addComponent('light',{type:'directional',color:new pc.Color(...color),intensity,castShadows:false});
 e.setEulerAngles(...rotation);app.root.addChild(e);
}
light('PBR_KEY',[28,43,0],[1,.94,.82],3.2);
light('PBR_LONG_STRIP',[6,-54,0],[.68,.83,1],2.8);
light('METAL_RIM',[-44,15,0],[1,1,1],1.8);
let bloom=false;
try{const cf=new pc.CameraFrame(app,camera.camera);cf.bloom.intensity=.075;cf.bloom.blurLevel=7;cf.update();bloom=true;}
catch(e){console.error('BLOOM_ERROR_V09',e)}
function createShieldValidationFixture(){
 // Explicit fixture, NOT the user's approved shield asset. Its unequal facets and pointed
 // bottom test whether the adapter reads actual mesh vertices (not a hardcoded circle).
 const outline=[
  [-.31,.64],[-.47,.45],[-.46,.08],[-.29,-.30],[0,-.68],
  [.29,-.30],[.46,.08],[.47,.45],[.31,.64]
 ];
 const pos=[0,0,.0],indices=[],zfront=.0,zback=-.065;
 for(const [x,y] of outline)pos.push(x,y,zfront);
 for(let i=0;i<outline.length;i++)indices.push(0,1+i,1+(i+1)%outline.length);
 const backoffset=pos.length/3;pos.push(0,0,zback);
 for(const [x,y] of outline)pos.push(x,y,zback);
 for(let i=0;i<outline.length;i++)indices.push(backoffset,backoffset+1+(i+1)%outline.length,backoffset+1+i);
 const mesh=new pc.Mesh(app.graphicsDevice);
 mesh.setPositions(pos);mesh.setIndices(indices);mesh.update();
 const mat=new pc.StandardMaterial();
 mat.useMetalness=true;mat.metalness=.82;mat.gloss=.36;mat.diffuse=new pc.Color(.55,.57,.62);mat.update();
 const e=new pc.Entity('SHIELD_TEST_FIXTURE_UNAPPROVED');
 e.addComponent('render',{meshInstances:[new pc.MeshInstance(mesh,mat)],castShadows:false,receiveShadows:false});
 app.root.addChild(e);
 e.setPosition(.77,0,0);
 return {entity:e,fixture:true,shape:'noncircular-pointed-shield',vertices:outline.length};
}
let swordRig=null,shieldRig=null;
function apply(time,channel,level){
 const values={};values[channel]=level;
 swordRig.apply(time,values);shieldRig.apply(time,values);
 document.getElementById('activeChannel').textContent=channel;
 document.getElementById('activeIntensity').textContent=String(level);
 return {channel,level,time,sword:swordRig.levels(),shield:shieldRig.levels()};
}
function loadSword(){
 app.assets.loadFromUrlAndFilename('/tests/universal-v09/source_original_v03.glb','Genesis_original_V03.glb','container',(err,asset)=>{
  if(err){window.__genesisError=String(err);console.error('SOURCE_ERROR',err);return;}
  const e=asset.resource.instantiateRenderEntity();e.name='V03_SWORD_UNMODIFIED';app.root.addChild(e);
  e.setPosition(-.73,0,0);
  let bladeAabb=null,meshes=0,triangles=0;
  const mats=[];
  e.forEach(c=>{if(c.render)for(const mi of c.render.meshInstances){
    const name=mi.material?.name||'?';mats.push(name);
    if(name.includes('Iron_Blade_V175'))bladeAabb=mi.aabb;
    meshes++;triangles+=(mi.mesh.primitive?.[0]?.count||0)/3;
  }});
  if(!bladeAabb){window.__genesisError='IRON_V175_BLADE_AABB_NOT_FOUND';throw Error(window.__genesisError);}
  swordRig=createSevenChannelRig(pc,app,e,{kind:'sword',bladeAabb});
  const fixture=createShieldValidationFixture();
  shieldRig=createSevenChannelRig(pc,app,fixture.entity,{kind:'shield'});
  apply(0,'Rayo',0);
  document.getElementById('status').textContent='';
  window.__genesisReady={
   channels:ELEMENTAL_CHANNELS,channelCount:ELEMENTAL_CHANNELS.length,
   sword:{source:'real V03 GLB',triangles,meshes,materials:mats,
     carrierTriangles:swordRig.carrierTriangles,meshVertices:swordRig.inputMeshVertices},
   shield:{source:'procedural fixture NOT USER SHIELD',shape:fixture.shape,
     carrierTriangles:shieldRig.carrierTriangles,meshVertices:shieldRig.inputMeshVertices,
     computedSilhouetteVertices:shieldRig.silhouetteVertices},
   originalSourceEdited:false,bloom,renderEngine:'PlayCanvas 2.23 WebGL2',
   approvedRayoVisualPreserved:true,fireUnapproved:true,
   productionShieldGLBTested:false
  };
  console.log('GENESIS_V09_READY',JSON.stringify(window.__genesisReady));
 });
}
window.__genesisStep=async({time=0,channel='Rayo',intensity=60,swordLevels=null,shieldLevels=null})=>{
 if(!window.__genesisReady)throw Error(window.__genesisError||'V09_NOT_READY');
 if(!ELEMENTAL_CHANNELS.includes(channel))throw Error('UNKNOWN_CHANNEL_'+channel);
 window.__captureMode=true;
 const values={[channel]:intensity};
 swordRig.apply(time,swordLevels||values);shieldRig.apply(time,shieldLevels||values);
 document.getElementById('activeChannel').textContent=channel;
 document.getElementById('activeIntensity').textContent=String(intensity);
 await new Promise(res=>requestAnimationFrame(()=>requestAnimationFrame(res)));
 return {time,channel,intensity,sword:swordRig.levels(),shield:shieldRig.levels()};
};
app.on('update',()=>{if(!window.__genesisReady||window.__captureMode)return;
 apply(performance.now()/1000,'Rayo',60);});
loadSword();
