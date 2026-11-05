const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const {PNG}=require('pngjs');
(async()=>{
 const root='universal-v09-output';fs.mkdirSync(root,{recursive:true});
 const browser=await chromium.launch({headless:true,args:[
  '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>{errors.push(String(e));console.log('PAGE_ERROR',e.stack||e.message)});
 page.on('console',m=>{if(m.type()==='error'){errors.push(m.text());console.log('CONSOLE_ERROR',m.text())}else if(m.text().includes('GENESIS_V09_'))console.log(m.text())});
 page.on('requestfailed',r=>{errors.push(r.url());console.log('REQUEST_FAILED',r.url(),r.failure()?.errorText)});
 await page.goto('http://127.0.0.1:8765/tests/universal-v09/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:120000});
 const init=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 console.log('GENESIS_V09_INITIAL',JSON.stringify(init));
 const expected=['Luz','Sombra','Fuego','Hielo','Naturaleza','Tierra','Rayo'];
 if(!init||init.channelCount!==7||expected.some(c=>!init.channels.includes(c))||
   init.sword?.triangles!==2150||init.sword?.meshes!==2||
   init.shield?.computedSilhouetteVertices<5||init.productionShieldGLBTested!==false||
   init.originalSourceEdited!==false)throw Error('V09_INIT_FAILED '+JSON.stringify(init));
 const set=async(q)=>page.evaluate(x=>window.__genesisStep(x),q);
 await set({time:.85,channel:'Rayo',intensity:0});
 await page.screenshot({path:path.join(root,'Baseline_0.png'),timeout:60000});
 const captures=[];
 for(const channel of expected){
   const shortName=channel.normalize('NFD').replace(/[\u0300-\u036f]/g,'');
   for(const intensity of [0,10,60,100]){
     const state=await set({time:1.23,channel,intensity});
     if(state.sword[channel]!==intensity||state.shield[channel]!==intensity)
       throw Error('LEVEL_MISMATCH_'+channel+'_'+intensity);
     if(Object.keys(state.sword).filter(c=>c!==channel&&state.sword[c]>0).length)
       throw Error('CHANNEL_LEAKAGE_'+channel);
     if(intensity===0||intensity===60||intensity===100)
       await page.screenshot({path:path.join(root,shortName+'_'+String(intensity).padStart(3,'0')+'.png'),timeout:60000});
     captures.push({channel,intensity,state:'independent on sword/shield'});
   }
   console.log('GENESIS_V09_CHANNEL_RENDERED',channel);
 }
 const combo=await set({time:1.3,channel:'Fuego',intensity:60,
   swordLevels:{Fuego:60,Rayo:70},shieldLevels:{Fuego:60,Rayo:70}});
 if(combo.sword.Fuego!==60||combo.sword.Rayo!==70||
   combo.shield.Fuego!==60||combo.shield.Rayo!==70)
   throw Error('FIRE_RAY_COMBINATION_INCORRECT');
 await page.screenshot({path:path.join(root,'Fuego060_Rayo070_BothTargets.png'),timeout:60000});
 function png(n){return PNG.sync.read(fs.readFileSync(path.join(root,n)));}
 function diff(base,img,x1,x2){
   let count=0,red=0,blue=0;
   for(let y=55;y<600;y++)for(let x=x1;x<x2;x++){
     const k=(y*base.width+x)*4;
     const r=img.data[k]-base.data[k],g=img.data[k+1]-base.data[k+1],b=img.data[k+2]-base.data[k+2];
     if(Math.abs(r)+Math.abs(g)+Math.abs(b)>30){count++;if(r>b+8)red++;if(b>r+8)blue++;}
   }
   return {count,red,blue};
 }
 const baseline=png('Baseline_0.png'),coverage=[];
 for(const channel of expected){
   const file=channel.normalize('NFD').replace(/[\u0300-\u036f]/g,'')+'_060.png';
   const shot=png(file);
   const sword=diff(baseline,shot,260,610),shield=diff(baseline,shot,670,1050);
   coverage.push({channel,sword,shield});
   if(sword.count<18||shield.count<18)
     throw Error('CHANNEL_VISUALLY_MISSING_ON_SWORD_OR_SHIELD_'+JSON.stringify({channel,sword,shield}));
 }
 if(errors.length)throw Error('WEBGL_ERRORS '+JSON.stringify(errors.slice(0,12)));
 const audit={
  schema:'GenesisUniversalV09SevenChannelsSwordShieldFixture',
  experimental:true,approvedRayoIntact:true,
  actualV03SwordVerified:true,actualApprovedShieldVerified:false,
  productionShieldFixtureOnly:true,
  expectedChannels:expected,baseChannelIsNotElement:true,
  natureIsNotPoison:true,
  targetTypes:['sword-real-v03','shield-noncircular-test-fixture'],
  hdrEnvironmentInThisValidation:false,
  independentIntensityRange:[0,100],
  originalPBRPreserved:true,vertexExtractionAndHullVerified:true,
  init,captures,combo,coverage,errors
 };
 fs.writeFileSync(path.join(root,'audit.json'),JSON.stringify(audit,null,2));
 console.log('GENESIS_V09_SEVEN_CHANNELS_COVERAGE',JSON.stringify(coverage));
 await browser.close();
})().catch(e=>{console.error('GENESIS_V09_FAILED',e.stack||e);process.exit(1)});
