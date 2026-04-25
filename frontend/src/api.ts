import axios from 'axios';
import type { ParseResponse, PlanStoreRequest, PlanStoreResponse } from './types';

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

export async function storePlan(req: PlanStoreRequest): Promise<PlanStoreResponse> {
  const response = await axios.post<PlanStoreResponse>(
    `${API_BASE}/plans`,
    req,
    { timeout: 30000 },
  );
  return response.data;
}

export function buildGcalSubscribeUrl(planId: string): string {
  const feedBase = import.meta.env.PROD
    ? 'https://syllabus-to-calendar-vfegtvvl.fly.dev'
    : window.location.origin;
  const icsUrl = `${feedBase}/api/plans/${planId}/calendar.ics`;
  return `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(icsUrl)}`;
}
