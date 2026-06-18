// Persona API client helpers.
//
// The backend owns persona generation/caching; the frontend only requests the
// current country/limit slice and renders the returned profile metadata.

import { backendApiUrl } from '../../config/api';


export async function fetchPersonas({ country = 'netherlands', limit = 30 } = {}) {
  const response = await fetch(`${backendApiUrl}/api/chat/personas?country=${country}&limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Persona request failed with status ${response.status}`);
  }
  return response.json();
}
