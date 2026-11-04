import * as pc from 'playcanvas';
const canvas=document.getElementById('app');
const device=await pc.createGraphicsDevice(canvas,{deviceTypes:[pc.DEVICETYPE_WEBGL2],antialias:true});
const options=new pc.AppOptions();
options.graphicsDevice=device;
options.componentSystems=[pc.RenderComponentSystem,pc.CameraComponentSystem,pc.LightComponentSystem];
options.resourceHandlers=[pc.TextureHandler,pc.ContainerHandler];
const app=new pc.AppBase(canvas);app.init(options);
app.setCanvasResolution(pc.RESOLUTION_FIXED,1280,720);
app.start();
app.scene.ambientLight=new pc.Color(.29,.31,.38);
app.scene.toneMapping=pc.TONEMAP_ACES;
app.scene.exposure=1.10;
const camera=new pc.Entity('V03_PREMIUM_CAMERA');
camera.addComponent('camera',{fov:34,nearClip:.02,farClip:45,clearColor:new pc.Color(.013,.016,.025)});
camera.setPosition(.10,.0,3.60);camera.lookAt(0,0,0);app.root.addChild(camera);
function studio(name,euler,color,intensity){
 const e=new pc.Entity(name);e.addComponent('light',{type:'directional',color:new pc.Color(...color),intensity,castShadows:false});
 e.setEulerAngles(...euler);app.root.addChild(e);return e;
}
studio('IRON_KEY',[25,46,0],[1,.86,.70],2.0);
studio('IRON_FILL',[16,-67,0],[.58,.73,1.0],1.9);
studio('IRON_STRIP',[-45,10,0],[1,1,1],1.2);
const practical=new pc.Entity('RAYO_BLUE_PBR_LIGHT');
practical.addComponent('light',{type:'omni',color:new pc.Color(.08,.40,1),intensity:1.6,range:2.4,castShadows:false});
practical.setPosition(.02,.35,.20);app.root.addChild(practical);
let bloomInfo='unavailable';
try{
 const frame=new pc.CameraFrame(app,camera.camera);
 frame.rendering.toneMapping=pc.TONEMAP_ACES;
 frame.rendering.samples=4;
 frame.bloom.intensity=.020;
 frame.bloom.blurLevel=8;
 frame.update();
 bloomInfo='CameraFrame HDR bloom .020';
}catch(e){console.warn('GENESIS_PREMIUM_BLOOM_UNAVAILABLE',String(e))}
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
const fragGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
float hash11(float x){return fract(sin(x*127.1)*43758.5453);}
float wire(float x,float y,float phase,float seed,float w){
 float z=floor(uTime*9.0+seed*2.0);
 float flick=hash11(z+seed*17.0);
 float v=sin(y*47.0+seed*4.1+uTime*4.1)*.043;
 v+=sin(y*103.0+seed*16.2+z*.73)*.018;
 v+=sin(y*211.0+seed*7.6+z*3.1)*.009;
 float center=x-(phase+v);
 float narrow=exp(-pow(abs(center)/w,1.30));
 return narrow*(.48+.52*flick);
}
void main(void){
 vec2 p=vec2((vUv.x-.5)*2.0,(vUv.y-.5)*2.0);
 float x=p.x;
 float y=p.y;
 float motion=uTime;
 // The metal beneath remains fully visible; no albedo, normal or roughness is replaced.
 float blade=smoothstep(-.93,-.80,y)*(1.0-smoothstep(.82,.98,y));
 float along=pow(.45+.55*sin(y*7.4-motion*7.8),2.0);
 float height=blade*(.70+.30*along);
 float core=0.0;
 float fringe=0.0;
 float outer=0.0;
 for(int k=0;k<4;k++){
  float seed=float(k);
  float side=mod(seed,2.0)<.5?-1.0:1.0;
  float center=side*(.225+.068*sin(y*4.3+seed*2.8+motion*1.3));
  float line=wire(x,y,center,seed,.010+seed*.0015);
  float gap=sin(y*(13.1+seed*1.7)-motion*(5.9+seed)+seed*2.2);
  float gate=smoothstep(-.2,.25,gap);
  core+=line*gate*(k<2?1.0:.4);
  float d=abs(x-center);
  fringe+=exp(-d*d/(.042*.042))*gate*.18;
  outer+=exp(-d*d/(.104*.104))*gate*.055;
 }
 // Branches flare out from the edges at irregular, evolving attachment points.
 float branch=0.0;
 for(int k=0;k<8;k++){
  float n=float(k);
  float cy=-.76+mod(n*0.267+floor(motion*.87)*.033,1.62);
  float fy=y-cy;
  float length=.135+.09*hash11(n*33.8);
  float window=smoothstep(0.,.023,fy)*(1.-smoothstep(length-.024,length,fy));
  float direction=mod(n,2.0)<.5?-1.0:1.0;
  float o=direction*(.25+fy*(1.1+hash11(n*7.2)));
  o+=sin(fy*79.+n*8.+floor(motion*12.))*.014;
  float d=abs(x-o);
  branch+=exp(-pow(d/.009,1.24))*window*(.55+.45*hash11(floor(motion*11.)+n));
  outer+=exp(-pow(d/.045,1.2))*window*.024;
 }
 // Electric nerve along blade ridge, interrupted with moving pulses.
 float nerve=exp(-pow(abs(x-(sin(y*23.-motion*8.)*.046))/.015,1.18));
 nerve*=pow(.52+.48*sin(y*10.-motion*12.),5.)*.7;
 // Sparse hot sparks in the outer air, not geometric spheres or particle primitives.
 vec2 cell=floor(vec2((x+1.)*21.,(y+1.)*49.));
 float rnd=hash11(cell.x*71.3+cell.y*9.7+floor(motion*13.));
 float sx=hash11(cell.y*5.+cell.x*3.9)-.5;
 float sy=hash11(cell.y*12.+cell.x*1.3)-.5;
 vec2 offset=fract(vec2((x+1.)*21.,(y+1.)*49.))-.5-vec2(sx,sy)*.60;
 float sparks=(1.-smoothstep(.01,.22,length(offset)))*step(.982,rnd);
 sparks*=smoothstep(.25,.55,abs(x))*(1.-smoothstep(.8,1.,abs(x)))*blade;
 float intense=clamp(uIntensity,0.,1.);
 core=(core+branch*.76+nerve*.45)*height;
 outer=(outer+fringe)*blade;
 vec3 white=vec3(.75,.92,1.0);
 vec3 blue=vec3(.016,.28,1.0);
 vec3 deep=vec3(.005,.04,.35);
 float blueGlow=outer*2.4 + core*.30;
 float whiteHot=core*.9+sparks*2.;
 vec3 color=deep*outer*2.7+blue*(blueGlow+core*.62)+white*(whiteHot);
 float alpha=clamp((core*.78+outer*.33+sparks)*(.60+.80*intense),0.,.78);
 color*=1.1+2.1*intense;
 gl_FragColor=vec4(color*height+blue*sparks*1.1,alpha);
}
`;
const mat=new pc.ShaderMaterial({uniqueName:'GenesisRayoPremiumGLSLv001',
 attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
 vertexGLSL,fragmentGLSL:fragGLSL});
mat.blendType=pc.BLEND_ADDITIVE;mat.depthWrite=false;mat.depthTest=true;mat.cull=pc.CULLFACE_NONE;
mat.setParameter('uTime',0);mat.setParameter('uIntensity',.8);
mat.update();
function overlayMesh(){
 const m=new pc.Mesh(device);
 const x=.235,y0=-.52,y1=1.08,z=.102;
 m.setPositions([-x,y0,z,x,y0,z,x,y1,z,-x,y1,z]);
 m.setNormals([0,0,1,0,0,1,0,0,1,0,0,1]);
 m.setUvs(0,[0,0,1,0,1,1,0,1]);
 m.setIndices([0,1,2,0,2,3]);m.update();
 const entity=new pc.Entity('RAYO_PREMIUM_PROCEDURAL_SHADER_NOT_PARTICLES');
 entity.addComponent('render',{meshInstances:[new pc.MeshInstance(m,mat)],castShadows:false,receiveShadows:false});
 app.root.addChild(entity);
}
overlayMesh();
let sourceTri=0,sourceMeshes=0;
app.assets.loadFromUrlAndFilename('/tests/rayo-premium-v001/source_original_v03.glb','original_v03.glb','container',(err,asset)=>{
 if(err){window.__rayoError=String(err);document.getElementById('status').textContent='ERROR '+err;return}
 const instance=asset.resource.instantiateRenderEntity();
 instance.name='GENESIS_ORIGINAL_V03_SOURCE_UNMODIFIED';
 app.root.addChild(instance);
 instance.forEach(child=>{if(child.render){sourceMeshes+=child.render.meshInstances.length;
   for(const mi of child.render.meshInstances)sourceTri+=mi.mesh.primitive?.[0]?.count/3||0;
 }});
 if(sourceMeshes!==2 || sourceTri!==2150){window.__rayoError='Wrong source geometry '+sourceMeshes+' / '+sourceTri;return}
 document.getElementById('status').textContent='';
 window.__rayoReady={loaded:true,meshes:sourceMeshes,triangles:sourceTri,shader:'ShaderMaterial GLSL procedural',bloom:bloomInfo,glb_unchanged:true};
 console.log('GENESIS_RAYO_PREMIUM_READY',JSON.stringify(window.__rayoReady));
});
window.__rayoStep=async(frame,frames=48)=>{
 if(!window.__rayoReady)throw Error(window.__rayoError||'NO_GLTF');
 const t=frame/24;
 mat.setParameter('uTime',t);
 mat.setParameter('uIntensity',.80);
 practical.light.intensity=1.10+.45*Math.pow(Math.sin(t*7.),2.);
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 return {frame,t,meshes:sourceMeshes,triangles:sourceTri,bloom:bloomInfo};
};
