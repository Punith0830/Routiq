import { FAQ } from './demo-faq';
import { Reply } from './tracker.models';

const STARTERS = ['How am I doing today?', 'What is still pending?', 'Can you suggest a small starting habit?', 'How can I make reading easier to maintain?'];
type Topic = 'today' | 'reading' | 'workout' | 'setup' | 'privacy' | 'general';
const groups: Record<Topic, string[]> = {
  today: ['Q-014','Q-015','Q-077','Q-083','Q-011','Q-017','Q-021','Q-055','Q-078','Q-082','Q-084','Q-012'],
  reading: ['Q-140','Q-142','Q-145','Q-147','Q-024','Q-044','Q-148','Q-031','Q-028','Q-029'],
  workout: ['Q-143','Q-142','Q-145','Q-147','Q-148','Q-031','Q-139','Q-141'],
  setup: ['Q-023','Q-026','Q-028','Q-029','Q-043','Q-025','Q-046','Q-189','Q-188','Q-024','Q-044'],
  privacy: ['Q-250','Q-251','Q-252','Q-253','Q-254','Q-188','Q-023','Q-031'],
  general: ['Q-031','Q-142','Q-145','Q-147','Q-148','Q-139','Q-141','Q-140','Q-143','Q-023'],
};
const byId = new Map(FAQ.map(q => [q.id, q]));
const eligible = new Set(Object.values(groups).flat());
const normalize = (s: string) => s.toLowerCase().replace(/[’‘]/g,"'").replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
const tokens = (s: string) => new Set(normalize(s).split(' ').filter(t => t.length > 2 && !['the','and','can','how','what','with','for','you','your','habit','habits','could','should'].includes(t)));

/** Conversation-local suggestions only. No network, storage or generated claims. */
export class CoachSuggestions {
  private topic: Topic = 'general';
  private asked: string[] = [];
  private shown: string[] = [];

  reset(): string[] {
    this.topic = 'general'; this.asked = []; this.shown = [];
    return [...STARTERS];
  }

  next(message: string, reply: Reply): string[] {
    const text = normalize(message);
    const matched = byId.get(reply.question_id || '') || FAQ.find(q => normalize(q.question) === text);
    const sensitive = /sk-[\w-]{8,}|api.?key|password|ignore.{0,35}instructions|reveal.{0,35}prompt/i.test(message);
    const followup = /^(and )?(what else|tell me more|more|another idea|what next|can you explain|go on|why)\b/.test(text);
    let topic: Topic = 'general';
    if (!sensitive) {
      if (reply.source === 'verified_local_data') topic = 'today';
      else if (/\b(read|reading|book|books)\b/.test(text)) topic = 'reading';
      else if (/\b(workout|exercise|fitness)\b/.test(text)) topic = 'workout';
      else if (/\b(privacy|data|conversation|conversations|chat history|export|access|opt out)\b/.test(text)) topic = 'privacy';
      else if (reply.source === 'verified_local_data' || /\b(today|pending|complete|completed|remaining|left)\b/.test(text)) topic = 'today';
      else if (matched?.id !== 'Q-031' && /\b(create|add|edit|rename|description|name|find)\b/.test(text)) topic = 'setup';
      else if (followup) topic = this.topic;
      // Clarification choices can identify a topic even if the user's words did not.
      else if (reply.source === 'clarification') {
        const choice = reply.choices.find(q => eligible.has(q.id));
        if (choice) topic = (['today','setup','privacy'] as Topic[]).find(t => groups[t].includes(choice.id)) || 'general';
      }
    }
    this.topic = topic;
    if (matched) this.asked = [...this.asked.filter(id => id !== matched.id), matched.id].slice(-8);
    const inputTokens = tokens(message);
    const choices = new Set(sensitive ? [] : reply.choices.map(q => q.id));
    const server = new Set(sensitive ? [] : (reply.suggestions || []).map(q => q.id));
    const rank = groups[topic].filter(id => id !== matched?.id).map((id, index) => {
      const question = byId.get(id)!;
      const overlap = [...tokens(question.question)].filter(t => inputTokens.has(t)).length;
      return { id, question: question.question, score: (choices.has(id) ? 8 : 0) + (server.has(id) ? 2 : 0) + Math.min(overlap, 3) - index / 20 - (this.shown.includes(id) ? 5 : 0) - (this.asked.includes(id) ? 12 : 0) };
    }).filter(q => normalize(q.question) !== text).sort((a,b) => b.score - a.score);
    const result = rank.slice(0,4);
    this.shown = result.map(q => q.id);
    return result.map(q => q.question);
  }
}
