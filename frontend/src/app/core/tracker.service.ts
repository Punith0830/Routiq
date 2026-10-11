import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
export interface Habit { id:string;name:string;description:string;created_at:string;start_date:string;completed:boolean; }
export interface Overview { today:string;timezone:string;habits:Habit[];completed:number;total:number;remaining:number;completion_percentage:number|null;recent_days:{day:string;completed:number}[]; }
export interface Progress { today:string;recorded_completions:number;history:{habit_id:string;habit_name:string;day:string}[]; }
export interface Reply { message:string;source:string;choices:{id:string;question:string}[];question_id:string|null; }
@Injectable({providedIn:'root'})
export class TrackerService {
  private readonly http=inject(HttpClient);
  private readonly headers=new HttpHeaders({'X-Routiq-Timezone':Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'});
  overview(){return this.http.get<Overview>('/api/habits',{headers:this.headers});}
  progress(){return this.http.get<Progress>('/api/progress',{headers:this.headers});}
  save(payload:{name:string;description:string},id:string|null){return id?this.http.patch<Habit>(`/api/habits/${encodeURIComponent(id)}`,payload,{headers:this.headers}):this.http.post<Habit>('/api/habits',payload,{headers:this.headers});}
  complete(habit:Habit,day:string){const url=`/api/habits/${encodeURIComponent(habit.id)}/completions/${day}`;return habit.completed?this.http.delete<Overview>(url,{headers:this.headers}):this.http.put<Overview>(url,{},{headers:this.headers});}
  chat(message:string){return this.http.post<Reply>('/api/coach/chat',{message},{headers:this.headers});}
}
