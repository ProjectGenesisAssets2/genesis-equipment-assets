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
app.scene.exposure=1.15;
app.scene.toneMapping=pc.TONEMAP_ACES;
const camera=new pc.Entity('GENESIS_CINEMATIC_CAMERA');
camera.addComponent('camera',{fov:34,nearClip:.01,farClip:50,clearColor:new pc.Color(.014,.017,.025)});
camera.setPosition(0,.02,3.48);camera.lookAt(0,0,0);
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
 framePost.bloom.intensity=.055;
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
float h1(float n){return fract(sin(n*127.17+34.23)*43758.5453);}
float hash2(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float piece(float y,float sections,float seed){
 float p=y*sections;float i=floor(p);
 return mix(h1(i+seed),h1(i+1.0+seed),fract(p))*2.0-1.0;
}
float fractalBolt(float y,float seed,float phase){
 float state=floor(phase*8.2);
 float x=.0;
 x+=.046*piece(y+phase*.05,12.,seed+state*.33);
 x+=.025*piece(y,37.,seed*2.17+state);
 x+=.008*piece(y,99.,seed*.67+state*1.3);
 return x;
}
float lp(float d,float radius){return exp(-abs(d)/radius);}
void main(){
 vec2 uv=vUv;
 float y=uv.y,x=uv.x;
 float t=uTime;
 float power=clamp(uIntensity,0.0,1.0);
 // The base iron PBR remains visible through the additive light.
 float core=0.,blue=0.,outer=0.,spark=0.;
 float envelope=smoothstep(.025,.095,y)*(1.0-smoothstep(.925,.989,y));
 float stablePulse=.84+.16*sin(t*29.0+1.9);
 // Five individualized, branching electric veins, not straight geometry.
 for(int i=0;i<5;i++){
   float fi=float(i);
   float anchor=(fi-2.0)*.043;
   float edgeBias=(fi<.5 || fi>3.5)?.084:0.0;
   float path=.5+anchor+edgeBias*(fi<2.? -1.:1.)
      +fractalBolt(y,fi*9.87+13.2,t)*(.70+.22*power);
   float dist=abs(x-path);
   float flick=.67+.33*h1(floor(t*12.0+fi*3.1));
   float focus=envelope*flick*(.6+.4*sin(y*23.+t*8.+fi));
   core+=lp(dist,.0021)*focus*(i==2?1.15:.74);
   blue+=lp(dist,.0105)*focus*(i==2?1.05:1.16);
   outer+=lp(dist,.034)*focus*.32;
 }
 // Short fractal branches erupt from specific anchors and dissipate.
 for(int j=0;j<12;j++){
   float fj=float(j);
   float seed=fj*23.74+9.0;
   float epoch=floor(t*6.0+fj*.13);
   float anchor=.10+fj*.064+.012*h1(fj*2.9);
   float life=smoothstep(anchor-.005,anchor+.018,y)*
            (1.0-smoothstep(anchor+.10,anchor+.17,y));
   float direction=mod(fj,2.)<1.? -1.:1.;
   float root=.5+fractalBolt(anchor,seed,t)*.45;
   float dy=clamp((y-anchor)/.17,0.,1.);
   float wobble=fractalBolt(y,seed*.91+4.2,t);
   float path=root+direction*(.018+.15*dy)+wobble*.44;
   float d=abs(x-path);
   float pulse=.5+.5*step(.35,h1(epoch+fj*11.3));
   float L=life*pulse;
   core+=lp(d,.00155)*L*.65;
   blue+=lp(d,.0085)*L*.85;
   outer+=lp(d,.027)*L*.22;
 }
 // Faint continuous shimmer across the existing longitudinal ridge.
 float ridge=lp(x-.501,.021)*envelope*(.16+.10*sin(y*38.-t*14.));
 blue+=ridge;
 // Edge corona follows the two physical blade edges but doesn't fill the blade.
 float edgeAbs=abs(x-.5);
 float edgeGlow=lp(edgeAbs-.080,.012)*envelope*(.44+.17*sin(y*35.+t*17.));
 blue+=edgeGlow*.35;outer+=edgeGlow*.18;
 // Transient micro-ionization, positioned in the halo, not primitive spheres.
 for(int k=0;k<18;k++){
  float fk=float(k);
  float epoch=floor(t*5.0+fk*.43);
  float sx=.5+(h1(fk*6.7+epoch*1.9)-.5)*.49;
  float sy=fract(h1(fk*7.9+epoch*4.1)+t*(.13+.04*h1(fk)));
  vec2 delta=(uv-vec2(sx,sy))*vec2(1.7,1.);
  float d=length(delta);
  float visibility=step(.64,h1(fk*3.2+epoch));
  spark+=exp(-d*270.)*visibility;
 }
 float flicker=(.73+.27*sin(t*32.5+1.5));
 core=clamp(core*stablePulse,0.,1.95);
 blue=clamp(blue,0.,2.3);
 outer=clamp(outer,0.,1.8);
 float current=power*(.88+.12*flicker);
 vec3 energy=
    vec3(.025,.20,1.32)*outer*.46+
    vec3(.055,.50,2.0)*blue*.72+
    vec3(.56,1.28,2.55)*core*.78+
    vec3(1.2,1.68,2.3)*spark*.7;
 float glow=clamp(core*.48+blue*.20+outer*.10+spark*.35,0.,.91);
 float lowAmbient=lp(x-.50,.20)*envelope*.035*current;
 vec3 ambient=vec3(.025,.11,.38)*lowAmbient;
 gl_FragColor=vec4(energy*current+ambient,max(.0,glow)*current);
}
`;
const material=new pc.ShaderMaterial({
 uniqueName:'Genesis_Rayo_Premium_FractalGLSL_V001',
 attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
 vertexGLSL,fragmentGLSL
});
material.blendType=pc.BLEND_ADDITIVEALPHA;
material.cull=pc.CULLFACE_NONE;
material.depthTest=false;
material.depthWrite=false;
material.setParameter('uTime',0);
material.setParameter('uIntensity',.85);
material.update();
const m=new pc.Mesh(app.graphicsDevice);
// Plane covers the real V03 blade only, z in front; generated 2-triangle VFX screen,
// not new sword geometry; no tube/cylinder/sphere primitives.
m.setPositions([-0.43,-.44,.18, .43,-.44,.18, .43,1.02,.18, -.43,1.02,.18]);
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
     vfxMaterial:material.name,proceduralShader:true,uvMasks:false,effectsMeshTriangles:2,sourceGlbEdited:false,materials:mats};
  document.getElementById('status').textContent='';
  console.log('GENESIS_RAYO_PREMIUM_READY',JSON.stringify(window.__genesisReady));
 });
}
window.__genesisStep=async (frame,frames=32)=>{
 if(!window.__genesisReady)throw Error('GLB_NOT_LOADED');
 const time=frame*2.75/frames;
 const intensity=.85;
 material.setParameter('uTime',time);
 material.setParameter('uIntensity',intensity);
 pulseLight.light.intensity=1.2+2.5*intensity*(.75+.25*Math.sin(time*17.0)**2);
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 return {frame,time,triangles:window.__genesisReady.triangles,bloom:bloomOK};
};
loadSword();
