import {Overview,Habit} from './tracker.models';
import {Preferences,inQuietHours,zonedTime} from './preferences';
type Delivery={status:'shown'|'dismissed'|'snoozed';until?:number};
interface Ledger{day:string;items:Record<string,Delivery>;}
export class ForegroundReminders{
  private readonly key:string;
  constructor(browserOnly:boolean){this.key='routiq-reminder-delivery-v1-'+(browserOnly?'browser':'local');}
  private read(day:string):Ledger{
    const raw=localStorage.getItem(this.key);if(!raw)return {day,items:{}};
    const parsed=JSON.parse(raw);
    if(!parsed||typeof parsed.day!=='string'||!parsed.items||typeof parsed.items!=='object'||Array.isArray(parsed.items))throw Error('Reminder storage could not be read.');
    for(const v of Object.values(parsed.items) as Delivery[])if(!v||!['shown','dismissed','snoozed'].includes(v.status)||v.status==='snoozed'&&(!Number.isFinite(v.until)||v.until!<0))throw Error('Reminder storage is invalid.');
    return parsed.day===day?parsed:{day,items:{}};
  }
  private write(value:Ledger){const raw=JSON.stringify(value);localStorage.setItem(this.key,raw);if(localStorage.getItem(this.key)!==raw)throw Error('Reminder storage changed in another tab.');}
  private async lock<T>(job:()=>T):Promise<T>{return typeof navigator!=='undefined'&&navigator.locks?navigator.locks.request(this.key,job):job();}
  async next(overview:Overview,prefs:Preferences,now=new Date()):Promise<Habit|null>{
    if(!prefs.notifications)return null;
    const at=zonedTime(overview.timezone,now);if(at.day!==overview.today||inQuietHours(at.time,prefs))return null;
    return this.lock(()=>{const ledger=this.read(at.day);const habit=overview.habits.find(h=>{
      const r=prefs.reminders[h.id],delivery=ledger.items[h.id];
      return !h.completed&&r?.enabled&&r.time<=at.time&&(!delivery||delivery.status==='snoozed'&&(delivery.until??Infinity)<=now.getTime());
    });if(!habit)return null;ledger.items[habit.id]={status:'shown'};this.write(ledger);return habit;});
  }
  async settle(id:string,day:string,snooze=false,now=new Date()){return this.lock(()=>{const ledger=this.read(day);ledger.items[id]=snooze?{status:'snoozed',until:now.getTime()+600000}:{status:'dismissed'};this.write(ledger);});}
}

