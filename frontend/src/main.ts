import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { App } from './app/app';
import { provideHttpClient } from '@angular/common/http';
bootstrapApplication(App, { providers: [provideRouter([]), provideHttpClient()] }).catch(() => console.error('Routiq could not start.'));
