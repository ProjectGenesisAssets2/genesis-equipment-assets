import * as pc from 'playcanvas';
const canvas=document.getElementById('app');
const variants=[
 {id:'01_Fuego25_Rayo80',name:'Fuego + Rayo',first:['Fuego',25],second:['Rayo',80]},
 {id:'02_Fuego80_Rayo25',name:'Fuego + Rayo',first:['Fuego',80],second:['Rayo',25]},
 {id:'03_Hielo80_Sombra25',name:'Hielo + Sombra',first:['Hielo',80],second:['Sombra',25]},
 {id:'04_Hielo25_Sombra80',name:'Hielo + Sombra',first:['Hielo',25],second:['Sombra',80]}
];
const setStatus = t=>{document.getElementById('status').textContent=t;};
const device=await pc.createGraphicsDevice(canvas,{deviceTypes:[pc.DEVICETYPE_WEBGL2],antialias:true,alpha:false});
const options=new pc.AppOptions();
options.graphicsDevice=device;
options.componentSystems=[pc.RenderComponentSystem,pc.CameraComponentSystem,pc.LightComponentSystem];
options.resourceHandlers=[pc.TextureHandler,pc.ContainerHandler];
const app=new pc.AppBase(canvas);
app.init(options);
app.setCanvasResolution(pc.RESOLUTION_FIXED,1280,720);
app.start();
app.scene.ambientLight=new pc.Color(.32,.35,.42);
app.scene.exposure=1.17;
app.scene.toneMapping=pc.TONEMAP_ACES;
const camera=new pc.Entity('STUDIO_CAMERA');
camera.addComponent('camera',{fov:35,nearClip:.01,farClip:40,clearColor:new pc.Color(.014,.019,.031),priority:0});
camera.setPosition(.18,.025,3.60);camera.lookAt(0,0,0);
app.root.addChild(camera);
function studioLight(name,direction,color,intensity){
 const e=new pc.Entity(name);
 e.addComponent('light',{type:'directional',color:new pc.Color(...color),intensity,castShadows:false});
 e.setEulerAngles(...direction);
 app.root.addChild(e);return e;
}
studioLight('STUDIO_KEY', [25,48,0],[1,.84,.67],2.35);
studioLight('STUDIO_FILL',[15,-68,0],[.48,.67,1],2.05);
studioLight('LONG_BLADE_STRIP',[-45,12,0],[1,1,1],1.6);
const channelLight=new pc.Entity('CHANNEL_LIGHT');
channelLight.addComponent('light',{type:'omni',color:new pc.Color(.18,.49,1),intensity:1.0,range:2.4,castShadows:false});
channelLight.setPosition(0,.30,.21);app.root.addChild(channelLight);
function hash(n){const x=Math.sin(n*127.1+78.233)*43758.5453123;return x-Math.floor(x);}
function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
function makeMat(rgb,intensity=2,opacity=.86){
 const m=new pc.StandardMaterial();
 m.useLighting=false;
 m.diffuse=new pc.Color(0,0,0);
 m.emissive=new pc.Color(...rgb);
 m.emissiveIntensity=intensity;
 m.opacity=opacity;
 m.blendType=pc.BLEND_ADDITIVE;
 m.depthWrite=false;
 m.depthTest=true;
 m.cull=pc.CULLFACE_NONE;
 m.update();
 return m;
}
const mats={
 flame:makeMat([1,.19,.025],3.2,.65),flamegold:makeMat([1,.66,.08],3,.70),
 ember:makeMat([1,.39,.10],3,.95),ray:makeMat([.045,.38,1],4.9,.75),
 raycore:makeMat([.68,.89,1],4.4,.95),ice:makeMat([.34,.82,1],2.5,.81),
 frost:makeMat([.86,.95,1],2.0,.74),shadow:makeMat([.36,.08,.62],2.6,.40),
 purple:makeMat([.59,.20,.91],2.4,.67)
};
function makePiece(name,type,mat){
 const e=new pc.Entity(name);
 e.addComponent('render',{type,material:mat,castShadows:false,receiveShadows:false});
 app.root.addChild(e);
 return e;
}
const sprites=[];
function buildSprites(channel,count,kind,material){
 for(let i=0;i<count;i++){
  const e=makePiece(channel+'_'+i,kind,material(i));
  sprites.push({e,i,channel,seed:hash(i*4.73+channel.length*91.7)});
 }
}
buildSprites('Fuego',76,'sphere',i=>i%4===0?mats.flamegold:i%6===0?mats.ember:mats.flame);
buildSprites('Hielo',74,'cone',i=>i%3===0?mats.frost:mats.ice);
buildSprites('Sombra',75,'sphere',i=>i%4===0?mats.purple:mats.shadow);
const lightning=[];
for(let arc=0;arc<7;arc++){
 const links=[];
 for(let s=0;s<14;s++){
  const outer=makePiece('RAYO_ARC_HALO_'+arc+'_'+s,'sphere',mats.ray);
  const core=makePiece('RAYO_ARC_CORE_'+arc+'_'+s,'sphere',mats.raycore);
  links.push([outer,core]);
 }
 lightning.push(links);
}
function placeSegment(e,ax,ay,az,bx,by,bz,width){
 const p0=new pc.Vec3(ax,ay,az),p1=new pc.Vec3(bx,by,bz);
 const diff=p1.clone().sub(p0); const len=diff.length();
 e.setPosition(p0.clone().add(p1).mulScalar(.5));
 e.setRotation(new pc.Quat().setFromDirections(pc.Vec3.UP,diff.normalize()));
 e.setLocalScale(width,len*.58,width);
}
let sourceMeshes=0, sourceTri=0;
function showVariant(vi){
 const v=variants[vi];
 const set=(key,val,bar,level,color)=>{
  document.getElementById(key).textContent=val;
  document.getElementById(bar).style.width=level+'%';
  document.getElementById(bar).style.background=color;
 };
 document.getElementById('name').textContent=v.name;
 document.getElementById('subtitle').innerHTML=(vi<2?'LLAMAS Y DESCARGAS':'ESCARCHA Y SOMBRAS')+'<br>EFECTOS ANIMADOS EN TIEMPO REAL';
 set('labelA',v.first[0].toUpperCase(),'barA',v.first[1],v.first[0]==='Fuego'?'#f68b42':'#79d8ff');
 set('labelB',v.second[0].toUpperCase(),'barB',v.second[1],v.second[0]==='Rayo'?'#378ef5':'#a969df');
 document.getElementById('valueA').textContent=v.first[1]+' / 100';
 document.getElementById('valueB').textContent=v.second[1]+' / 100';
}
function setTime(vi,frame){
 showVariant(vi);
 const v=variants[vi],lv={Fuego:0,Rayo:0,Hielo:0,Sombra:0};lv[v.first[0]]=v.first[1];lv[v.second[0]]=v.second[1];
 const t=frame/18, fire=lv.Fuego/100,ray=lv.Rayo/100,ice=lv.Hielo/100,shadow=lv.Sombra/100;
 const mix=vi<2?'fire_ray':'ice_shadow';
 const flash=(.75+.25*Math.sin(t*15+1.4)**2);
 channelLight.light.color=new pc.Color(...(vi<2?[.38,.52,1]:[.34,.31,.72]));
 channelLight.light.intensity=(vi<2?1.6:.85)*Math.max(fire,ray,ice,shadow)*flash;
 for(const p of sprites){
  const i=p.i,h=p.seed,ch=p.channel,L=lv[ch]/100;
  const active=i<Math.round((ch==='Fuego'?72:ch==='Hielo'?72:70)*L);
  if(!active){p.e.enabled=false;continue}
  p.e.enabled=true;
  const r=hash(i*73.13),r2=hash(i*31.79+7);
  if(ch==='Fuego'){
    const life=(r+t*(.24+.37*L))%1;
    const originY=-.43+r2*1.22;
    const y=originY+.24*life*(.5+L);
    const side=(i%2?-1:1)*(.058+.035*r);
    const wobble=.016*Math.sin(t*9+i*.62);
    const x=side+wobble+life*(i%2?-.02:.02);
    const scale=(.013+.036*L)*Math.sin(Math.PI*clamp(life,.08,.94))*(.7+r2*.8);
    p.e.setPosition(x,y,.083+.02*r);
    p.e.setLocalScale(scale*(.68+.25*Math.sin(t*6+i)),scale*2.25,scale*.46);
  } else if(ch==='Hielo'){
    const y=-.43+1.39*r;
    const grow=clamp((t*.14+.35+r2*.35)*L*2.0,0,1);
    const edge=(i%2?-1:1)*(.064-(.015*Math.max(0,y-.7)));
    const x=edge+.008*Math.sin(i*11+t*.9);
    const scale=(.008+.038*L)*(.45+r2*.55)*grow;
    p.e.setPosition(x,y,.052+.018*r2);
    p.e.setEulerAngles(0,0,(i%2?-40:40)+Math.sin(i*3.2)*17);
    p.e.setLocalScale(scale*.38,scale*(2.+r2*2.4),scale*.24);
    // Frost also reaches the pommel, without modifying the hilt material.
    if(i%9===0){p.e.setPosition((r-.5)*.09,-.83+(r2-.5)*.18,.077)}
  } else {
    const life=(r+t*(.11+.20*L))%1;
    const y=-.43+r2*1.34+.17*life;
    const side=(i%2?-1:1)*(.10+.065*r);
    const x=side+.043*Math.sin(t*2.4+i*.91)+.02*life;
    const size=(.028+.085*L)*(.4+.6*Math.sin(Math.PI*life));
    p.e.setPosition(x,y,.04+.02*r);
    p.e.setLocalScale(size*.8,size*1.45,size*.48);
  }
 }
 // Each arc is a truly changing segmented 3D path, not a baked emissive texture.
 for(let a=0;a<lightning.length;a++){
  const on=a<Math.round(1+6*ray);
  const links=lightning[a];
  for(let s=0;s<links.length;s++){
   const [out,core]=links[s];out.enabled=core.enabled=!!on;
   if(!on)continue;
   const start=-.38+hash(a*7)*.4;
   const total=.54+hash(a*5+1)*.8;
   const fa=s/links.length,fb=(s+1)/links.length;
   function pos(u){
    const y=clamp(start+u*total,-.40,.99);
    const bend=.042*Math.sin(y*14+t*18+a*3.7)+.014*Math.sin(y*71+t*39+a);
    const jitter=.022*Math.sin(y*170+t*51+a*9.1);
    const x=(a%3-1)*(.035+.018*ray)+bend+jitter*(1.2-.5*ray);
    const z=.088+.009*Math.sin(t*13+a);
    return [x,y,z];
   }
   const p=pos(fa),q=pos(fb);
   const w=(.0030+.004*ray)*(.8+.2*Math.sin(t*37+a));
   placeSegment(out,...p,...q,w*2.0);
   placeSegment(core,...p,...q,w*.65);
  }
 }
 // diffuse bloom-like emissive brightness is handled by glow materials and post grading.
 window.__genesisCurrent={variant:v.id,frame,levels:lv,engine:'PlayCanvas',triangles:sourceTri,sourceMeshes};
}
function loadSword(){
 app.assets.loadFromUrlAndFilename('/tests/pc-vfx-video/source_original_v03.glb','original_v03.glb','container',(err,asset)=>{
  if(err){window.__genesisError=String(err);setStatus('ERROR '+err);console.error(err);return}
  const instance=asset.resource.instantiateRenderEntity();
  instance.name='GENESIS_V03_ORIGINAL_SOURCE';
  app.root.addChild(instance);
  instance.setLocalPosition(0,0,0);
  // Keep source V03 PBR maps and geometry completely unchanged.
  instance.forEach(child=>{if(child.render){sourceMeshes+=child.render.meshInstances.length;
   for(const mesh of child.render.meshInstances){sourceTri+=mesh.mesh.primitive?.[0]?.count/3||0}
  }});
  setStatus('');
  window.__genesisReady={loaded:true,meshes:sourceMeshes,triangles:sourceTri,renderer:'PlayCanvas WebGL2'};
  console.log('GENESIS_PC_VFX_LOAD',JSON.stringify(window.__genesisReady));
  setTime(0,0);
 });
}
window.__genesisStep=async(variant,frame)=>{
 if(!window.__genesisReady)throw Error(window.__genesisError||'NOT_READY');
 if(!variants[variant])throw Error('INVALID_VARIANT');
 setTime(variant,frame);
 await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 return window.__genesisCurrent;
};
loadSword();
