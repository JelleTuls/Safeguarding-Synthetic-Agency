// Red-team API client helpers.
//
// The main backend can launch the standalone red-team service; once running,
// these helpers talk to both APIs for run creation, polling, review submission,
// and final report download links.

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

export async function generateRedTeamAnalysis(runId) {
  const response = await fetch(`${backendApiUrl}/api/red-team/runs/${runId}/analysis`, {
    method: 'POST',
  });
  return parseJsonResponse(response, 'Could not generate computational analysis');
}

export async function fetchRedTeamAnalysis(runId) {
  const response = await fetch(`${backendApiUrl}/api/red-team/runs/${runId}/analysis`);
  if (!response.ok) {
    return null;
  }
  return response.json();
}

export async function fetchFinalReports() {
  const response = await fetch(`${backendApiUrl}/api/red-team/final-reports`);
  return parseJsonResponse(response, 'Could not load final report JSON files');
}

export async function fetchFinalReportDataset(runId) {
  const response = await fetch(finalReportDatasetJsonUrl(runId));
  return parseJsonResponse(response, 'Could not load final report dataset');
}

export async function deleteFinalReport(runId) {
  const response = await fetch(`${backendApiUrl}/api/red-team/final-reports/${runId}`, {
    method: 'DELETE',
  });
  return parseJsonResponse(response, 'Could not delete final report dataset');
}

export async function generateAnalysisFromFinalReport(runId) {
  const response = await fetch(`${backendApiUrl}/api/red-team/final-reports/${runId}/analysis`, {
    method: 'POST',
  });
  return parseJsonResponse(response, 'Could not generate analysis from final report');
}

export function finalReportPdfUrl(runId) {
  return `${backendApiUrl}/api/red-team/final-reports/${runId}/pdf`;
}

export function finalReportJsonUrl(runId) {
  return finalReportDatasetJsonUrl(runId);
}

export function analysisArtifactUrl(runId, artifact) {
  return `${backendApiUrl}/api/red-team/runs/${runId}/analysis/artifacts/${artifact}`;
}

export function analysisZipUrl(runId) {
  return `${backendApiUrl}/api/red-team/runs/${runId}/analysis.zip`;
}

export function analysisVisualZipUrl(runId) {
  return `${backendApiUrl}/api/red-team/runs/${runId}/analysis/artifacts/visual_zip`;
}

export function analysisPlotPngUrl(runId, artifact, width = 1800) {
  return `${backendApiUrl}/api/red-team/runs/${runId}/analysis/plots/${artifact}.png?width=${width}`;
}

export function finalReportDatasetJsonUrl(runId) {
  return `${backendApiUrl}/api/red-team/final-reports/${runId}/json`;
}
