import type { Reply } from './tracker.models';

export const ASSIGNMENT_REMOTE_TIMEOUT_MS=2500;

const sensitive=/sk-[\w-]{8,}|api.?key|password|ignore.{0,35}instructions|reveal.{0,35}prompt/i;

export function shouldUseRemoteCoach(message:string,reply:Reply){
  return !reply.question_id&&reply.source!=='verified_local_data'&&!sensitive.test(message);
}
