import axios from 'axios';
import type { ParseResponse, CalendarExportRequest, CalendarExportResponse } from './types';

const API_BASE = import.meta.env.PROD
  ? 'https://syllabus-to-calendar-vfegtvvl.fly.dev/api'
  : '/api';

export async function parseSyllabus(file: File): Promise<ParseResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post<ParseResponse>(`${API_BASE}/parse`, formData, {
    timeout: 120000,
  });

  return response.data;
}

export async function exportIcs(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${API_BASE}/export/ics`, formData, {
    responseType: 'blob',
    timeout: 120000,
  });

  return response.data;
}

export function generateGcalLink(
  title: string,
  date: string,
  time: string | null,
  durationMinutes: number,
  description: string = '',
): string {
  const startDt = time ? `${date}T${time}:00` : `${date}T09:00:00`;
  const start = new Date(startDt);
  const end = new Date(start.getTime() + durationMinutes * 60000);

  const fmt = (d: Date) =>
    d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');

  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: title,
    dates: `${fmt(start)}/${fmt(end)}`,
    details: description,
  });

  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export async function exportToGoogleCalendar(
  req: CalendarExportRequest,
): Promise<CalendarExportResponse> {
  const response = await axios.post<CalendarExportResponse>(
    `${API_BASE}/calendar/export`,
    req,
    { timeout: 120000 },
  );
  return response.data;
}

// --- User data persistence (MongoDB) ---

export interface UserDataResponse {
  courses: { name: string; data: ParseResponse }[];
  task_progress: Record<string, { completed_items: string[]; custom_tasks: { id: string; text: string; completed: boolean }[] }>;
  cold_calls: Record<string, string>;
}

export async function fetchUserCourses(uid: string): Promise<UserDataResponse> {
  const response = await axios.get<UserDataResponse>(`${API_BASE}/user-data/${uid}/courses`);
  return response.data;
}

export async function saveUserCourse(uid: string, courseName: string, courseData: ParseResponse): Promise<void> {
  await axios.put(`${API_BASE}/user-data/courses`, {
    uid,
    course_name: courseName,
    course_data: courseData,
  });
}

export async function deleteUserCourse(uid: string, courseName: string): Promise<void> {
  await axios.delete(`${API_BASE}/user-data/${uid}/courses/${encodeURIComponent(courseName)}`);
}

export async function saveUserTaskProgress(
  uid: string,
  courseName: string,
  completedItems: string[],
  customTasks: { id: string; text: string; completed: boolean }[],
): Promise<void> {
  await axios.put(`${API_BASE}/user-data/tasks`, {
    uid,
    course_name: courseName,
    completed_items: completedItems,
    custom_tasks: customTasks,
  });
}

export async function recordColdCall(uid: string, courseName: string): Promise<string> {
  const response = await axios.put<{ status: string; date: string }>(`${API_BASE}/user-data/cold-call`, {
    uid,
    course_name: courseName,
  });
  return response.data.date;
}
