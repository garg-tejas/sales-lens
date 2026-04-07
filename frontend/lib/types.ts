export interface Call {
  id: string;
  filename: string;
  language: string;
  created_at: string;
}

export interface TranscriptSegment {
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
}

export interface Objection {
  text: string;
  severity?: string;
  timestamp?: number;
}

export interface ActionItem {
  text: string;
  priority?: string;
  assignee?: string;
}

export interface CallScore {
  total: number;
  breakdown?: Record<string, number>;
}

export interface Insights {
  call_score?: CallScore;
  objections?: Objection[];
  action_items?: ActionItem[];
  sentiment_timeline?: SentimentPoint[];
  summary?: string;
  key_topics?: string[];
}

export interface SentimentPoint {
  timestamp: string;
  score: number;
}

export interface QAResponse {
  answer: string;
  sources?: string[];
}

export type ConnectionStatus = "connecting" | "connected" | "reconnecting" | "closed";

export interface StreamEvent {
  type: string;
  seq?: number;
  progress?: number;
  is_partial?: boolean;
  segment?: TranscriptSegment;
}
