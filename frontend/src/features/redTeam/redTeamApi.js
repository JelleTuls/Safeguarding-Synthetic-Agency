import { backendApiUrl, redTeamApiUrl } from '../../config/api';


async function parseJsonResponse(response, message) {
  if (!response.ok) {
    throw new Error(`${message}: ${response.status}`);
  }
  return response.json();
}

export async function startRedTeamService() {
  const response = await fetch(`${backendApiUrl}/api/red-team/service/start`, {
    method: 'POST',
  });
  const payload = await parseJsonResponse(response, 'Could not start red-team service');
  if (!payload.ready) {
    throw new Error('Red-team service did not become ready.');
  }
  return payload;
}

export async function fetchPromptSettings() {
  const response = await fetch(`${redTeamApiUrl}/api/prompt-settings`);
  return parseJsonResponse(response, 'Could not load red-team prompt settings');
}

export async function createRedTeamRun(payload) {
  const response = await fetch(`${redTeamApiUrl}/api/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse(response, 'Could not start red-team run');
}

export async function fetchRedTeamRun(runId) {
  const response = await fetch(`${redTeamApiUrl}/api/runs/${runId}`);
  return parseJsonResponse(response, 'Red-team run request failed');
}

export async function fetchRedTeamReviewItems(runId) {
  const response = await fetch(`${redTeamApiUrl}/api/runs/${runId}/review-items`);
  if (!response.ok) {
    return null;
  }
  return response.json();
}

export async function cancelRedTeamRun(runId) {
  const response = await fetch(`${redTeamApiUrl}/api/runs/${runId}/cancel`, {
    method: 'POST',
  });
  return parseJsonResponse(response, 'Could not cancel red-team run');
}

export async function submitRedTeamReview({ runId, caseId, review }) {
  const response = await fetch(`${redTeamApiUrl}/api/runs/${runId}/review-items/${caseId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(review),
  });
  return parseJsonResponse(response, 'Could not save human review');
}

export async function finalizeRedTeamRun(runId) {
  const response = await fetch(`${redTeamApiUrl}/api/runs/${runId}/finalize`, {
    method: 'POST',
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Could not save final results: ${response.status} ${message}`);
  }
  return response.json();
}
