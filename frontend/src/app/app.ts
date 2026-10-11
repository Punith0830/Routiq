import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { Habit, Overview, Progress, Reply, TrackerService } from './core/tracker.service';
interface ChatEntry {role:'user'|'coach';text:string;source?:string;choices?:Reply['choices'];}

@Component({
  selector:'routiq-app',standalone:true,imports:[FormsModule],templateUrl:'./app.html'
})
export class App {
  private readonly api = inject(TrackerService);
  readonly isDemo=this.api.isDemo;
  readonly isAssignment=this.api.isAssignment;
  private readonly destroy = inject(DestroyRef);
  readonly tab=signal<'today'|'progress'|'coach'>('today');
  readonly overview=signal<Overview|null>(null);
  readonly progress=signal<Progress|null>(null);
  readonly loading = signal(false);
  readonly error=signal(''); readonly notice=signal('');
  private refreshQueued=false;
  readonly editor=signal(false);readonly editingId=signal<string|null>(null);
  readonly saving=signal(false);readonly formError=signal('');
  readonly pending=signal(new Set<string>());readonly chatting=signal(false);readonly chatError=signal('');
  readonly chat=signal<ChatEntry[]>([{role:'coach',text:'Hi, I’m your Routiq Coach. Ask about today’s habits or explore a small habit idea. I use prepared answers and saved Today records; live AI is off.'}]);
  name='';description='';message='';
  readonly samples=['How am I doing today?','What is still pending?','Can you suggest a small starting habit?','How can I make reading easier to maintain?'];
  constructor(){
    this.load();const resume=()=>{if(!document.hidden)this.load();};
    document.addEventListener('visibilitychange',resume);window.addEventListener('focus',resume);
    const timer=window.setInterval(()=>{if(!document.hidden)this.load();},60000);
    this.destroy.onDestroy(()=>{clearInterval(timer);document.removeEventListener('visibilitychange',resume);window.removeEventListener('focus',resume);});
  }
  navigate(tab:'today'|'progress'|'coach'){this.tab.set(tab);if(tab!=='coach')this.load();}
  load() {
    if (this.loading()) {this.refreshQueued=true;return;}
    this.loading.set(true);
    forkJoin({overview:this.api.overview(),progress:this.api.progress()}).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next:result=>{this.overview.set(result.overview);this.progress.set(result.progress);this.loading.set(false);this.error.set('');if(this.refreshQueued){this.refreshQueued=false;this.load();}},
      error:()=>{this.error.set('We couldn’t load your saved habits. Check the local connection and try again.');this.loading.set(false);this.refreshQueued=false;}
    });
  }
  openEditor(habit?:Habit){this.editingId.set(habit?.id||null);this.name=habit?.name||'';this.description=habit?.description||'';this.formError.set('');this.editor.set(true);setTimeout(()=>document.getElementById('habit-name')?.focus(),0);}
  cancelEditor(){if(!this.saving()){this.editor.set(false);setTimeout(()=>document.getElementById('add-habit')?.focus(),0);}}
  editorKey(event:KeyboardEvent){if(event.key==='Escape'){this.cancelEditor();return;}if(event.key==='Tab'){const elements=Array.from(document.querySelectorAll<HTMLElement>('.editor button:not(:disabled),.editor input:not(:disabled),.editor textarea:not(:disabled)'));const first=elements[0],last=elements[elements.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}}
  save(){
    if(this.saving())return;const name=this.name.trim(),description=this.description.trim();
    if(!name||name.length>80||description.length>300){this.formError.set('Use a name of 1–80 characters and a description of up to 300 characters.');return;}
    this.saving.set(true);this.formError.set('');
    this.api.save({name,description},this.editingId()).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next:()=>{this.saving.set(false);this.editor.set(false);this.notice.set(this.editingId()?'Habit updated.':'Habit added.');this.load();},
      error:()=>{this.saving.set(false);this.formError.set('We couldn’t save this habit. Your entries are still here. Try again.');}
    });
  }
  toggle(habit:Habit){
    const overview=this.overview();if(!overview||this.pending().has(habit.id))return;
    this.pending.update(s=>new Set(s).add(habit.id));this.notice.set('');
    this.api.complete(habit,overview.today).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next:result=>{this.overview.set(result);this.pending.update(s=>{const copy=new Set(s);copy.delete(habit.id);return copy;});this.notice.set(habit.completed?'Completion undone.':'Completion saved.');this.load();},
      error:()=>{this.pending.update(s=>{const copy=new Set(s);copy.delete(habit.id);return copy;});this.error.set('We couldn’t save that change. Refresh Today and try again.');}
    });
  }
  send(text=this.message){
    text=text.trim();if(!text||this.chatting())return;if(text.length>4000){this.chatError.set('Keep your question under 4,000 characters.');return;}
    this.chatting.set(true);this.chatError.set('');this.message=text;
    this.api.chat(text).pipe(takeUntilDestroyed(this.destroy)).subscribe({
      next:reply=>{this.chat.update(items=>[...items,{role:'user',text},{role:'coach',text:reply.message,source:reply.source,choices:reply.choices}]);this.message='';this.chatting.set(false);setTimeout(()=>document.getElementById('chat-end')?.scrollIntoView({behavior:'auto',block:'nearest'}),0);},
      error:()=>{this.chatting.set(false);this.chatError.set('The Coach couldn’t respond. Your question is still here; try sending again.');}
    });
  }
  resetChat(){if(!this.chatting()){this.chat.set([{role:'coach',text:'A fresh start. What would you like to work on?'}]);this.chatError.set('');this.message='';}}
  dateLabel(value:string){return new Date(value+'T12:00:00').toLocaleDateString(undefined,{weekday:'long',month:'short',day:'numeric'});}
  shortDay(value:string){return new Date(value+'T12:00:00').toLocaleDateString(undefined,{weekday:'short'});}
  activityTotal(){return this.overview()?.recent_days.reduce((sum,day)=>sum+day.completed,0)??0;}
  barHeight(count:number){const max=Math.max(1,...(this.overview()?.recent_days.map(day=>day.completed)??[]));return count/max*100;}
  sourceLabel(source?:string){return source==='verified_local_data'?'From your saved Today records':source==='prepared_faq'?'Prepared FAQ answer':source==='application_help'?'Routiq help':source==='clarification'?'Choose a question':'Current scope';}
}
