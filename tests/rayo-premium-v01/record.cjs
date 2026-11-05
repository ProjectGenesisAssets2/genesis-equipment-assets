const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const {PNG}=require('pngjs');
(async()=>{
 const FPS=12,PER_PHASE=36,CYCLE_SECONDS=1/.33;
 const root='rayo-v07-output';
 fs.mkdirSync(root,{recursive:true});
 const browser=await chromium.launch({headless:true,args:[
  '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const context=await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>{errors.push(String(e));console.error('PAGE_ERROR',e.stack||e.message)});
 page.on('console',m=>{if(m.type()==='error'){errors.push(m.text());console.error('BROWSER_ERROR',m.text())}else if(m.text().includes('GENESIS_RAYO_'))console.log(m.text())});
 page.on('requestfailed',r=>{errors.push(r.url());console.error('REQUEST_FAILED',r.url(),r.failure()?.errorText)});
 await page.goto('http://127.0.0.1:8765/tests/rayo-premium-v01/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:120000});
 const init=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 if(!init||init.loaded!==true||init.triangles!==2150||init.meshes!==2||
    init.geometry!=='actual-worldspace-3d-helix'||init.helix?.turns<3||
    init.bloom!==true||init.sourceGlbEdited!==false)
   throw Error('ORIGINAL_SWORD_OR_TRUE_HELIX_INVALID '+JSON.stringify(init));
 // TWO SEPARATE COMPLETE HELIX TRAVERSALS. The value never ramps inside a phase.
 // Phase 1: fixed intensity 10 for an entire helix cycle.
 // Phase 2: fixed intensity 100 for another entire helix cycle.
 const phases=[{name:'SUAVE',intensity:10},{name:'FUERTE',intensity:100}];
 const samples=[];
 for(let pi=0;pi<phases.length;pi++){
   const phase=phases[pi];
   for(let local=0;local<PER_PHASE;local++){
     const time=local/PER_PHASE*CYCLE_SECONDS;
     const actual=await page.evaluate(async args=>{
       const stage=document.getElementById('cycleStage');
       if(stage)stage.textContent='CICLO '+(args.phaseIndex+1)+'/2 · INTENSIDAD FIJA '+args.intensity+'/100';
       return window.__genesisStep(args.local,args.frames,args.intensity,args.time);
     },{phaseIndex:pi,local,frames:PER_PHASE,intensity:phase.intensity,time});
     if(actual.intensity!==phase.intensity||!Number.isFinite(actual.time)||
        Math.abs(actual.time-time)>1e-7)
       throw Error('CYCLE_FRAME_INVALID '+JSON.stringify({pi,local,actual}));
     const ix=pi*PER_PHASE+local;
     await page.screenshot({path:path.join(root,'cycle_frame_'+String(ix).padStart(3,'0')+'.png'),timeout:60000});
     samples.push({frame:ix,phase:pi+1,intensity:actual.intensity,time:actual.time});
     if(local%12===0)console.log('GENESIS_RAYO_V07_CYCLE',phase.intensity,local+'/'+PER_PHASE);
   }
 }
 const sampleLocal=14, idx10=sampleLocal, idx100=PER_PHASE+sampleLocal;
 fs.copyFileSync(path.join(root,'cycle_frame_'+String(idx10).padStart(3,'0')+'.png'),path.join(root,'Still_010.png'));
 fs.copyFileSync(path.join(root,'cycle_frame_'+String(idx100).padStart(3,'0')+'.png'),path.join(root,'Still_100.png'));
 const midTime=sampleLocal/PER_PHASE*CYCLE_SECONDS;
 await page.evaluate(async ({time,frames})=>window.__genesisStep(0,frames,0,time),{time:midTime,frames:PER_PHASE});
 await page.screenshot({path:path.join(root,'Still_000.png'),timeout:60000});
 function png(name){return PNG.sync.read(fs.readFileSync(path.join(root,name)));}
 const p0=png('Still_000.png'),p10=png('Still_010.png'),p100=png('Still_100.png');
 function luma(p,x,y){const i=(y*p.width+x)*4;return .2126*p.data[i]+.7152*p.data[i+1]+.0722*p.data[i+2];}
 function blueDifference(base,target,x,y){
   const k=(y*target.width+x)*4;
   return target.data[k+2]-base.data[k+2]>15&&target.data[k+2]-target.data[k]>12;
 }
 let electric10=0,electric100=0,variation10=0,variation100=0;
 const a10=png('cycle_frame_008.png'),b10=png('cycle_frame_025.png');
 const a100=png('cycle_frame_044.png'),b100=png('cycle_frame_061.png');
 for(let y=55;y<500;y++)for(let x=603;x<680;x++){
   if(blueDifference(p0,p10,x,y))electric10++;
   if(blueDifference(p0,p100,x,y))electric100++;
   if(Math.abs(luma(a10,x,y)-luma(b10,x,y))>12)variation10++;
   if(Math.abs(luma(a100,x,y)-luma(b100,x,y))>12)variation100++;
 }
 const visual={
   background0:luma(p0,600,205),background10:luma(p10,600,205),
   background100:luma(p100,600,205),bladeBase:luma(p0,640,205),
   electricPixels10:electric10,electricPixels100:electric100,
   motionChanged10:variation10,motionChanged100:variation100
 };
 console.log('GENESIS_RAYO_V07_TWO_CYCLE_VISUAL_CHECK',JSON.stringify(visual));
 if(Math.min(visual.background0,visual.background10,visual.background100)<18||
    visual.bladeBase<18)
   throw Error('BLACK_RECTANGLE_OR_HIDDEN_V175_'+JSON.stringify(visual));
 if(electric10<30||electric100<electric10*2.1)
   throw Error('10_VS_100_NO_VISIBLE_POWER_DIFFERENCE_'+JSON.stringify(visual));
 if(variation10<25||variation100<150)
   throw Error('NOT_BOTH_COMPLETE_MOVING_HELIX_PHASES_'+JSON.stringify(visual));
 if(samples.length!==72||
    samples.slice(0,36).some(x=>x.intensity!==10)||
    samples.slice(36).some(x=>x.intensity!==100)||
    samples[35].time/CYCLE_SECONDS<.95||
    samples[71].time/CYCLE_SECONDS<.95)
   throw Error('INCOMPLETE_CYCLE_OR_UNWANTED_RAMP');
 const audit={
  schema:'Genesis_Rayo_V007_TwoCompleteFixedIntensityCycles',
  status:'experiment-not-approved',
  originalV03SHA256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',
  source:init,realPlayCanvasWebGL2:true,noGeometryChanges:true,
  fps:FPS,framesPerPhase:PER_PHASE,totalFrames:samples.length,
  phaseDurationSeconds:PER_PHASE/FPS,
  completeHelixCycleSeconds:CYCLE_SECONDS,
  sequence:[
   {intensity:10,fromFrame:0,toFrame:35,helixCycles:1,fixedThroughout:true},
   {intensity:100,fromFrame:36,toFrame:71,helixCycles:1,fixedThroughout:true}
  ],
  intensityRamps:false,
  sameCameraAndOriginalMaterials:true,visual,
  sampledFrames:[samples[0],samples[14],samples[35],samples[36],samples[50],samples[71]],
  errors
 };
 fs.writeFileSync(path.join(root,'audit.json'),JSON.stringify(audit,null,2));
 await browser.close();
 if(errors.length)throw Error('PLAYCANVAS_CONSOLE_ERRORS '+JSON.stringify(errors));
 console.log('GENESIS_RAYO_V07_10_THEN_100_FULL_CYCLE_VERIFIED',JSON.stringify({frames:samples.length,visual}));
})().catch(e=>{console.error('GENESIS_RAYO_V07_FAILED',e.stack||e);process.exit(1)});
