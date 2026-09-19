const {chromium}=require('/Users/rocket/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');const path=require('path');const crypto=require('crypto');
const root='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S78_match_visual_preflight/viewer_execution_01';
(async()=>{
 const start=new Date().toISOString();const output=path.join(root,'screenshots');fs.mkdirSync(output);
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1080},deviceScaleFactor:1});
  await page.goto('file://'+path.join(root,'viewer/index.html'));
  await page.locator('img').first().waitFor();
  await page.waitForFunction(()=>Array.from(document.images).every(im=>im.complete&&im.naturalWidth===576&&im.naturalHeight===576));
  const cards=page.locator('.pair');if(await cards.count()!==18)throw new Error('Expected18 cards');
  const files=[];
  for(let i=0;i<18;i++){
   const card=cards.nth(i);const id=await card.getAttribute('id');
   await card.screenshot({path:path.join(output,id+'.png')});
   for(let j=0;j<2;j++)await card.locator('.local').nth(j).screenshot({path:path.join(output,id+'_'+j+'_local.png')});
   files.push({id,full_card:id+'.png',sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(output,id+'.png'))).digest('hex')});
  }
  const info=await page.locator('.local img').first().evaluate(el=>({imageRendering:getComputedStyle(el).imageRendering,width:getComputedStyle(el).width}));
  fs.writeFileSync(path.join(root,'ACTUAL_BROWSER_RENDER.json'),JSON.stringify({started_utc:start,completed_utc:new Date().toISOString(),status:'18_CARDS_RENDERED_NOT_RATED',browser:await browser.version(),viewport:{width:1440,height:1080},actual_local_css:info,files,source_images_modified:0,new_features:0,new_models:0},null,2));
  console.log(JSON.stringify({status:'RENDERED',cards:18,browser:await browser.version()}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
