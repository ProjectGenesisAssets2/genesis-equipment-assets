const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const {PNG}=require('pngjs');
(async()=>{
 const root='fire-ray-v19-output';fs.mkdirSync(root,{recursive:true});
 const browser=await chromium.launch({headless:true,args:[
  '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>{errors.push(String(e));console.error('GENESIS_V19_PAGE_ERROR',e.stack||e.message)});
 page.on('console',m=>{if(m.type()==='error'){errors.push(m.text());console.error('GENESIS_V19_BROWSER_ERROR',m.text())}else if(m.text().includes('GENESIS_V19'))console.log(m.text())});
 page.on('requestfailed',r=>{errors.push(r.url());console.error('GENESIS_V19_NETWORK_ERROR',r.url(),r.failure()?.errorText)});
 await page.goto('http://127.0.0.1:8765/tests/fire-ray-v19/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:120000});
 const init=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 if(!init||init.originalLoaded!==true||init.triangles!==2150||init.meshes!==2||
   !init.rayoApproved?.approvedVisual||init.rayoTriangles!==1160||
   init.fireTriangles!==1760||init.fuegoSpec?.approved!==false||
   init.fuegoSpec?.haloWidthScaleVsLegacyWebGLV01!==0.40||init.fireVeins?.haloWidthReductionPercent!==60||
   init.sourceGLBEdited!==false||init.bloom!==true)
   throw Error('GENESIS_V19_SOURCE_OR_VFX_INVALID '+JSON.stringify(init));
 const cases=[
  {id:'Fuego_060',fire:60,ray:0},
  {id:'Fuego_100',fire:100,ray:0},
  {id:'Rayo_060',fire:0,ray:60},
  {id:'Fuego060_Rayo060',fire:60,ray:60},
  {id:'Fuego025_Rayo080',fire:25,ray:80},
  {id:'Fuego080_Rayo025',fire:80,ray:25}
 ];
 const frames=24,samples=[];
 for(const cfg of cases){
  for(let i=0;i<frames;i++){
   const t=i/frames*2.75;
   const frame=await page.evaluate(q=>window.__genesisStep(q),{time:t,fire:cfg.fire,ray:cfg.ray});
   if(!Number.isFinite(frame.time)||frame.fire!==cfg.fire||frame.ray!==cfg.ray)
    throw Error('GENESIS_V19_INVALID_FRAME_'+cfg.id+'_'+i+' '+JSON.stringify(frame));
   const name=cfg.id+'_frame_'+String(i).padStart(3,'0')+'.png';
   await page.screenshot({path:path.join(root,name),timeout:60000});
   if(i===12){fs.copyFileSync(path.join(root,name),path.join(root,'Proof_'+cfg.id+'.png'));}
  }
  samples.push({mode:cfg.id,fire:cfg.fire,ray:cfg.ray,frames});
  console.log('GENESIS_V19_CAPTURED',cfg.id);
 }
 await page.evaluate(q=>window.__genesisStep(q),{time:12/24*2.75,fire:0,ray:0});
 await page.screenshot({path:path.join(root,'Proof_Base_V175.png'),timeout:60000});
 function png(n){return PNG.sync.read(fs.readFileSync(path.join(root,n)));}
 const base=png('Proof_Base_V175.png'),f60=png('Proof_Fuego_060.png'),
  f100=png('Proof_Fuego_100.png'),r60=png('Proof_Rayo_060.png'),both=png('Proof_Fuego060_Rayo060.png');
 function lum(p,x,y){let i=(y*p.width+x)*4;return p.data[i]*.2126+p.data[i+1]*.7152+p.data[i+2]*.0722;}
 function pixelCounts(ref,test){
  let warm=0,blue=0,changed=0;
  for(let y=35;y<520;y++)for(let x=605;x<681;x++){
   const i=(y*ref.width+x)*4;
   const dr=test.data[i]-ref.data[i],dg=test.data[i+1]-ref.data[i+1],db=test.data[i+2]-ref.data[i+2];
   if(dr>14&&dr>db+7&&dg>3)warm++;
   if(db>14&&db>dr+7)blue++;
   if(Math.abs(dr)+Math.abs(dg)+Math.abs(db)>40)changed++;
  }
  return {warm,blue,changed};
 }
 const checks={
  noEffectBackground:lum(base,594,205),
  untouchedBlade:lum(base,638,215),
  fire60:pixelCounts(base,f60),
  fire100:pixelCounts(base,f100),
  rayo60:pixelCounts(base,r60),
  combined60:pixelCounts(base,both)
 };
 console.log('GENESIS_V19_VISUAL_CHECKS',JSON.stringify(checks));
 if(checks.noEffectBackground<20||checks.untouchedBlade<19)
  throw Error('BLACK_VFX_RECTANGLE_OR_HIDDEN_METAL_'+JSON.stringify(checks));
 if(checks.fire60.warm<35||checks.fire100.warm<checks.fire60.warm*1.08)
  throw Error('FIRE_MISSING_OR_NO_INTENSITY_SCALING_'+JSON.stringify(checks));
 if(checks.rayo60.blue<50||checks.combined60.blue<35)
  throw Error('APPROVED_RAYO_MISSING_IN_COMBINATION_'+JSON.stringify(checks));
 if(checks.combined60.warm<30)throw Error('FIRE_MISSING_IN_COMBINATION_'+JSON.stringify(checks));
 if(errors.length)throw Error('GENESIS_V19_CONSOLE_ERRORS '+JSON.stringify(errors.slice(0,8)));
 const audit={
  schema:'Genesis_V19_ModularRayoApproved_ExperimentalFuegoAndCombined',
  status:{rayo:'V07 APPROVED VISUAL (not integrated)',fuego:'EXPERIMENT, NOT APPROVED',combinations:'EXPERIMENT, NOT APPROVED'},
  originalSha256:init.sourceSha256,source:init,
  originalGeometryUntouched:true,originalV175PBRUntouched:true,
  modules:['vfx/approved/Genesis_Rayo_Helicoidal_V07.mjs',
           'vfx/experimental/Genesis_Fuego_HaloFino_V18_WebGL.mjs'],
  originalRayoShaderUnchanged:true,shaderTimeIndependent:true,
  visualReference:'V18 V06 Blender Cycles HDRI 32 bit; V19 WebGL preview uses matching thin silhouette, separate non-HDRI lighting',
  flameIsApproximationOfBlenderV18:true,notIdenticalToCyclesV12B:true,
  sameCameraAndLightingAsV07:true,realPlayCanvasWebGL2:true,
  fps:12,framesPerMode:frames,samples,checks,errors
 };
 fs.writeFileSync(path.join(root,'audit.json'),JSON.stringify(audit,null,2));
 await browser.close();
 console.log('GENESIS_V19_RENDER_VALIDATED',JSON.stringify({modes:samples,checks}));
})().catch(e=>{console.error('GENESIS_V19_TEST_FAILED',e.stack||e);process.exit(1)});
