import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { of, switchMap, timeout } from 'rxjs';
import { TrackerService as BrowserTracker } from './tracker.demo.service';
import { Reply } from './tracker.models';
import { environment } from '../../environments/environment.production';
export type { Habit, Overview, Progress, Reply } from './tracker.models';

@Injectable({providedIn:'root'})
export class TrackerService extends BrowserTracker {
  override readonly isAssignment=true;
  private readonly http=inject(HttpClient);
  override chat(message:string){
    // Only questions leave the browser. Never send habit names or check-ins.
    return super.chat(message).pipe(switchMap(reply=>{
      if(reply.source==='verified_local_data'||/sk-[\w-]{8,}|api.?key|password|ignore.{0,35}instructions|reveal.{0,35}prompt/i.test(message))return of(reply);
      const origin=new URL(environment.apiBaseUrl);
      if(origin.protocol!=='https:'||origin.origin!==environment.apiBaseUrl)throw new Error('Configure the Render API origin before deploying.');
      return this.http.post<Reply>(`${origin.origin}/api/coach/chat`,{message}).pipe(timeout(60000));
    }));
  }
}
