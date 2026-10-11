import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

export interface Readiness { status: 'ready'; phase: 'foundation'; tracking_available: false; }

@Injectable({ providedIn: 'root' })
export class ReadinessService {
  private readonly http = inject(HttpClient);
  check() { return this.http.get<Readiness>('/api/ready'); }
}
