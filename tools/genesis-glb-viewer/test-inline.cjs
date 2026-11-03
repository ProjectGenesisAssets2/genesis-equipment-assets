const {chromium}=require('playwright'),path=require('path'),assert=require('node:assert/strict');(async()=>{
 const b=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  const p=await b.newPage({viewport:{width:1050,height:770},deviceScaleFactor:1});const errors=[];
  p.on('pageerror',e=>errors.push(String(e)));
  p.on('request',r=>{if(!r.url().startsWith('file://'))errors.push('Unexpected external dependency '+r.url())});
  await p.goto('file://'+path.resolve('tools/genesis-glb-viewer/inline-selfcontained.html'),{waitUntil:'load'});
  await p.waitForFunction(()=>window.GENESIS_INLINE_QA?.ok||window.GENESIS_INLINE_QA?.error,{timeout:12000});
  const state=await p.evaluate(()=>window.GENESIS_INLINE_QA);
  assert.deepEqual(state,{ok:true,triangles:3324,error:null});
  assert.deepEqual(errors,[]);
  await p.waitForTimeout(300);
  const ink=await p.locator('canvas').evaluate(c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n;});
  assert.ok(ink>3000,'Model did not draw');
  await p.locator('#front').click();await p.locator('#side').click();await p.locator('#zoomIn').click();
  await p.locator('#spin').click();
  assert.equal(await p.locator('#spin').textContent(),'Activar giro');
  await p.screenshot({path:'/tmp/genesis-inline-glb-proof.png',fullPage:true});
  console.log('PASS_GENESIS_INLINE_GLB',JSON.stringify({triangles:state.triangles,ink,networkRequests:0,errors:0}));
 } finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});