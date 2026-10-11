export interface Habit { id:string;name:string;description:string;created_at:string;start_date:string;completed:boolean; }
export interface Overview { today:string;timezone:string;habits:Habit[];completed:number;total:number;remaining:number;completion_percentage:number|null;recent_days:{day:string;completed:number}[]; }
export interface Progress { today:string;recorded_completions:number;history:{habit_id:string;habit_name:string;day:string}[]; }
export interface Reply { message:string;source:string;choices:{id:string;question:string}[];question_id:string|null; }
