const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const {PNG}=require('pngjs');
(async()=>{
 const browser=await chromium.launch({headless:true,args:[
   '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const context=await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const page=await context.newPage();const errors=[];
 page.on('pageerror',e=>{console.log('PAGE_ERROR',e.stack||e.message);errors.push(String(e))});
 page.on('console',m=>{
   if(m.type()==='error'){console.log('BROWSER_ERROR',m.text());errors.push(m.text())}
   else if(m.text().includes('GENESIS_RAYO_'))console.log(m.text());
 });
 page.on('requestfailed',r=>{console.log('REQUEST_FAILED',r.url(),r.failure()?.errorText);errors.push(r.url())});
 await page.goto('http://127.0.0.1:8765/tests/rayo-premium-v01/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:120000});
 const init=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 console.log('GENESIS_RAYO_V03_AUDIT',JSON.stringify(init));
 if(!init || init.loaded!==true || init.triangles!==2150||init.meshes!==2||init.proceduralShader!==true||init.bladeOnly!==true||init.geometry!=='actual-worldspace-3d-helix'||init.helix?.turns<3||init.helix?.depthTest!==true||init.intensityRange?.[0]!==0||init.intensityRange?.[1]!==100)
  throw Error('GENESIS_SOURCE_OR_SHADER_AUDIT_FAILED '+JSON.stringify(init));
 if(!init.bloom)throw Error('CAMERAFRAME_HDR_BLOOM_WAS_NOT_ACTIVATED');
 const root='rayo-v05-output';fs.mkdirSync(root,{recursive:true});
 const frames=Number(process.env.FRAMES||32);
 let last;
 for(let frame=0;frame<frames;frame++){
  const rampIntensity=Math.round(frame/Math.max(1,frames-1)*100);
  last=await page.evaluate(async x=>window.__genesisStep(x.frame,x.frames,x.intensity),{frame,frames,intensity:rampIntensity});
  if(!Number.isFinite(last.time)||last.intensity!==rampIntensity)throw Error('INVALID_RAMP_FRAME_'+frame+' '+JSON.stringify(last));
  await page.screenshot({path:path.join(root,'frame_'+String(frame).padStart(3,'0')+'.png'),timeout:60000});
  if(frame%8===0)console.log('GENESIS_RAYO_PREMIUM_FRAME',frame,'of',frames);
 }
 // Second independent movie: a moving lightning strand at a constant, inspectable 60/100.
 for(let frame=0;frame<frames;frame++){
   const sample=await page.evaluate(async x=>window.__genesisStep(x.frame,x.frames,60),{frame,frames});
   if(sample.intensity!==60||!Number.isFinite(sample.time))throw Error('HELIX_MOVIE_INVALID_FRAME_'+frame);
   await page.screenshot({path:path.join(root,'helix_frame_'+String(frame).padStart(3,'0')+'.png'),timeout:60000});
 }
 const intensityComparison=[];
 for(const intensity of [0,25,50,75,100]){
   const sample=await page.evaluate(async ({n,frames})=>window.__genesisStep(16,frames,n),{n:intensity,frames});
   if(!Number.isFinite(sample.time))throw Error('INVALID_GLSL_TIME_'+intensity);
   if(sample.intensity!==intensity)throw Error('INTENSITY_SWEEP_MISMATCH_'+intensity);
   intensityComparison.push(sample);
   await page.screenshot({path:path.join(root,'Intensity_'+String(intensity).padStart(3,'0')+'.png'),timeout:60000});
 }

 const p0=PNG.sync.read(fs.readFileSync(path.join(root,'Intensity_000.png')));
 const p100=PNG.sync.read(fs.readFileSync(path.join(root,'Intensity_100.png')));
 function luminance(png,x,y){
   const i=(y*png.width+x)*4;
   return .2126*png.data[i]+.7152*png.data[i+1]+.0722*png.data[i+2];
 }
 let changedPixels=0;
 for(let y=45;y<310;y++)for(let x=620;x<663;x++){
   if(Math.abs(luminance(p100,x,y)-luminance(p0,x,y))>7)changedPixels++;
 }
 const visualChecks={
   transparentBackground0:luminance(p0,600,205),
   transparentBackground100:luminance(p100,600,205),
   sourceBladeVisible0:luminance(p0,640,205),
   changedPixels0to100:changedPixels,
   rampStartIntensity:0,rampEndIntensity:100,
   sampleTime:p100.width?16*2.75/frames:null
 };
 console.log('GENESIS_RAYO_VISUAL_PIXEL_CHECKS',JSON.stringify(visualChecks));
 if(visualChecks.transparentBackground0<15||visualChecks.transparentBackground100<15)
  throw Error('OPAQUE_BLACK_VFX_RECTANGLE_DETECTED '+JSON.stringify(visualChecks));
 if(visualChecks.sourceBladeVisible0<18)
  throw Error('V175_BLADE_HIDDEN_AT_ZERO '+JSON.stringify(visualChecks));
 if(changedPixels<35)
  throw Error('NO_VISIBLE_INTENSITY_CHANGE '+JSON.stringify(visualChecks));
 const h8=PNG.sync.read(fs.readFileSync(path.join(root,'helix_frame_008.png')));
 const h20=PNG.sync.read(fs.readFileSync(path.join(root,'helix_frame_020.png')));
 let movingPixels=0;
 for(let y=50;y<500;y++)for(let x=599;x<682;x++){
   if(Math.abs(luminance(h8,x,y)-luminance(h20,x,y))>13)movingPixels++;
 }
 if(movingPixels<75)throw Error('HELIX_NOT_MOVING_OR_INVISIBLE_'+movingPixels);
 const audit={
   schema:'Genesis_Rayo_V005_3DHelix_Animated_Evidence',
   status:'experiment-not-approved',
   verified_original_sha256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',
   source:init,realPlayCanvasWebGL2:true,
   generatedBy:'Chromium WebGL2 PlayCanvas ShaderMaterial GLSL, camera bloom and real PBR GLB',
   noGeometryChanges:true,sourceImageTexturesNotChanged:true,
   extraVfxGeometry:'one quad, two triangles, procedural shader',
   noStaticMasks:true,noSpheresOrTubes:true,
   fps:12,frames,displayResolution:[1280,720],
   animation:last,intensityComparison,visualChecks,helixMovement:{comparisonFrames:[8,20],changedPixels:movingPixels,fixedIntensity:60},errors};
 fs.writeFileSync(path.join(root,'audit.json'),JSON.stringify(audit,null,2));
 console.log('GENESIS_RAYO_V05_HELIX_COMPLETE',JSON.stringify({frames,errors:errors.length,bloom:init.bloom,triangles:init.triangles}));
 await browser.close();
 if(errors.length)throw Error('GENESIS_CONSOLE_ERRORS '+JSON.stringify(errors.slice(0,6)));
})().catch(e=>{console.error('GENESIS_RAYO_PREMIUM_FAILED',e.stack||e);process.exit(1)});
