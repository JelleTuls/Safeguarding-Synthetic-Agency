import { backendApiUrl } from '../../config/api';


export async function fetchPersonas({ country = 'netherlands', limit = 30 } = {}) {
  const response = await fetch(`${backendApiUrl}/api/chat/personas?country=${country}&limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Persona request failed with status ${response.status}`);
  }
  return response.json();
}
