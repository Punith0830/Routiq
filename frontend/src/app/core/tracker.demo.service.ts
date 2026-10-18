import { Injectable } from '@angular/core';
import {DeviceStore,DeviceData} from './device-store';
import {Preferences,validatePreferences,rewardSummary,featureHelp} from './preferences';
import { defer, of } from 'rxjs';
import { Habit, Overview, Progress, Reply } from './tracker.models';
import { FAQ, HELP } from './demo-faq';
export type { Habit, Overview, Progress, Reply } from './tracker.models';
interface DemoData {zone:string;habits:Omit<Habit,'completed'>[];checks:{habit_id:string;day:string}[];}
const normalize=(s:string)=>s.toLowerCase().replace(/[’‘]/g,"'").replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();

@Injectable({providedIn:'root'})
export class TrackerService {
  readonly isAssignment:boolean=false;
  readonly isDemo=true;
  private readonly store=new DeviceStore();
  private get data(){return this.store.read();}
  private day(){const p=new Intl.DateTimeFormat('en',{timeZone:this.data.zone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());return ['year','month','day'].map(k=>p.find(x=>x.type===k)!.value).join('-');}
  private snapshot():Overview{
    const today=this.day();const habits=this.data.habits.filter(h=>h.start_date<=today).map(h=>({...h,completed:this.data.checks.some(c=>c.habit_id===h.id&&c.day===today)}));
    const completed=habits.filter(h=>h.completed).length;
    const recent_days=Array.from({length:7},(_,i)=>{const d=new Date(today+'T12:00:00Z');d.setUTCDate(d.getUTCDate()-6+i);const day=d.toISOString().slice(0,10);return {day,completed:this.data.checks.filter(c=>c.day===day).length};});
    return {today,timezone:this.data.zone,habits,total:habits.length,completed,remaining:habits.length-completed,completion_percentage:habits.length?Math.round(completed/habits.length*1000)/10:null,recent_days};
  }
  overview(){return defer(async()=>{await this.store.initialize();return this.snapshot();});}
  settings(){return defer(async()=>{await this.store.initialize();return this.data.settings;});}
  saveSettings(payload:Preferences){return defer(()=>this.store.mutate(data=>{const p=validatePreferences(payload);if(Object.keys(p.reminders).some(id=>!data.habits.some(h=>h.id===id)))throw Error('Unknown reminder habit');data.settings=p;return p;}));}
  rewards(){return defer(()=>{const data=this.data,today=this.day();return of(rewardSummary(data.checks.filter(c=>c.day<=today&&data.habits.some(h=>h.id===c.habit_id&&h.start_date<=c.day)).length));});}
  progress(){return defer(()=>{const today=this.day();const start=new Date(today+'T12:00:00Z');start.setUTCDate(start.getUTCDate()-29);const history=this.data.checks.filter(c=>c.day>=start.toISOString().slice(0,10)&&c.day<=today).map(c=>({...c,habit_name:this.data.habits.find(h=>h.id===c.habit_id)!.name})).sort((a,b)=>b.day.localeCompare(a.day));return of<Progress>({today,recorded_completions:history.length,history});});}
  save(payload:import('./tracker.models').HabitInput,id:string|null){return defer(()=>this.store.mutate(data=>{
    const name=payload.name.trim(),description=payload.description.trim();
    if(!name||name.length>80||description.length>300)throw Error('Invalid habit');
    if(!id&&data.habits.length>=100)throw Error('Demo habit limit');
    const existing=id?data.habits.find(h=>h.id===id):null;if(id&&!existing)throw Error('Unknown habit');
    const extras={reason:payload.reason?.trim()||'',small_action:payload.small_action?.trim()||'',cue:payload.cue?.trim()||''};
    if(Object.values(extras).some(s=>s.length>300))throw Error('Keep optional fields under 300 characters.');
    const habit={name,description,...extras,id:existing?.id||crypto.randomUUID(),created_at:existing?.created_at||new Date().toISOString(),start_date:existing?.start_date||this.day()};
    data.habits=existing?data.habits.map(h=>h.id===id?habit:h):[...data.habits,habit];
    return {...habit,completed:data.checks.some(c=>c.habit_id===habit.id&&c.day===this.day())} as Habit;
  }));}
  complete(habit:Habit,day:string){return defer(async()=>{
    await this.store.mutate(data=>{
      if(day!==this.day()||!data.habits.some(h=>h.id===habit.id&&h.start_date<=day))throw Error('Refresh Today');
      data.checks=data.checks.filter(c=>!(c.habit_id===habit.id&&c.day===day));
      if(!habit.completed)data.checks.push({habit_id:habit.id,day});
    });return this.snapshot();
  });}
  chat(message:string){return defer(()=>of(this.answer(message)));}
  private answer(message:string):Reply{
    if(!message.trim()||message.length>4000)throw Error('Invalid question');
    const reply=(text:string,source:string,q?:typeof FAQ[number],choices:Reply['choices']=[]):Reply=>({message:text,source,question_id:q?.id??null,choices});
    if(/sk-[\w-]{8,}|api.?key|password|ignore.{0,35}instructions|reveal.{0,35}prompt/i.test(message))return reply('Please keep credentials private. I cannot reveal private instructions or invent activity, but I’m happy to help with a habit question.','scope_limit');
    const text=normalize(message),q=FAQ.find(q=>normalize(q.question)===text);
    const help=featureHelp(message);if(help)return reply(help,'application_help',q);
    const todayIds=new Set(['Q-011','Q-012','Q-013','Q-014','Q-015','Q-016','Q-017','Q-021','Q-055','Q-075','Q-077','Q-078','Q-081','Q-082','Q-083','Q-084']);
    if(['how am i doing today','today progress','what habits are left today','remaining habits','show today habits'].includes(text)||q&&todayIds.has(q.id)){
      const today=this.snapshot();if(!today.total)return reply('Happy to help you get started! You have no test habits yet. Choose Add habit on Today.','verified_local_data',q);
      const done=q&&['Q-014','Q-055'].includes(q.id);const names=today.habits.filter(h=>done?h.completed:!h.completed).map(h=>h.name);
      return reply(`Happy to help! For ${today.today}, you have recorded ${today.completed} of ${today.total} daily test habits complete. ${done?'Completed':'Remaining'}: ${names.join(', ')||'none'}.`,'verified_local_data',q);
    }
    if(HELP[text])return reply(HELP[text],'application_help',q);
    if(q){
      if(q.id!=='Q-031'&&['APP_HELP','HABIT_CREATION_HELP','HABIT_MANAGEMENT','REMINDERS','HABIT_SCHEDULING'].includes(q.intent_id))return reply('Happy to explain what’s available. Use Today to add or edit a daily test habit and Progress to review saved check-ins. Foreground reminders are available in Settings; custom schedules and accounts are not included.','application_help',q);
      if(/notebook|\/live|\/offline|\/reset/.test(q.answer.toLowerCase()))return reply('Thank you for asking. This browser demo uses prepared FAQ answers and device-local habits. Live generative AI is off. Chat clears on reload; habits and preferences persist in this browser.','scope_limit',q);
      if(['DAILY_PROGRESS','WEEKLY_PROGRESS','MONTHLY_PROGRESS','PERIOD_COMPARISON','STREAKS','PATTERN_ANALYSIS','COMPLETION_STATUS','TODAY_OVERVIEW','MISSED_HABITS','HIGH_CONSISTENCY','RETURNING_USER','RECOMMENDATION_EXPLANATION'].includes(q.intent_id))return reply('Thank you for asking. That analysis isn’t included in this demo yet. You can check today’s completion percentage on Today or saved check-ins in Progress. Historical rates and streaks still need approved rules.','scope_limit',q);
      return reply(q.answer,'prepared_faq',q);
    }
    const stops=new Set('a an the i my me you your can could would should do does how what which is are am was were it this that to for of on in and with please show tell about'.split(' '));
    const tokens=(s:string)=>new Set(normalize(s).split(' ').filter(t=>t&&!stops.has(t)));const input=tokens(text);
    const choices=FAQ.map(q=>{const t=tokens(q.question),shared=[...input].filter(x=>t.has(x)).length;return {q,shared,score:shared?2*shared/(input.size+t.size):0};}).filter(x=>x.shared>=Math.min(2,input.size)&&x.score>=.35).sort((a,b)=>b.score-a.score||a.q.id.localeCompare(b.q.id)).slice(0,3).map(x=>({id:x.q.id,question:x.q.question}));
    return reply(choices.length?'Happy to help you find the right answer. Which related question did you mean?':'I’m happy to help with Routiq and habits. Try today’s progress or a sample habit question. This demo uses prepared answers, not live AI.',choices.length?'clarification':'scope_limit',undefined,choices);
  }
}
