// Shared API endpoint configuration for the frontend.
//
// Environment variables let local development, hosted demos, and red-team
// service debugging point at different backend URLs without changing components.

export const backendApiUrl = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export const redTeamApiUrl = (process.env.REACT_APP_RED_TEAM_API_URL || 'http://127.0.0.1:8010').replace(/\/$/, '');
