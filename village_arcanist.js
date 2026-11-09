/* Project Genesis v0.14b — approved V027 mineral emission with neutral frontal fill.
 * Visual source and its WebGL LOD are pinned to an immutable public commit.
 * This is decorative scenery: the door remains closed and keeps workshop collision.
 */
import {Entity,Color,Texture,FILTER_LINEAR} from 'playcanvas';

export const ARCANE_DOOR_SOURCE = 'https://raw.githubusercontent.com/ProjectgenesisAssets/genesis-workshop-assets/588de60f6888c7e3d4db20e31ee60b3e19918968/deliverables/door_v027/webgl/Arcanist_Door_V027_WebGL.glb';


// Animate the emissive masks themselves: the light climbs through the original
// mineral veins in two uneven, offset waves. The base/normal/roughness PBR maps
// and V027 geometry are not changed.
function animateArcaneVeins(app,pivot,visual){
 const mobile=globalThis.GenesisDevice?.safePreviews===true;
 const size=mobile?384:512;
 const mats=new Map(),sources=[];
 for(const render of visual.findComponents('render')){
  for(const mi of render.meshInstances||[]){
   const original=mi.material;
   if(!original?.emissiveMap)continue;
   if(!mats.has(original)){
    const material=original.clone();
    material.emissive=new Color(.18,.62,1);
    material.emissiveIntensity=5.2; // Blender V027 material emission strength
    material.update();
    mats.set(original,material);
    // The WebGL GLB has static emissive WebP maps and NO animation tracks.
    // Recover the decoded source once, animate at a capped 6–9 Hz.
    try{
     const source=original.emissiveMap.getSource?.();
     const canvas=document.createElement('canvas');canvas.width=canvas.height=size;
     const ctx=canvas.getContext('2d',{willReadFrequently:true});
     if(!source||!ctx)throw new Error('Emissive image unavailable');
     ctx.drawImage(source,0,0,size,size);
     const originalPixels=ctx.getImageData(0,0,size,size);
     const current=ctx.createImageData(size,size);
     const texture=new Texture(app.graphicsDevice,{name:'V027 · corrientes arcanas animadas',srgb:true,mipmaps:false,minFilter:FILTER_LINEAR,magFilter:FILTER_LINEAR});
     texture.setSource(canvas);
     material.emissiveMap=texture;material.update();
     sources.push({ctx,canvas,texture,base:originalPixels.data,pixels:current,offset:sources.length*.37});
    }catch(error){
     console.warn('Arcanista: emisión animada recurre a pulso de intensidad',error);
    }
   }
   mi.material=mats.get(original);
  }
 }
 const debug={textureMasks:sources.length,lights:0,updatedFrames:0,phaseA:0,phaseB:0,emissionStrength:5.2,version:'v0.14b'};
 globalThis.__genesisArcaneVeinsStatus=debug;
 let elapsed=0,acc=0;
 // Light the actual mineral/metal door surface, not just the animated emissive veins.
 // World-fixed relative to the doorway, so turning the camera cannot change it.
 const fill=new Entity('Arcanista · luz frontal mineral suave V027');
 fill.addComponent('light',{type:'omni',color:new Color(.76,.83,1),range:3.4,intensity:mobile?1.05:1.3,castShadows:false});
 fill.setLocalPosition(0,1.38,.91);pivot.addChild(fill);
 debug.fillLight=true;
 const lights=[];
 for(const [index,x] of (mobile?[[-1,-.18]]:[[0,-.20],[1,.23]])){
  const light=new Entity('Corriente arcana ascendente '+index);
  light.addComponent('light',{type:'omni',color:new Color(.18,.62,1),range:1.8,intensity:1.0,castShadows:false});
  light.setLocalPosition(x,.25,.45);pivot.addChild(light);lights.push(light);
 }
 debug.lights=lights.length+1;
 const tick=dt=>{
  if(!pivot.enabled||!visual.enabled)return;
  elapsed+=Math.min(Math.max(0,dt||0),.08);
  acc+=dt||0;
  // Blender approved V027 travel: two offset crests climbing from -0.35m to 2.73m.
  const riseA=((elapsed*.74)%3.08)-.35,riseB=riseA-.30;
  debug.phaseA=riseA;debug.phaseB=riseB;
  for(let i=0;i<lights.length;i++){
   const phase=i===0?riseA:riseB;
   lights[i].setLocalPosition(i===0?-.20:.23,Math.max(.12,Math.min(2.3,phase)),.43);
   lights[i].light.intensity=(i===0?1.3:.75)*(.72+.28*Math.sin(elapsed*2.1+i));
  }
  for(const [i,material] of [...mats.values()].entries()){
   // Residual glow stays visible between two upward-moving energy currents.
   material.emissiveIntensity=5.2*(.92+.08*Math.sin(elapsed*3.1+i*.8));
   material.update();
  }
  if(acc<(mobile?1/6:1/9))return;
  acc=0;
  for(const source of sources){
   const {ctx,texture,base,pixels,offset}=source,output=pixels.data;
   for(let y=0;y<size;y++){
    const height=(1-y/(size-1))*2.32,row=y*size*4;
    for(let x=0;x<size;x++){
     // Small mineral irregularity keeps the effect from looking like neon.
     const jitter=.15*Math.sin(x*.049+y*.017)+.10*Math.cos(x*.019-y*.031);
     const mineralHeight=height+jitter;
     const bandA=Math.exp(-13.5*Math.pow(mineralHeight-riseA,2));
     const bandB=Math.exp(-17.0*Math.pow(mineralHeight-riseB+offset*.03,2));
     const factor=.28+2.65*(bandA+.55*bandB);
     const n=row+x*4;
     output[n]=Math.min(255,base[n]*factor);
     output[n+1]=Math.min(255,base[n+1]*factor);
     output[n+2]=Math.min(255,base[n+2]*factor);
     output[n+3]=base[n+3];
    }
   }
   try{ctx.putImageData(pixels,0,0);texture.upload();debug.updatedFrames++}
   catch(error){console.warn('Arcanista V027: error actualizando la emisión',error)}
  }
 };
 app.on('update',tick);
 return {animatedTextures:sources.length,lights:lights.length+1};
}

export function mountArcanePortal(app,building,fallbackDoor,options={}){
 const pivot=new Entity('Arcanista · puerta mágica V027 · cerrada');
 pivot.setLocalPosition(0,0,.12);
 building.addChild(pivot);
 let phase='loading',detail='';
 let resolveInitial;
 const initialReady=new Promise(resolve=>{resolveInitial=resolve;});
 const settle=()=>{globalThis.__genesisArcaneDoorStatus=report();if(phase==='ready')options.onResourceLoaded?.('door:arcane:V027');resolveInitial(report());};
 const report=()=>({version:'V027',phase,detail,url:ARCANE_DOOR_SOURCE});
 globalThis.__genesisArcaneDoorStatus=report();
 app.assets.loadFromUrl(ARCANE_DOOR_SOURCE,'container',(error,asset)=>{
  if(error||!asset?.resource){
   phase='fallback';detail=String(error||'GLB sin recurso');
   console.warn('Arcanista V027: se conserva la puerta anterior:',detail);
   settle();return;
  }
  let visual;
  try{
   visual=asset.resource.instantiateRenderEntity();
   pivot.addChild(visual);
   const renders=visual.findComponents('render');
   if(!renders.length)throw new Error('GLB V027 sin superficies renderizables');
   for(const renderer of renders){renderer.castShadows=true;renderer.receiveShadows=true}
   const energy=animateArcaneVeins(app,pivot,visual);
   fallbackDoor.enabled=false;
   phase='ready';detail=renders.length+' superficies · '+energy.animatedTextures+' máscaras emissive animadas · '+energy.lights+' corrientes';
  }catch(err){
   visual?.destroy();
   phase='fallback';detail=String(err?.message||err);
   console.warn('Arcanista V027: falla de importación:',detail);
  }
  settle();
 });
 return Object.freeze({pivot,status:report,initialReady});
}
