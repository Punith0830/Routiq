import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import {Habit, Overview, Progress, Reply} from './tracker.models';
import {Preferences, Rewards} from './preferences';
export type {Habit, Overview, Progress, Reply} from './tracker.models';
@Injectable({providedIn:'root'})
export class TrackerService {
  readonly isAssignment:boolean=false;
  readonly isDemo=false;
  private readonly http=inject(HttpClient);
  private readonly headers=new HttpHeaders({'X-Routiq-Timezone':Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'});
  overview(){return this.http.get<Overview>('/api/habits',{headers:this.headers});}
  progress(){return this.http.get<Progress>('/api/progress',{headers:this.headers});}
  save(payload:import('./tracker.models').HabitInput,id:string|null){return id?this.http.patch<Habit>(`/api/habits/${encodeURIComponent(id)}`,payload,{headers:this.headers}):this.http.post<Habit>('/api/habits',payload,{headers:this.headers});}
  settings(){return this.http.get<Preferences>('/api/settings');}
  saveSettings(payload:Preferences){return this.http.put<Preferences>('/api/settings',payload);}
  rewards(){return this.http.get<Rewards>('/api/rewards',{headers:this.headers});}
  complete(habit:Habit,day:string){const url=`/api/habits/${encodeURIComponent(habit.id)}/completions/${day}`;return habit.completed?this.http.delete<Overview>(url,{headers:this.headers}):this.http.put<Overview>(url,{},{headers:this.headers});}
  chat(message:string){return this.http.post<Reply>('/api/coach/chat',{message},{headers:this.headers});}
}
