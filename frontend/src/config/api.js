export const backendApiUrl = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export const redTeamApiUrl = (process.env.REACT_APP_RED_TEAM_API_URL || 'http://127.0.0.1:8010').replace(/\/$/, '');
