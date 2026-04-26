export interface SyllabusEvent {
  title: string;
  date: string;
  time: string | null;
  duration_minutes: number;
  event_type: string;
  description: string;
  weight: string | null;
  selected?: boolean;
}

export interface StudyBlock {
  title: string;
  date: string;
  time: string | null;
  duration_minutes: number;
  block_type: string;
  related_event: string;
  description: string;
  priority: string;
  selected?: boolean;
}

export interface OutlineSubtopic {
  name: string;
  rules: string[];
  cases: string[];
  notes: string;
}

export interface OutlineSection {
  topic: string;
  subtopics: OutlineSubtopic[];
  key_concepts: string[];
}

export interface ParseResponse {
  course_name: string;
  semester: string;
  instructor: string | null;
  syllabus_events: SyllabusEvent[];
  study_blocks: StudyBlock[];
  weekly_summary: string[];
  warnings: string[];
  course_outline: OutlineSection[];
  raw_text_preview: string;
}

export type AppStep = 'upload' | 'processing' | 'review' | 'success';

export interface CalendarExportRequest {
  course_name: string;
  access_token: string;
  syllabus_events: SyllabusEvent[];
  study_blocks: StudyBlock[];
}

export interface CalendarExportResponse {
  calendar_id: string;
  calendar_url: string;
  events_created: number;
}
