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
