// V20C.1: capture true WebGL2 frames with 24 Hz game-time, original fire unchanged.
// Source frames: 72 output + 12 seam overlap at 24 fps, 3.0 s natural video loop.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const {PNG}=require('pngjs');
(async()=>{
 const root='fuego-v20c1-output';fs.mkdirSync(root,{recursive:true});
 const fps=24,loopFrames=72,overlapFrames=12,sourceFrames=loopFrames+overlapFrames;
 const cases=[{id:'Fuego_060',fire:60},{id:'Fuego_100',fire:100}];
 const browser=await chromium.launch({headless:true,args:[
  '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>{errors.push(e.message);console.error('GENESIS_V20C1_PAGE_ERROR',e.stack||e.message)});
 page.on('console',m=>{if(m.type()==='error'){errors.push(m.text());console.error('GENESIS_V20C1_BROWSER_ERROR',m.text())}});
 page.on('requestfailed',r=>{errors.push(r.url());console.error('GENESIS_V20C1_REQUEST_FAILED',r.url(),r.failure()?.errorText)});
 await page.goto('http://127.0.0.1:8765/tests/fuego-v20c1/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:90000});
 const source=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 if(!source||source.originalLoaded!==true||source.triangles!==2150||source.meshes!==2||
   source.sourceSha256!=='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'||
   source.fireTriangles!==824||source.fireVeins?.flameTongues!==8||
   source.fireVeins?.heatTriangles!==440||source.fireVeins?.tongueTriangles!==384||
   source.fireVeins?.outerElectricalOrbitAbsent!==true||
   source.fireVeins?.noLegacyLongRibbons!==true||
   source.fuegoSpec?.approved!==false||source.rayoTriangles!==0||
   source.sourceGLBEdited!==false||source.bloom!==true)
  throw Error('GENESIS_V20C1_SOURCE_OR_FIRE_INVALID '+JSON.stringify(source));
 const results=[];
 for(const config of cases) {
  for(let i=0;i<sourceFrames;i++){
   const time=i/fps;
   const displayed=await page.evaluate(q=>window.__genesisStep(q),{time,fire:config.fire});
   if(displayed.fire!==config.fire||displayed.sliderFire!==config.fire||
     displayed.ray!==0||Math.abs(displayed.time-time)>1e-8)
     throw Error('GENESIS_V20C1_FRAME_STATE_WRONG '+JSON.stringify({config,i,displayed}));
   const name=config.id+'_source_frame_'+String(i).padStart(3,'0')+'.png';
   await page.screenshot({path:path.join(root,name),timeout:60000});
   if(i===Math.floor(loopFrames/2))
     fs.copyFileSync(path.join(root,name),path.join(root,'Proof_'+config.id+'.png'));
  }
  results.push({mode:config.id,intensity:config.fire,sourceFrames,loopFrames,overlapFrames,fps});
  console.log('GENESIS_V20C1_SOURCE_CAPTURED',JSON.stringify(results[results.length-1]));
 }
 await page.evaluate(q=>window.__genesisStep(q),{time:1.5,fire:0});
 await page.screenshot({path:path.join(root,'Proof_Base_V175.png'),timeout:60000});
 if(errors.length)throw Error('GENESIS_V20C1_BROWSER_FAILURE '+JSON.stringify(errors.slice(0,12)));
 const base=PNG.sync.read(fs.readFileSync(path.join(root,'Proof_Base_V175.png')));
 const lit=PNG.sync.read(fs.readFileSync(path.join(root,'Proof_Fuego_060.png')));
 let changed=0;
 for(let y=40;y<500;y++)for(let x=615;x<677;x++){
  const k=(y*base.width+x)*4;
  if(Math.abs(lit.data[k]-base.data[k])+Math.abs(lit.data[k+1]-base.data[k+1])>24)changed++;
 }
 if(changed<90)throw Error('FIRE_HAS_DISAPPEARED '+changed);
 const audit={
  schema:'Genesis_V20C1_LoopCapture_24fps_UnchangedShader',
  source,visualStatus:'experimental_user_review_required',
  shaderApproved:false,shaderEdited:false,originalModelEdited:false,
  sourceEffect:'Genesis_Fuego_V20C_CalorYFlamas.mjs original SHA fc4a3722e7c07b33d034b6d1ead5504f480a6345',
  originalLoop:{sourceFrames:24,shadersNonPeriodic:true,gifFps:10,loopDiscontinuity:true},
  improvedLoop:{fps,loopFrames,overlapFrames,sourceFrames,periodSeconds:loopFrames/fps,
    seamMethod:'crossfade source window [T,T+overlap] to [0,overlap] at beginning; last frame to first follows real WebGL temporal progression',
    noFrameInterpolationBetweenRealCaptures:true},
  cases:results,changedPixelsAt60:changed,errors
 };
 fs.writeFileSync(path.join(root,'capture_audit.json'),JSON.stringify(audit,null,2));
 await browser.close();
 console.log('GENESIS_V20C1_CAPTURE_VALIDATED',JSON.stringify({results,changed}));
})().catch(e=>{console.error('GENESIS_V20C1_CAPTURE_FAILED',e.stack||e);process.exit(1)});
