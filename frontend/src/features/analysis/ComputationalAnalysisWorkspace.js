// Standalone computational-analysis workspace.
//
// This view lists saved final-results JSON reports from the red-team service and
// lets the user generate reproducible computational-analysis artifacts without
// starting a new red-team run.

import { useEffect, useMemo, useState } from 'react';

import {
  analysisArtifactUrl,
  analysisPlotPngUrl,
  deleteFinalReport,
  fetchFinalReports,
  fetchRedTeamAnalysis,
  finalReportDatasetJsonUrl,
  generateAnalysisFromFinalReport,
} from '../redTeam/redTeamApi';
import { formatPercent } from '../redTeam/redTeamUtils';

import './computationalAnalysisWorkspace.css';

const plotDownloadSizes = [
  { label: '1200 px', value: 1200 },
  { label: '1800 px', value: 1800 },
  { label: '2400 px', value: 2400 },
  { label: '3200 px', value: 3200 },
];

const figureKeys = [
  ['paired_delta_forest', 'Paired guardrail effect forest plot'],
  ['pairwise_win_rate', 'Pairwise win rate'],
  ['failure_transition_matrix_plot', 'Failure transition matrix'],
  ['score_distributions_boxplot', 'Score distributions'],
  ['delta_ecdf_by_method', 'Delta ECDF by method'],
  ['stability_frontier', 'Performance-stability frontier'],
  ['guardrail_delta_heatmap', 'Guardrail delta heatmap'],
];

const fallbackFigureGroups = {
  thesis: [
    'paired_delta_forest',
    'pairwise_win_rate',
    'failure_transition_matrix_plot',
    'delta_ecdf_by_method',
    'score_distributions_boxplot',
    'stability_frontier',
    'guardrail_delta_heatmap',
  ],
};

const groupLabels = {
  thesis: 'Selected thesis figures',
  diagnostic: 'Diagnostic figures',
  descriptive: 'Descriptive figures',
};

function figureLabel(key, analysis) {
  return analysis?.figures?.[key]?.title || figureKeys.find(([item]) => item === key)?.[1] || key.replaceAll('_', ' ');
}

function visibleFigureKeys(analysis) {
  return new Set(Object.values(analysis?.figure_groups || fallbackFigureGroups).flat());
}

function dateLabel(value) {
  if (!value) return 'Unknown date';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function ComputationalAnalysisWorkspace({ onRegisterBackHandler }) {
  const [reports, setReports] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [plotSizes, setPlotSizes] = useState({});

  const selectedReport = useMemo(() => (
    reports.find((report) => report.run_id === selectedRunId) || null
  ), [reports, selectedRunId]);

  async function loadReports() {
    setStatus('loading');
    setError(null);
    try {
      const payload = await fetchFinalReports();
      const nextReports = payload.reports || [];
      setReports(nextReports);
      setSelectedRunId((current) => (
        nextReports.some((report) => report.run_id === current) ? current : null
      ));
      setStatus('ready');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  useEffect(() => {
    if (!selectedReport?.run_id) {
      setAnalysis(null);
      return;
    }
    fetchRedTeamAnalysis(selectedReport.run_id)
      .then((payload) => setAnalysis(payload))
      .catch(() => setAnalysis(null));
  }, [selectedReport?.run_id]);

  async function handleGenerate() {
    if (!selectedReport?.run_id) return;
    setStatus('generating');
    setError(null);
    try {
      const payload = await generateAnalysisFromFinalReport(selectedReport.run_id);
      setAnalysis(payload);
      setReports((current) => current.map((report) => (
        report.run_id === selectedReport.run_id ? { ...report, analysis_available: true } : report
      )));
      setStatus('ready');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  async function handleDeleteReport(event, report) {
    const confirmed = window.confirm(`Delete ${report.filename} and its matching PDF report? This also removes generated analysis artifacts for this dataset.`);
    if (!confirmed) return;
    setStatus('deleting');
    setError(null);
    try {
      await deleteFinalReport(report.run_id);
      setReports((current) => current.filter((item) => item.run_id !== report.run_id));
      if (selectedRunId === report.run_id) {
        setSelectedRunId(null);
        setAnalysis(null);
      }
      setStatus('ready');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }

  function handleSelectReport(runId) {
    setSelectedRunId(runId);
    setAnalysis(null);
    setError(null);
  }

  function handleBackToSelection() {
    setSelectedRunId(null);
    setAnalysis(null);
    setError(null);
  }

  useEffect(() => {
    if (!onRegisterBackHandler) {
      return undefined;
    }
    onRegisterBackHandler(() => {
      if (!selectedReport) {
        return false;
      }
      handleBackToSelection();
      return true;
    });
    return () => onRegisterBackHandler(null);
  }, [onRegisterBackHandler, selectedReport]);

  return (
    <section className="analysisWorkspace">
      <header className="analysisTop">
        <p className="analysisEyebrow">Computational analysis</p>
        <h2>Recreate thesis plots from saved red-team results</h2>
        <p>{selectedReport ? 'Inspect generated analytical plots, tables, and downloadable artifacts for the selected red-team report.' : 'Select an earlier final-results JSON file first. The next page generates reproducible tables, SVG plots, and a downloadable artifact bundle.'}</p>
      </header>

      <div className="analysisActionRow">
        {selectedReport ? (
          <>
            <button type="button" className="isSecondary" onClick={handleBackToSelection}>Back to JSON files</button>
            <button type="button" className="isPrimary" disabled={status === 'generating'} onClick={handleGenerate}>
              {status === 'generating' ? 'Generating analysis' : analysis ? 'Regenerate analysis' : 'Generate analysis'}
            </button>
          </>
        ) : (
          <button type="button" className="isSecondary" onClick={loadReports}>Refresh JSON files</button>
        )}
      </div>

      {error && <p className="analysisError">{error}</p>}

      {!selectedReport ? (
        <div className="analysisScrollableBody">
          {status === 'loading' && <p className="analysisMuted">Loading eligible reports...</p>}
          {reports.length === 0 && status !== 'loading' && (
            <p className="analysisMuted">No saved final-results JSON files were found.</p>
          )}
          <div className="analysisReportButtons">
            {reports.map((report) => (
              <div className="analysisReportCard" key={report.run_id}>
                <button
                  className="analysisReportSelect"
                  type="button"
                  onClick={() => handleSelectReport(report.run_id)}
                >
                  <strong>{report.filename}</strong>
                  <span>{report.case_count} cases · {report.profile_count} profiles · {dateLabel(report.finalized_at || report.completed_at)}</span>
                  <small>{report.analysis_available ? 'Analysis ready' : 'Analysis not generated'}</small>
                </button>
                <button
                  className="analysisDeleteButton"
                  disabled={status === 'deleting'}
                  onClick={(event) => handleDeleteReport(event, report)}
                  type="button"
                >
                  {status === 'deleting' ? 'Deleting' : 'Delete'}
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="analysisScrollableBody">
          <div className="analysisScoreSet">
            <div>
              <span>Overall</span>
              <strong>{formatPercent(selectedReport.overall_score)}</strong>
            </div>
            <div>
              <span>Guardrailed</span>
              <strong>{selectedReport.guardrailed_score === null || selectedReport.guardrailed_score === undefined ? 'N/A' : formatPercent(selectedReport.guardrailed_score)}</strong>
            </div>
            <div>
              <span>Lightweight</span>
              <strong>{selectedReport.lightweight_score === null || selectedReport.lightweight_score === undefined ? 'N/A' : formatPercent(selectedReport.lightweight_score)}</strong>
            </div>
            <div>
              <span>Mean delta</span>
              <strong>{analysis?.overall_mean_delta === null || analysis?.overall_mean_delta === undefined ? 'N/A' : `${analysis.overall_mean_delta >= 0 ? '+' : ''}${Math.round(analysis.overall_mean_delta * 100)}%`}</strong>
            </div>
          </div>

          {analysis && (
          <>
            <div className="analysisCaseSummary">
              <div className="analysisCaseMetric">
                <span>Total cases</span>
                <strong>{analysis.case_count}</strong>
              </div>
              <div className="analysisCaseMetric">
                <span>Paired cases</span>
                <strong>{analysis.paired_case_count}</strong>
              </div>
            </div>

            <div className="analysisDownloads">
              <a href={finalReportDatasetJsonUrl(selectedReport.run_id)}>Download full JSON dataset</a>
            </div>

            {analysis.warnings?.length > 0 && (
              <div className="analysisWarnings">
                {analysis.warnings.map((warning) => (
                  <p key={warning}>{warning}</p>
                ))}
              </div>
            )}

            {analysis.skipped_figures && Object.entries(analysis.skipped_figures).some(([key]) => visibleFigureKeys(analysis).has(key)) && (
              <div className="analysisSkipped">
                <strong>Skipped advanced plots</strong>
                <span>
                  {Object.entries(analysis.skipped_figures)
                    .filter(([key]) => visibleFigureKeys(analysis).has(key))
                    .map(([key, reason]) => `${figureLabel(key, analysis)}: ${reason}`)
                    .join(' · ')}
                </span>
              </div>
            )}

            {Object.entries(analysis.figure_groups || fallbackFigureGroups).map(([group, keys]) => {
              const visibleKeys = keys.filter((key) => !analysis.figures?.[key]?.skipped);
              if (!visibleKeys.length) return null;
              return (
                <section className="analysisFigureSection" key={group}>
                  <h3>{groupLabels[group] || group}</h3>
                  <div className="analysisFigureGrid">
                    {visibleKeys.map((key) => {
                      const label = figureLabel(key, analysis);
                      const description = analysis.figure_descriptions?.[key] || analysis.figures?.[key]?.description;
                      return (
                        <figure key={key}>
                          <figcaption>
                            <span>{label}</span>
                            <div className="analysisPlotDownload">
                              <select
                                aria-label={`Pixel width for ${label}`}
                                onChange={(event) => setPlotSizes((current) => ({ ...current, [key]: event.target.value }))}
                                value={plotSizes[key] || plotDownloadSizes[1].value}
                              >
                                {plotDownloadSizes.map((size) => (
                                  <option key={size.value} value={size.value}>{size.label}</option>
                                ))}
                              </select>
                              <a
                                href={analysisPlotPngUrl(selectedReport.run_id, key, plotSizes[key] || plotDownloadSizes[1].value)}
                              >
                                Download
                              </a>
                            </div>
                          </figcaption>
                          {description && <p>{description}</p>}
                          <a href={analysisArtifactUrl(selectedReport.run_id, key)} target="_blank" rel="noreferrer">
                            <img alt={label} src={analysisArtifactUrl(selectedReport.run_id, key)} />
                          </a>
                        </figure>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </>
          )}

          {!analysis && (
          <p className="analysisEmpty">This report is eligible. Generate analysis to create CSV tables, SVG plots, a Markdown summary, and a ZIP bundle.</p>
          )}
        </div>
      )}
    </section>
  );
}

export default ComputationalAnalysisWorkspace;
