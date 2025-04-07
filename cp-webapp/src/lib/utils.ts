import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function getProxiedImageUrl(url: string) {
  if (!url) return url;
  // Using Cloudflare's proxy service
  return `https://images.1choice.ai?url=${encodeURIComponent(url)}`;
}

export function convertToISO8601(dateString: string): string {
  // Check if the input string matches the expected format
  const regex = /^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) ([+-]\d{4})$/;
  const match = dateString.match(regex);

  if (!match) {
    throw new Error('Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS ±HHMM');
  }

  const [, datePart, timePart, timezonePart] = match;

  // Insert 'T' between date and time
  // Format timezone offset by inserting a colon (e.g., -0800 -> -08:00)
  const formattedTimezone = `${timezonePart.slice(0, 3)}:${timezonePart.slice(3)}`;

  return `${datePart}T${timePart}${formattedTimezone}`;
}
