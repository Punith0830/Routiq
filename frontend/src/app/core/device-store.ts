import {Habit} from './tracker.models';
import {defaultPreferences, Preferences, validatePreferences} from './preferences';
export interface DeviceData {schema:2;revision:number;zone:string;habits:Omit<Habit,'completed'>[];checks:{habit_id:string;day:string}[];settings:Preferences;}
export const DEVICE_KEY='routiq-device-v2';
const OLD_KEY='routiq-tab-demo-v1';
export class DeviceStore {
  private parse(raw:string,legacy=false):DeviceData{
    const p=JSON.parse(raw);if(!p||typeof p!=='object'||!Array.isArray(p.habits)||!Array.isArray(p.checks)||typeof p.zone!=='string')throw Error('Saved device data is unreadable; it has not been overwritten.');
    new Intl.DateTimeFormat('en',{timeZone:p.zone});
    if(!legacy&&(p.schema!==2||!Number.isInteger(p.revision)||p.revision<0))throw Error('Unsupported device storage version.');
    if(p.habits.length>100||p.checks.length>100000)throw Error('Device record limit reached.');
    const date=(v:unknown)=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&!Number.isNaN(Date.parse(v+'T12:00:00Z'))&&new Date(v+'T12:00:00Z').toISOString().slice(0,10)===v;
    const ids=new Set<string>();
    const habits=p.habits.map((h:Record<string,unknown>)=>{
      if(!h||typeof h.id!=='string'||!h.id||ids.has(h.id)||typeof h.name!=='string'||!h.name.trim()||h.name.length>80||typeof h.description!=='string'||h.description.length>300||!date(h.start_date)||typeof h.created_at!=='string'||Number.isNaN(Date.parse(h.created_at)))throw Error('Saved habits are invalid; original data preserved.');
      ids.add(h.id);
      for(const field of ['reason','small_action','cue'])if(h[field]!==undefined&&(typeof h[field]!=='string'||(h[field] as string).length>300))throw Error('Invalid habit field');
      return {...h,reason:h.reason??'',small_action:h.small_action??'',cue:h.cue??''};
    }) as DeviceData['habits'];
    const unique=new Set<string>();
    const checks=p.checks.map((c:DeviceData['checks'][number])=>{
      if(!c||!ids.has(c.habit_id)||!date(c.day))throw Error('Saved check-ins are invalid; original data preserved.');
      const key=c.habit_id+'|'+c.day;if(unique.has(key))throw Error('Duplicate saved check-in');unique.add(key);return {habit_id:c.habit_id,day:c.day};
    });
    return {schema:2,revision:legacy?0:p.revision,zone:p.zone,habits,checks,settings:legacy?defaultPreferences():validatePreferences(p.settings)};
  }
  read():DeviceData{
    const raw=localStorage.getItem(DEVICE_KEY);if(raw!==null)return this.parse(raw);
    const legacy=sessionStorage.getItem(OLD_KEY);if(legacy!==null)return this.parse(legacy,true);
    return {schema:2,revision:0,zone:Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC',habits:[],checks:[],settings:defaultPreferences()};
  }
  private async lock<T>(job:()=>T|Promise<T>):Promise<T>{
    if(typeof navigator!=='undefined'&&navigator.locks)return navigator.locks.request(DEVICE_KEY,job);
    return job();
  }
  async initialize(){await this.lock(()=>{if(localStorage.getItem(DEVICE_KEY)===null)this.commit(this.read());});}
  private commit(data:DeviceData){
    const raw=JSON.stringify(data);this.parse(raw);
    localStorage.setItem(DEVICE_KEY,raw);
    if(localStorage.getItem(DEVICE_KEY)!==raw)throw Error('Another tab changed these records. Refresh and try again.');
  }
  async mutate<T>(operation:(data:DeviceData)=>T):Promise<T>{
    return this.lock(()=>{const current=this.read(),base=localStorage.getItem(DEVICE_KEY),next=structuredClone(current);const result=operation(next);next.revision=current.revision+1;
      if(localStorage.getItem(DEVICE_KEY)!==base)throw Error('Another tab changed these records. Refresh before saving.');
      this.commit(next);return result;
    });
  }
}

