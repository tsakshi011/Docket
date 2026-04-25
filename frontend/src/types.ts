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

export interface ParseResponse {
  course_name: string;
  semester: string;
  instructor: string | null;
  syllabus_events: SyllabusEvent[];
  study_blocks: StudyBlock[];
  weekly_summary: string[];
  warnings: string[];
  raw_text_preview: string;
}

export type AppStep = 'upload' | 'processing' | 'review' | 'success';

<<<<<<< HEAD
export interface PlanStoreRequest {
  course_name: string;
=======
export interface CalendarExportRequest {
  course_name: string;
  access_token: string;
>>>>>>> 5e078a0fb8605bca5ad6a1298f51f11e70d11d99
  syllabus_events: SyllabusEvent[];
  study_blocks: StudyBlock[];
}

<<<<<<< HEAD
export interface PlanStoreResponse {
  plan_id: string;
=======
export interface CalendarExportResponse {
  calendar_id: string;
  calendar_url: string;
  events_created: number;
>>>>>>> 5e078a0fb8605bca5ad6a1298f51f11e70d11d99
}
