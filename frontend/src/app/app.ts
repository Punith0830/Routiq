import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { forkJoin, Subscription } from 'rxjs';
import { Habit, Overview, Progress, Reply, TrackerService } from './core/tracker.service';
import { CoachSuggestions } from './core/coach-suggestions';
import { Preferences, Rewards, defaultPreferences, validatePreferences, inQuietHours, zonedTime } from './core/preferences';
import { ForegroundReminders } from './core/foreground-reminders';
import { APP_VERSION } from './core/build-version';
interface ChatEntry{role:'user'|'assistant';text:string;source?:string;choices?:Reply['choices'];}
type Tab='today'|'progress'|'achievements'|'settings';
const intro:ChatEntry={role:'assistant',text:'Hi, I’m your Routiq AI Assist. Ask about your recorded habits or a small next step. I use prepared answers and supported Today records; live generative AI is off.'};
@Component({selector:'routiq-app',standalone:true,imports:[FormsModule],templateUrl:'./app.html',host:{'(document:keydown)':'globalKey($event)'}})
export class App{
  private readonly api=inject(TrackerService);
  private readonly destroy=inject(DestroyRef);
  readonly isDemo=this.api.isDemo;readonly isAssignment=this.api.isAssignment;
  readonly version=APP_VERSION;
  readonly tab=signal<Tab>('today');
  readonly overview=signal<Overview|null>(null);readonly progress=signal<Progress|null>(null);
  readonly rewards=signal<Rewards|null>(null);readonly prefs=signal<Preferences>(defaultPreferences());
  readonly loading=signal(false);readonly error=signal('');readonly notice=signal('');
  readonly editor=signal(false);readonly editingId=signal<string|null>(null);readonly saving=signal(false);readonly formError=signal('');
  readonly pending=signal(new Set<string>());readonly chatting=signal(false);readonly chatError=signal('');
  readonly assistOpen=signal(false);readonly mobile=signal(window.matchMedia('(max-width:650px)').matches);
  readonly chat=signal<ChatEntry[]>([{...intro}]);readonly reflectionHidden=signal(false);
  readonly photoLoading=signal(false);readonly photoError=signal('');private photoGeneration=0;
  readonly settingsSaving=signal(false);readonly settingsError=signal('');readonly settingsNotice=signal('');
  readonly settingsDirty=signal(false);readonly reminderActive=signal<Habit|null>(null);readonly reminderError=signal('');
  private readonly suggestions=new CoachSuggestions();readonly samples=signal(this.suggestions.reset());
  private readonly reminderManager=new ForegroundReminders(this.isDemo);
  private reminderChecking=false;private reminderDay='';private refreshQueued=false;private chatGeneration=0;private chatRequest?:Subscription;
  private editorOpener:HTMLElement|null=null;private sourceScroll=0;private readonly originalOverflow=document.documentElement.style.overflow;
  private readonly systemTheme=window.matchMedia('(prefers-color-scheme:dark)');
  private readonly systemMotion=window.matchMedia('(prefers-reduced-motion:reduce)');
  private readonly mobileQuery=window.matchMedia('(max-width:650px)');
  name='';description='';reason='';smallAction='';cue='';message='';draft=defaultPreferences();
  constructor(){
    this.load();
    const resume=()=>{if(!document.hidden)this.load();};
    const resize=()=>{this.mobile.set(this.mobileQuery.matches);this.syncOverlay();if(this.assistOpen()&&this.mobile())setTimeout(()=>document.getElementById('message')?.focus(),0);};
    const appearance=()=>this.applyAppearance();
    document.addEventListener('visibilitychange',resume);window.addEventListener('focus',resume);window.addEventListener('storage',resume);
    this.mobileQuery.addEventListener('change',resize);this.systemTheme.addEventListener('change',appearance);this.systemMotion.addEventListener('change',appearance);
    const reload=window.setInterval(()=>{if(!document.hidden)this.load();},60000);
    const reminders=window.setInterval(()=>{if(!document.hidden){if(this.prefs().notifications)this.load();else void this.checkReminders();}},15000);
    this.destroy.onDestroy(()=>{clearInterval(reload);clearInterval(reminders);this.chatRequest?.unsubscribe();document.removeEventListener('visibilitychange',resume);window.removeEventListener('focus',resume);window.removeEventListener('storage',resume);this.mobileQuery.removeEventListener('change',resize);this.systemTheme.removeEventListener('change',appearance);this.systemMotion.removeEventListener('change',appearance);document.documentElement.style.overflow=this.originalOverflow;delete document.documentElement.dataset['theme'];delete document.documentElement.dataset['reduceMotion'];});
  }
  navigate(tab:Tab){this.tab.set(tab);this.load();setTimeout(()=>document.getElementById('page-title')?.focus(),0);}
  load(){
    if(this.loading()){this.refreshQueued=true;return;}this.loading.set(true);
    forkJoin({overview:this.api.overview(),progress:this.api.progress(),settings:this.api.settings(),rewards:this.api.rewards()}).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next:r=>{this.overview.set(r.overview);this.progress.set(r.progress);this.rewards.set(r.rewards);this.prefs.set(r.settings);if(!this.settingsDirty())this.draft=structuredClone(r.settings);this.applyAppearance();this.loading.set(false);this.error.set('');void this.checkReminders();if(this.refreshQueued){this.refreshQueued=false;this.load();}},
      error:()=>{this.error.set('Could not load saved records. Check device storage or the local service, then retry. Existing data has not been reset.');this.loading.set(false);this.refreshQueued=false;}
    });
  }
  markSettingsDirty(){this.settingsDirty.set(true);this.settingsNotice.set('');}
  reminderFor(id:string){return this.draft.reminders[id]??(this.draft.reminders[id]={enabled:false,time:'09:00'});}
  savePreferences(){
    if(this.settingsSaving()||this.photoLoading())return;let p:Preferences;
    try{p=validatePreferences(this.draft);}catch(e){this.settingsError.set(e instanceof Error?e.message:'Check your settings.');return;}
    this.settingsSaving.set(true);this.settingsError.set('');this.settingsNotice.set('');
    this.api.saveSettings(p).pipe(takeUntilDestroyed(this.destroy)).subscribe({next:value=>{this.prefs.set(value);this.draft=structuredClone(value);this.settingsDirty.set(false);this.settingsSaving.set(false);this.settingsNotice.set('Preferences saved on this device.');this.applyAppearance();void this.checkReminders();},error:()=>{this.settingsSaving.set(false);this.settingsError.set('Preferences could not be saved. Your draft is still here; previous preferences remain active.');}});
  }
  async uploadPhoto(event:Event){
    const input=event.target as HTMLInputElement,file=input.files?.[0];input.value='';if(!file)return;
    const generation=++this.photoGeneration;this.photoError.set('');
    if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>5*1024*1024){this.photoError.set('Choose a JPG, PNG or WebP photo under 5 MB.');return;}
    this.photoLoading.set(true);const url=URL.createObjectURL(file);
    try{
      const image=new Image();image.src=url;await image.decode();
      if(!image.naturalWidth||image.naturalWidth*image.naturalHeight>16000000)throw Error('Choose a photo under 16 megapixels.');
      const canvas=document.createElement('canvas');canvas.width=256;canvas.height=256;
      const ctx=canvas.getContext('2d');if(!ctx)throw Error('Could not prepare your photo.');
      const side=Math.min(image.naturalWidth,image.naturalHeight);ctx.fillStyle='#ffffff';ctx.fillRect(0,0,256,256);
      ctx.drawImage(image,(image.naturalWidth-side)/2,(image.naturalHeight-side)/2,side,side,0,0,256,256);
      const photo=canvas.toDataURL('image/jpeg',0.85);if(photo.length>200000)throw Error('Choose a smaller photo.');
      if(generation===this.photoGeneration){this.draft.avatar_image=photo;this.draft.avatar='initial';this.markSettingsDirty();}
    }catch(e){if(generation===this.photoGeneration)this.photoError.set(e instanceof Error?e.message:'Could not read that photo.');}
    finally{URL.revokeObjectURL(url);if(generation===this.photoGeneration)this.photoLoading.set(false);}
  }
  removePhoto(){this.photoGeneration++;this.photoLoading.set(false);this.draft.avatar_image='';this.draft.avatar='initial';this.photoError.set('');this.markSettingsDirty();}
  applyAppearance(){const p=this.prefs();document.documentElement.dataset['theme']=p.theme==='system'?(this.systemTheme.matches?'dark':'light'):p.theme;document.documentElement.dataset['reduceMotion']=String(p.reduced_motion||this.systemMotion.matches);}
  motionOff(){return this.prefs().reduced_motion||this.systemMotion.matches;}
  avatar(){return this.prefs().avatar==='leaf'?'❧':this.prefs().avatar==='sun'?'☀':this.prefs().avatar==='spark'?'✦':(this.prefs().display_name.trim().slice(0,1).toUpperCase()||'r.');}
  openEditor(habit?:Habit){this.editorOpener=document.activeElement as HTMLElement;if(this.assistOpen())this.closeAssist(false);this.editingId.set(habit?.id||null);this.name=habit?.name||'';this.description=habit?.description||'';this.reason=habit?.reason||'';this.smallAction=habit?.small_action||'';this.cue=habit?.cue||'';this.formError.set('');this.editor.set(true);this.syncOverlay();setTimeout(()=>document.getElementById('habit-name')?.focus(),0);}
  cancelEditor(){if(this.saving())return;this.editor.set(false);this.syncOverlay();setTimeout(()=>{if(this.editorOpener?.isConnected)this.editorOpener.focus();else document.getElementById('add-habit')?.focus();},0);}
  trap(event:KeyboardEvent,selector:string){if(event.key!=='Tab')return;const f=Array.from(document.querySelectorAll<HTMLElement>(selector)).filter(e=>!e.hasAttribute('disabled'));const first=f[0],last=f[f.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}
  editorKey(event:KeyboardEvent){if(event.key==='Escape'){event.stopPropagation();this.cancelEditor();}else this.trap(event,'.editor button,.editor input,.editor textarea');}
  save(){
    if(this.saving())return;const name=this.name.trim(),description=this.description.trim(),reason=this.reason.trim(),small_action=this.smallAction.trim(),cue=this.cue.trim();
    if(!name||name.length>80||[description,reason,small_action,cue].some(s=>s.length>300)){this.formError.set('Use a name of 1–80 characters. Each optional field can contain up to 300 characters.');setTimeout(()=>document.getElementById('habit-name')?.focus(),0);return;}
    this.saving.set(true);this.formError.set('');
    this.api.save({name,description,reason,small_action,cue},this.editingId()).pipe(takeUntilDestroyed(this.destroy)).subscribe({next:()=>{this.saving.set(false);this.cancelEditor();this.notice.set(this.editingId()?'Habit updated.':'Habit added.');this.load();},error:()=>{this.saving.set(false);this.formError.set('Could not save this habit. Your entries remain here; try again.');}});
  }
  toggle(habit:Habit){
    const daily=this.overview();if(!daily||this.pending().has(habit.id))return;this.pending.update(s=>new Set(s).add(habit.id));this.notice.set('');
    this.api.complete(habit,daily.today).pipe(takeUntilDestroyed(this.destroy)).subscribe({next:r=>{this.overview.set(r);this.pending.update(s=>{const n=new Set(s);n.delete(habit.id);return n;});if(this.reminderActive()?.id===habit.id)this.reminderActive.set(null);this.notice.set(habit.completed?'Completion undone. Points and milestones have been recalculated.':this.prefs().gamification?'Completion saved. Points follow your recorded activity.':'Completion saved.');this.load();},error:()=>{this.pending.update(s=>{const n=new Set(s);n.delete(habit.id);return n;});this.error.set('Could not save that change. Refresh Today and retry.');}});
  }
  openAssist(){this.sourceScroll=window.scrollY;this.assistOpen.set(true);this.syncOverlay();setTimeout(()=>document.getElementById('message')?.focus(),0);}
  closeAssist(focus=true){this.assistOpen.set(false);this.syncOverlay();if(this.mobile())window.scrollTo({top:this.sourceScroll,behavior:'instant'});if(focus)setTimeout(()=>document.getElementById('assist-launcher')?.focus(),0);}
  syncOverlay(){document.documentElement.style.overflow=this.editor()||this.mobile()&&this.assistOpen()?'hidden':this.originalOverflow;}
  assistKey(event:KeyboardEvent){if(event.key==='Escape'){event.stopPropagation();this.closeAssist();}else if(this.mobile())this.trap(event,'.assist-window button,.assist-window input');}
  globalKey(event:KeyboardEvent){if(event.key==='Escape'&&this.assistOpen()&&!this.editor()){event.stopPropagation();this.closeAssist();}}
  send(text=this.message){
    text=text.trim();if(!text||this.chatting())return;if(text.length>4000){this.chatError.set('Keep your question under 4,000 characters.');return;}
    const generation=++this.chatGeneration;this.chatting.set(true);this.chatError.set('');this.message=text;
    document.getElementById('message')?.focus();
    this.chatRequest=this.api.chat(text).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next:reply=>{if(generation!==this.chatGeneration)return;this.samples.set(this.suggestions.next(text,reply));this.chat.update(items=>[...items,{role:'user',text},{role:'assistant',text:reply.message,source:reply.source,choices:reply.choices}]);this.message='';this.chatting.set(false);setTimeout(()=>{document.getElementById('chat-end')?.scrollIntoView({behavior:'auto',block:'nearest'});if(this.assistOpen())document.getElementById('message')?.focus();},0);},
      error:()=>{if(generation!==this.chatGeneration)return;this.chatting.set(false);this.chatError.set('AI Assist could not respond. Your question is still here; retry when ready.');}
    });
  }
  resetChat(){this.chatGeneration++;this.chatRequest?.unsubscribe();this.chatting.set(false);this.samples.set(this.suggestions.reset());this.chat.set([{...intro}]);this.chatError.set('');this.message='';setTimeout(()=>document.getElementById('message')?.focus(),0);}
  async checkReminders(){
    const daily=this.overview(),p=this.prefs();if(!daily||this.reminderChecking||document.hidden||this.error())return;
    const active=this.reminderActive();if(active&&(!p.notifications||!p.reminders[active.id]?.enabled||this.reminderDay!==daily.today||inQuietHours(zonedTime(daily.timezone).time,p)||daily.habits.find(h=>h.id===active.id)?.completed))this.reminderActive.set(null);
    if(this.reminderActive()||!p.notifications)return;this.reminderChecking=true;
    try{const habit=await this.reminderManager.next(daily,p);if(habit&&this.prefs().notifications){this.reminderDay=daily.today;this.reminderActive.set(habit);}this.reminderError.set('');}catch{this.reminderError.set('In-app reminders are paused because device delivery storage is unavailable. Your habit records are unchanged.');}finally{this.reminderChecking=false;}
  }
  async settleReminder(snooze=false){const active=this.reminderActive(),daily=this.overview();if(!active||!daily)return;try{await this.reminderManager.settle(active.id,daily.today,snooze);this.reminderActive.set(null);this.notice.set(snooze?'Reminder snoozed for 10 minutes while Routiq is open.':'Reminder dismissed for today.');setTimeout(()=>{if(document.activeElement===document.body)document.getElementById('page-title')?.focus();},0);}catch{this.reminderError.set('Could not save the reminder choice. Try again.');}}
  goToReminder(){const h=this.reminderActive();if(!h)return;this.navigate('today');setTimeout(()=>document.getElementById('habit-'+h.id)?.focus(),0);}
  dismissReflection(){this.reflectionHidden.set(true);setTimeout(()=>document.getElementById('page-title')?.focus(),0);}
  dateLabel(value:string){return new Date(value+'T12:00:00').toLocaleDateString(undefined,{weekday:'long',month:'short',day:'numeric'});}
  shortDay(value:string){return new Date(value+'T12:00:00').toLocaleDateString(undefined,{weekday:'short'});}
  activityTotal(){return this.overview()?.recent_days.reduce((sum,day)=>sum+day.completed,0)??0;}
  barHeight(count:number){return count/Math.max(1,...(this.overview()?.recent_days.map(day=>day.completed)??[]))*100;}
  sourceLabel(source?:string){return source==='verified_local_data'?'From recorded Today activity':source==='prepared_faq'?'Prepared FAQ':source==='application_help'?'Routiq help':source==='clarification'?'Choose a question':'Scope guidance';}
}

