export interface Reminder {enabled:boolean;time:string;}
export interface Preferences {
  display_name:string;avatar_image:string;avatar:'initial'|'leaf'|'sun'|'spark';theme:'system'|'light'|'dark';
  reduced_motion:boolean;celebrations:boolean;gamification:boolean;notifications:boolean;
  quiet_hours:boolean;quiet_start:string;quiet_end:string;reminders:Record<string,Reminder>;
}
export interface Rewards {recorded:number;points:number;milestones:{target:number;progress:number;earned:boolean}[];}
export const defaultPreferences=():Preferences=>({display_name:'',avatar_image:'',avatar:'initial',theme:'system',reduced_motion:false,celebrations:true,gamification:true,notifications:false,quiet_hours:false,quiet_start:'22:00',quiet_end:'08:00',reminders:{}});
export function validatePreferences(value:unknown):Preferences{
  if(!value||typeof value!=='object')throw Error('Invalid preferences');
  const v=value as Record<string,unknown>,d=defaultPreferences();
  if(Object.keys(v).some(k=>!(k in d)))throw Error('Unknown preference');
  const p={...d,...v} as Preferences;
  if(typeof p.display_name!=='string'||p.display_name.trim().length>80||!['initial','leaf','sun','spark'].includes(p.avatar)||!['system','light','dark'].includes(p.theme))throw Error('Invalid profile or theme');
  if(typeof p.avatar_image!=='string'||p.avatar_image.length>200000||p.avatar_image&&!/^data:image\/jpeg;base64,\/9j\/[A-Za-z0-9+/]+={0,2}$/.test(p.avatar_image))throw Error('Choose a valid profile photo.');
  for(const key of ['reduced_motion','celebrations','gamification','notifications','quiet_hours'] as const)if(typeof p[key]!=='boolean')throw Error('Invalid switch');
  const valid=(s:unknown)=>typeof s==='string'&&/^([01]\d|2[0-3]):[0-5]\d$/.test(s);
  if(!valid(p.quiet_start)||!valid(p.quiet_end)||p.quiet_hours&&p.quiet_start===p.quiet_end)throw Error('Choose different valid quiet-hours start and end times.');
  if(!p.reminders||typeof p.reminders!=='object'||Array.isArray(p.reminders)||Object.keys(p.reminders).length>100)throw Error('Invalid reminders');
  for(const r of Object.values(p.reminders))if(!r||Object.keys(r).some(k=>!['enabled','time'].includes(k))||typeof r.enabled!=='boolean'||!valid(r.time))throw Error('Choose a valid reminder time.');
  return {...p,display_name:p.display_name.trim(),reminders:structuredClone(p.reminders)};
}
export function rewardSummary(recorded:number):Rewards{return {recorded,points:recorded*10,milestones:[1,5,20].map(target=>({target,progress:Math.min(recorded,target),earned:recorded>=target}))};}
export function zonedTime(zone:string,now=new Date()){
  const parts=new Intl.DateTimeFormat('en-GB',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now);
  const part=(key:string)=>parts.find(p=>p.type===key)!.value;
  return {day:part('year')+'-'+part('month')+'-'+part('day'),time:part('hour')+':'+part('minute')};
}
export function inQuietHours(time:string,p:Preferences){return p.quiet_hours&&(p.quiet_start<p.quiet_end?time>=p.quiet_start&&time<p.quiet_end:time>=p.quiet_start||time<p.quiet_end);}
export function featureHelp(message:string):string|null{
  const t=message.toLowerCase();
  if(/\b(points?|rewards?|milestones?|gamification|badges)\b/.test(t))return 'Each eligible recorded habit earns 10 points per day. Undo recalculates points and milestones at 1, 5 and 20 recorded check-ins. Rewards are optional in Settings; missing a day does not erase earlier records.';
  if(/\b(reminders?|notifications?|snooze|quiet hours)\b/.test(t))return 'Use Settings → Notifications to choose a reminder time for a habit. In-app reminders work while Routiq is open. Quiet hours and completed habits suppress reminders. Dismiss for today or snooze for 10 minutes. There is no background delivery promise.';
  if(/\b(themes?|settings|profile|version|animations|synced)\b/.test(t))return 'Settings contains a local display name and uploaded profile photo, System/Light/Dark appearance, reduced motion, optional rewards, in-app reminders and the application version. No account or cross-device sync.';
  return null;
}

