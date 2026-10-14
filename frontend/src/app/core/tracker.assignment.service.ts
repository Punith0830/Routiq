import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, of, switchMap, timeout } from 'rxjs';
import { TrackerService as BrowserTracker } from './tracker.demo.service';
import { Reply } from './tracker.models';
import { ASSIGNMENT_REMOTE_TIMEOUT_MS, shouldUseRemoteCoach } from './assignment-chat-routing';
import { environment } from '../../environments/environment.production';
export type { Habit, Overview, Progress, Reply } from './tracker.models';

@Injectable({providedIn:'root'})
export class TrackerService extends BrowserTracker {
  override readonly isAssignment=true;
  private readonly http=inject(HttpClient);
  override chat(message:string){
    // Prepared answers and verified Today summaries stay in the browser. Only an
    // unmatched custom question can reach Render; habit names and check-ins never do.
    return super.chat(message).pipe(switchMap(reply=>{
      if(!shouldUseRemoteCoach(message,reply))return of(reply);
      const origin=new URL(environment.apiBaseUrl);
      if(origin.protocol!=='https:'||origin.origin!==environment.apiBaseUrl)throw new Error('Configure the Render API origin before deploying.');
      return this.http.post<Reply>(`${origin.origin}/api/coach/chat`,{message}).pipe(
        timeout(ASSIGNMENT_REMOTE_TIMEOUT_MS),
        catchError(()=>of(reply))
      );
    }));
  }
}
