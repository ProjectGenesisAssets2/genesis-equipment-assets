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
 framePost.bloom.intensity=.027;
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
uniform float uIntensity; // 0 to 100, not an arbitrary rarity tier.
float h1(float n){return fract(sin(n*127.17+34.23)*43758.5453);}
float zig(float y,float seed,float time){
  float s=floor(time*3.0);
  return .014*sin(y*51.0 + seed*2.8 + s*.56)
       + .008*sin(y*113.0 - seed*6.2 + s*.91)
       + .003*sin(y*251.0 + seed*1.2 + s*.33);
}
float lineEnergy(float distance,float width){return exp(-abs(distance)/width);}
float segment(float y,float center,float radius){
  return 1.0-smoothstep(radius*.45,radius,abs(y-center));
}
void main(void){
 vec2 uv=vUv;
 float x=uv.x,y=uv.y,t=uTime;
 float power=clamp(uIntensity*.01,0.0,1.0);
 // Blade only: never the guard, grip or pommel. Remaining UVs are transparent.
 float blade=smoothstep(.13,.25,y)*(1.0-smoothstep(.88,.965,y));
 blade*=1.0-smoothstep(.27,.33,abs(x-.5));
 // Brief, contained motion rather than persistent lightning or full-body corona.
 float beat=pow(max(0.0,sin(t*5.1+1.0)),5.0);
 float glimmer=.31+.69*beat;
 float travel=.56+.075*sin(t*1.6);
 float primary=segment(y,travel,.16)*blade;
 float second=segment(y,.38+.045*sin(t*1.25+1.7),.095)*blade
              *smoothstep(.30,.64,power);
 float third=segment(y,.73+.025*sin(t*.95+2.0),.065)*blade
             *smoothstep(.73,.98,power);
 float mainPath=.5+zig(y,1.0,t);
 float secondPath=.52+zig(y,2.9,t);
 float thirdPath=.477+zig(y,4.1,t);
 float core=lineEnergy(x-mainPath,.0080)*primary
          +lineEnergy(x-secondPath,.0065)*second*.55
          +lineEnergy(x-thirdPath,.0055)*third*.32;
 float shimmer=lineEnergy(x-mainPath,.027)*primary*.25
          +lineEnergy(x-secondPath,.011)*second*.09
          +lineEnergy(x-thirdPath,.009)*third*.05;
 // Sparse 1-2 little branches at higher channel strength, no free-floating sparks.
 float spurAmount=smoothstep(.52,.90,power);
 float branchPath=.5+.028*(y-.57)+zig(y,7.2,t)*.6;
 float branch=lineEnergy(x-branchPath,.0028)*
              segment(y,.60,.045)*blade*spurAmount*beat*.28;
 core+=branch;
 float strength=power*(.70+.70*power)*(.42+.58*beat);
 vec3 electricBlue=vec3(.36,1.00,2.00)*shimmer
                  +vec3(.90,1.55,2.40)*core;
 vec3 result=electricBlue*strength;
 float opacity=clamp((core*.90+shimmer*.34)*(.30+.70*power),0.,.65);
 gl_FragColor=vec4(result,opacity);
}

`;
const material=new pc.ShaderMaterial({
 uniqueName:'Genesis_Rayo_ContainedBlade_0to100_V004',
 attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
 vertexGLSL,fragmentGLSL
});
material.blendType=pc.BLEND_ADDITIVEALPHA;
material.cull=pc.CULLFACE_NONE;
material.depthTest=false;
material.depthWrite=false;
material.setParameter('uTime',0);
material.setParameter('uIntensity',35);
material.update();
const m=new pc.Mesh(app.graphicsDevice);
// Plane covers the real V03 blade only, z in front; generated 2-triangle VFX screen,
// not new sword geometry; no tube/cylinder/sphere primitives.
m.setPositions([-.135,.08,.18, .135,.08,.18, .135,.96,.18, -.135,.96,.18]);
m.setUvs(0,[0,0,1,0,1,1,0,1]);
m.setIndices([0,1,2,0,2,3]);m.update();
const shaderEntity=new pc.Entity('RAYO_SHADER_BLADE_DECAL_PROCEDURAL');
shaderEntity.addComponent('render',{meshInstances:[new pc.MeshInstance(m,material)],castShadows:false,receiveShadows:false});
app.root.addChild(shaderEntity);
function loadSword(){
 app.assets.loadFromUrlAndFilename('/tests/rayo-premium-v01/source_original_v03.glb','Genesis_original_V03.glb','container',(err,asset)=>{
  if(err){window.__genesisError=String(err);console.error('SOURCE_V03_ERROR',err);return;}
  const e=asset.resource.instantiateRenderEntity();e.name='ORIGINAL_SOURCE_V03_UNMODIFIED';
  app.root.addChild(e);
  let meshes=0,tris=0;const mats=[];
  e.forEach(c=>{if(c.render){for(const mi of c.render.meshInstances){
    meshes++;tris+=(mi.mesh?.primitive?.[0]?.count||0)/3;
    mats.push(mi.material?.name||'?');
  }}});
  window.__genesisReady={source:'original_v03',loaded:true,meshes,triangles:tris,bloom:bloomOK,
     vfxMaterial:material.name,proceduralShader:true,uvMasks:false,effectsMeshTriangles:2,sourceGlbEdited:false,materials:mats,intensityRange:[0,100],defaultIntensity:35,bladeOnly:true,intensityAnimation:'0-to-100-in-32-frames'};
  document.getElementById('status').textContent='';
  console.log('GENESIS_RAYO_PREMIUM_READY',JSON.stringify(window.__genesisReady));
 });
}
window.__genesisIntensity=35;
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
 pulseLight.light.intensity=.30*(intensity/100)*(.35+.65*Math.pow(Math.max(0,Math.sin(time*5.1+1.0)),5));
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 if(!Number.isFinite(time))throw Error('INVALID_SHADER_TIME');
 return {frame,time,intensity,triangles:window.__genesisReady.triangles,bloom:bloomOK};
};
document.getElementById('intensitySlider').addEventListener('input',e=>window.__genesisSetIntensity(e.target.value));
app.on('update',dt=>{if(!window.__genesisReady||window.__genesisCaptureMode)return;const now=performance.now()/1000;material.setParameter('uTime',now);material.setParameter('uIntensity',window.__genesisIntensity);pulseLight.light.intensity=.30*(window.__genesisIntensity/100)*(.35+.65*Math.pow(Math.max(0,Math.sin(now*5.1+1.0)),5));});
loadSword();
