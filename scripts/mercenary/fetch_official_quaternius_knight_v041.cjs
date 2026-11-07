// Project Genesis: use the real browser path to the free, publisher-hosted
// Quaternius Standard ZIP. Never follow paid Source files or use private URLs.
const { chromium } = require('playwright');
const fs = require('fs');
const os = require('os');
const path = require('path');
const DEST='/tmp/genesis_v041/quaternius_fantasy_standard.zip';
(async()=>{
  fs.mkdirSync(path.dirname(DEST),{recursive:true});
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({acceptDownloads:true});
  try {
    const url='https://quaternius.itch.io/modular-character-outfits-fantasy/purchase';
    await page.goto(url,{waitUntil:'domcontentloaded',timeout:65000});
    console.log('V041_PURCHASE_URL',page.url());
    let b=page.locator('a.direct_download_btn').first();
    if (!await b.count()) throw new Error('Official FREE "No thanks" button missing');
    const label=(await b.innerText()).trim();
    console.log('V041_FREE_BUTTON',label);
    if(!/no thanks|download/i.test(label))throw new Error('No free publisher-supported download route');
    const navigation=page.waitForURL(url=>!/\/purchase(?:[?#]|$)/.test(url.toString()),{timeout:30000}).catch(err=>console.error('V041_URL_WAIT',String(err)));
    await b.click({timeout:18000});
    await navigation;
    await page.waitForLoadState('domcontentloaded',{timeout:20000}).catch(()=>{});
    await page.waitForTimeout(2500);
    console.log('V041_AFTER_FREE_PAGE',page.url());
    console.log('V041_BODY',JSON.stringify((await page.locator('body').innerText()).slice(0,4000)));
    const links=await page.locator('a').evaluateAll(els=>els.map(e=>({
      label:(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,170),
      href:e.href,
      cls:e.className})).filter(x=>/download|standard|\.zip/i.test(x.label+' '+x.href)).slice(0,45));
    console.log('V041_FREE_DOWNLOAD_LINKS',JSON.stringify(links));
    let candidate=page.locator('a').filter({hasText:/Modular Character Outfits - Fantasy\[Standard\]/i}).first();
    if(!await candidate.count())candidate=page.locator('a.download_btn').first();
    if(!await candidate.count())candidate=page.getByText('Download', {exact:true}).first();
    if(!await candidate.count())throw new Error('Could not locate Standard free ZIP download link');
    const chosen=(await candidate.innerText().catch(()=>''))+' '+(await candidate.getAttribute('href').catch(()=>''));
    console.log('V041_SELECTED_STANDARD',chosen);
    if(/source.*\$20|\$20.*source/i.test(chosen))throw new Error('Refusing paid source product');
    const [download]=await Promise.all([
       page.waitForEvent('download',{timeout:180000}),
       candidate.click({timeout:25000})
    ]);
    const suggested=download.suggestedFilename();
    console.log('V041_SUGGESTED_NAME',suggested);
    if(!/standard/i.test(suggested))throw new Error('Not a Standard free package: '+suggested);
    await download.saveAs(DEST);
    console.log('V041_STANDARD_DOWNLOADED',DEST,fs.statSync(DEST).size);
    if(fs.statSync(DEST).size<1000000||fs.statSync(DEST).size>390000000)
      throw new Error('Unexpected file size for 280MB Standard free download');
  }catch(err){
    console.error('V041_STANDARD_DOWNLOAD_ERROR',String(err));
    await page.screenshot({path:'/tmp/genesis_v041/itch_free_download_diagnostic.png',fullPage:false}).catch(()=>{});
    process.exitCode=2;
  }finally{await browser.close();}
})();