// Real browser-adapter/storage and foreground-reminder behavior in isolated storage.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict'),ts=require('typescript'),rxjs=require('rxjs');
const persistent=new Map(),session=new Map();let deny=false,tail=Promise.resolve();
const storage=map=>({getItem:k=>{if(deny)throw Error('denied');return map.get(k)??null;},setItem:(k,v)=>{if(deny)throw Error('denied');map.set(k,v);},removeItem:k=>map.delete(k)});
const modules=new Map();
const globals={Intl,Date,crypto:require('node:crypto').webcrypto,structuredClone,localStorage:storage(persistent),sessionStorage:storage(session),navigator:{locks:{request:(_key,job)=>{const next=tail.then(job);tail=next.catch(()=>{});return next;}}}};
function load(file){file=path.resolve(file);if(modules.has(file))return modules.get(file);const exports={};modules.set(file,exports);const requireLocal=id=>id==='@angular/core'?{Injectable:()=>x=>x}:id==='rxjs'?rxjs:id.startsWith('.')?load(path.resolve(path.dirname(file),id+'.ts')):require(id);vm.runInNewContext(ts.transpile(fs.readFileSync(file,'utf8'),{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,experimentalDecorators:true}),{...globals,exports,require:requireLocal},{filename:file});return exports;}
const {TrackerService}=load('src/app/core/tracker.demo.service.ts');
const {DEVICE_KEY}=load('src/app/core/device-store.ts');
const {defaultPreferences,inQuietHours}=load('src/app/core/preferences.ts');
const {ForegroundReminders}=load('src/app/core/foreground-reminders.ts');
const first=rxjs.firstValueFrom;
(async()=>{
 const api=new TrackerService();assert.equal((await first(api.overview())).total,0);
 const h=await first(api.save({name:' Read one page ',description:'Sample',cue:'After breakfast'},null));
 const daily=await first(api.overview());for(let i=0;i<2;i++)await first(api.complete(h,daily.today));
 assert.equal((await first(api.rewards())).points,10);
 await first(api.complete({...h,completed:true},daily.today));assert.equal((await first(api.rewards())).points,0);
 let p=await first(api.settings());p.theme='dark';p.display_name=' Alex ';p.reminders[h.id]={enabled:true,time:'09:00'};await first(api.saveSettings(p));
 const photo='data:image/jpeg;base64,/9j/4HNhbXBsZf/Z';p.avatar_image=photo;await first(api.saveSettings(p));assert.equal((await first(new TrackerService().settings())).avatar_image,photo);p.avatar_image='';await first(api.saveSettings(p));assert.equal((await first(new TrackerService().settings())).avatar_image,'');await assert.rejects(first(api.saveSettings({...p,avatar_image:'data:image/svg+xml;base64,PHN2Zz4='})));
 const second=new TrackerService();assert.equal((await first(second.settings())).display_name,'Alex');assert.equal((await first(second.overview())).habits[0].cue,'After breakfast');
 await Promise.all([api.save({name:'Walk',description:''},null),second.save({name:'Stretch',description:''},null)].map(first));
 assert.equal((await first(api.overview())).total,3);
 const before=persistent.get(DEVICE_KEY);deny=true;await assert.rejects(first(api.save({name:'Cannot save',description:''},null)));deny=false;assert.equal(persistent.get(DEVICE_KEY),before);
 persistent.set(DEVICE_KEY,'corrupt');await assert.rejects(first(api.overview()));assert.equal(persistent.get(DEVICE_KEY),'corrupt');persistent.set(DEVICE_KEY,before);
 persistent.delete(DEVICE_KEY);const old={zone:'UTC',habits:[{...h,cue:undefined,reason:undefined,small_action:undefined}],checks:[{habit_id:h.id,day:daily.today}]};session.set('routiq-tab-demo-v1',JSON.stringify(old));const migrated=new TrackerService();assert.equal((await first(migrated.overview())).total,1);assert.equal((await first(migrated.rewards())).points,10);assert(session.has('routiq-tab-demo-v1'));
 p=defaultPreferences();p.notifications=true;p.reminders[h.id]={enabled:true,time:'09:00'};
 const at=new Date('2026-10-18T12:00:00Z'),view={today:'2026-10-18',timezone:'UTC',habits:[{...h,completed:false}]};
 const manager=new ForegroundReminders(true);assert.equal((await manager.next(view,p,at)).id,h.id);assert.equal(await manager.next(view,p,at),null);
 await manager.settle(h.id,view.today,true,at);assert.equal(await manager.next(view,p,new Date(at.getTime()+599999)),null);assert.equal((await manager.next(view,p,new Date(at.getTime()+600000))).id,h.id);
 await manager.settle(h.id,view.today,false,at);assert.equal(await new ForegroundReminders(true).next(view,p,at),null);
 persistent.delete('routiq-reminder-delivery-v1-browser');assert.equal(await manager.next({...view,habits:[{...h,completed:true}]},p,at),null);
 p.quiet_hours=true;p.quiet_start='22:00';p.quiet_end='08:00';assert(inQuietHours('23:00',p));assert(inQuietHours('07:59',p));assert(!inQuietHours('08:00',p));
 const [{FAQ},{CoachSuggestions}]=[load('src/app/core/demo-faq.ts'),load('src/app/core/coach-suggestions.ts')];const picker=new CoachSuggestions();for(const q of FAQ){const answer=await first(migrated.chat(q.question));assert.equal(answer.question_id,q.id);const choices=picker.next(q.question,answer);assert.equal(choices.length,4);assert.equal(new Set(choices).size,4);}
 console.log('PASS: durable persistence/migration, concurrent writes, corruption/write denial, reward duplicate/undo, settings restart, foreground snooze/dismiss/completed suppression, quiet hours, all FAQ IDs and four dynamic suggestions.');
})().catch(e=>{console.error(e);process.exitCode=1;});

