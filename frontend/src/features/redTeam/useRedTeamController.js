// Red-team workflow controller hook.
//
// The hook starts the standalone red-team service, creates/cancels/finalizes
// runs, polls progress, loads review items, and stores optional human score
// overrides used by the answer-review panel.

import { useCallback, useEffect, useMemo, useState } from 'react';

import { backendApiUrl } from '../../config/api';
import {
  cancelRedTeamRun as cancelRunRequest,
  createRedTeamRun,
  fetchFinalReportDataset,
  fetchFinalReports,
  fetchPromptSettings,
  fetchRedTeamReviewItems,
  fetchRedTeamRun,
  fetchRedTeamAnalysis,
  finalizeRedTeamRun as finalizeRunRequest,
  generateAnalysisFromFinalReport,
  resetFinalReportReview,
  resetRedTeamReview,
  startRedTeamService,
  submitFinalReportReview,
  submitRedTeamReview,
} from './redTeamApi';
import {
  normalizePromptSettings,
  recomputeRedTeamScores,
  redTeamMethods,
} from './redTeamUtils';


export function useRedTeamController() {
  const [redTeamRun, setRedTeamRun] = useState(null);
  const [redTeamReviewItems, setRedTeamReviewItems] = useState([]);
  const [redTeamError, setRedTeamError] = useState(null);
  const [selectedRedTeamMethods, setSelectedRedTeamMethods] = useState(redTeamMethods.map(([method]) => method));
  const [redTeamTargetMode, setRedTeamTargetMode] = useState('full_analysis_stack');
  const [selectedRedTeamProfileIds, setSelectedRedTeamProfileIds] = useState([]);
  const [redTeamPromptSettings, setRedTeamPromptSettings] = useState([]);
  const [redTeamPromptSettingsStatus, setRedTeamPromptSettingsStatus] = useState('idle');
  const [selectedPromptId, setSelectedPromptId] = useState(null);
  const [redTeamSettingsOpen, setRedTeamSettingsOpen] = useState(false);
  const [redTeamAnalysis, setRedTeamAnalysis] = useState(null);
  const [redTeamAnalysisStatus, setRedTeamAnalysisStatus] = useState('idle');
  const [savedRedTeamReports, setSavedRedTeamReports] = useState([]);
  const [savedRedTeamReportsStatus, setSavedRedTeamReportsStatus] = useState('idle');

  const loadRedTeamRun = useCallback(async (runId) => {
    if (!runId) {
      return;
    }
    const runPayload = await fetchRedTeamRun(runId);
    setRedTeamRun(runPayload);

    if (['completed', 'cancelled', 'error'].includes(runPayload.status)) {
      const reviewPayload = await fetchRedTeamReviewItems(runId);
      if (reviewPayload) {
        setRedTeamReviewItems(reviewPayload.cases || []);
      }
      const analysisPayload = await fetchRedTeamAnalysis(runId);
      if (analysisPayload) {
        setRedTeamAnalysis(analysisPayload);
        setRedTeamAnalysisStatus('ready');
      }
    }
  }, []);

  const loadSavedRedTeamReports = useCallback(async () => {
    try {
      setSavedRedTeamReportsStatus('loading');
      const payload = await fetchFinalReports();
      setSavedRedTeamReports(payload.reports || []);
      setSavedRedTeamReportsStatus('ready');
      return payload.reports || [];
    } catch (err) {
      setSavedRedTeamReportsStatus('error');
      setRedTeamError(err.message);
      return [];
    }
  }, []);

  useEffect(() => {
    loadSavedRedTeamReports();
  }, [loadSavedRedTeamReports]);

  const openSavedRedTeamReport = useCallback(async (runId) => {
    if (!runId) {
      return null;
    }
    try {
      setRedTeamError(null);
      setRedTeamAnalysis(null);
      setRedTeamAnalysisStatus('idle');
      const report = await fetchFinalReportDataset(runId);
      const cases = report.cases || [];
      const hydratedRun = {
        ...report,
        loaded_from_final_report: true,
        status: report.status || 'completed',
        progress: report.progress || {
          total_cases: cases.length,
          completed_cases: cases.length,
          current_step: 'loaded from saved final report',
        },
        final_scores: report.final_scores || {},
        final_report: {
          download_url: `/api/red-team/final-reports/${runId}/json`,
          json_download_url: `/api/red-team/final-reports/${runId}/json`,
          pdf_download_url: `/api/red-team/final-reports/${runId}/pdf`,
        },
      };
      setRedTeamRun(hydratedRun);
      setRedTeamReviewItems(cases);
      const analysisPayload = await fetchRedTeamAnalysis(runId);
      if (analysisPayload) {
        setRedTeamAnalysis(analysisPayload);
        setRedTeamAnalysisStatus('ready');
      }
      return hydratedRun;
    } catch (err) {
      setRedTeamError(err.message);
      return null;
    }
  }, []);

  const refreshRedTeamRun = useCallback(async () => {
    if (!redTeamRun?.run_id) {
      return;
    }
    try {
      await loadRedTeamRun(redTeamRun.run_id);
    } catch (err) {
      setRedTeamError(err.message);
    }
  }, [loadRedTeamRun, redTeamRun?.run_id]);

  useEffect(() => {
    const status = redTeamRun?.status;
    if (!redTeamRun?.run_id || !['created', 'running', 'cancelling'].includes(status)) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      loadRedTeamRun(redTeamRun.run_id).catch((err) => setRedTeamError(err.message));
    }, 1600);

    return () => window.clearInterval(intervalId);
  }, [loadRedTeamRun, redTeamRun?.run_id, redTeamRun?.status]);

  const loadRedTeamPromptSettings = useCallback(async () => {
    try {
      setRedTeamPromptSettingsStatus('loading');
      setRedTeamError(null);
      await startRedTeamService();
      const payload = await fetchPromptSettings();
      const prompts = normalizePromptSettings(payload.prompts || []);
      setRedTeamPromptSettings(prompts);
      setSelectedPromptId((current) => current || prompts[0]?.prompt_id || null);
      setRedTeamPromptSettingsStatus('ready');
      return prompts;
    } catch (err) {
      setRedTeamPromptSettingsStatus('error');
      setRedTeamError(err.message);
      return [];
    }
  }, []);

  async function startRedTeamRun() {
    if (selectedRedTeamMethods.length === 0) {
      setRedTeamError('Select at least one red-team method.');
      return;
    }

    const promptSettingsForRun = redTeamPromptSettingsStatus === 'ready'
      ? redTeamPromptSettings
      : await loadRedTeamPromptSettings();
    const methodsToRun = selectedRedTeamMethods;
    if (selectedRedTeamProfileIds.length === 0) {
      setRedTeamError('Select at least one profile.');
      return;
    }

    const targetModeCount = redTeamTargetMode === 'full_analysis_stack' ? 2 : 1;
    const totalCases = methodsToRun.length * 10 * selectedRedTeamProfileIds.length * targetModeCount;
    const expectedAnswerOverrides = Object.fromEntries(
      promptSettingsForRun
        .filter((prompt) => methodsToRun.includes(prompt.method))
        .filter((prompt) => prompt.expected_answer.trim() !== prompt.original_expected_answer.trim())
        .map((prompt) => [prompt.prompt_id, prompt.expected_answer.trim()])
    );
    const calibrationNoteOverrides = Object.fromEntries(
      promptSettingsForRun
        .filter((prompt) => methodsToRun.includes(prompt.method))
        .filter((prompt) => (prompt.calibration_note || '').trim() !== (prompt.original_calibration_note || '').trim())
        .map((prompt) => [prompt.prompt_id, (prompt.calibration_note || '').trim()])
    );

    setRedTeamError(null);
    setRedTeamReviewItems([]);
    setRedTeamRun({
      status: 'starting',
      final_scores: {},
      progress: {
        total_cases: totalCases,
        completed_cases: 0,
        current_step: 'starting standalone red-team service',
      },
    });

    try {
      await startRedTeamService();
      const payload = await createRedTeamRun({
        backend_url: backendApiUrl,
        country: 'netherlands',
        selected_methods: methodsToRun,
        target_mode: redTeamTargetMode,
        profile_count: selectedRedTeamProfileIds.length,
        selected_profile_ids: selectedRedTeamProfileIds,
        expected_answer_overrides: expectedAnswerOverrides,
        calibration_note_overrides: calibrationNoteOverrides,
      });
      setRedTeamRun({
        ...payload,
        progress: {
          total_cases: totalCases,
          completed_cases: 0,
          current_step: 'queued in red-team service',
        },
      });
      await loadRedTeamRun(payload.run_id);
    } catch (err) {
      setRedTeamError(err.message);
      setRedTeamRun({
        status: 'error',
        final_scores: {},
        progress: { current_step: 'red-team service unavailable' },
      });
    }
  }

  async function cancelRedTeamRun() {
    if (!redTeamRun?.run_id) {
      return;
    }
    try {
      await cancelRunRequest(redTeamRun.run_id);
      await loadRedTeamRun(redTeamRun.run_id);
    } catch (err) {
      setRedTeamError(err.message);
    }
  }

  const submitHumanReview = useCallback(async (caseId, review) => {
    if (!redTeamRun?.run_id) {
      return;
    }
    const runId = redTeamRun.run_id;
    const boundedReview = {
      ...review,
      score: Math.max(0, Math.min(1, Number(review.score))),
    };
    const humanReview = {
      score: boundedReview.score,
      passed: boundedReview.score >= 0.5,
      notes: boundedReview.notes || '',
    };

    setRedTeamReviewItems((current) => current.map((item) => (
      item.case_id === caseId ? { ...item, human_review: humanReview } : item
    )));
    setRedTeamRun((current) => {
      if (!current?.cases) {
        return current;
      }
      const updatedCases = current.cases.map((item) => (
        item.case_id === caseId ? { ...item, human_review: humanReview } : item
      ));
      return {
        ...current,
        cases: updatedCases,
        final_scores: recomputeRedTeamScores(updatedCases),
      };
    });
    setRedTeamAnalysis(null);
    setRedTeamAnalysisStatus('idle');
    if (redTeamRun.loaded_from_final_report) {
      const payload = await submitFinalReportReview({ runId, caseId, review: boundedReview });
      setRedTeamRun((current) => current ? { ...current, final_scores: payload.final_scores || current.final_scores } : current);
      await loadSavedRedTeamReports();
      return;
    }
    const payload = await submitRedTeamReview({ runId, caseId, review: boundedReview });
    setRedTeamRun((current) => current ? { ...current, final_scores: payload.final_scores || current.final_scores } : current);
  }, [loadSavedRedTeamReports, redTeamRun?.loaded_from_final_report, redTeamRun?.run_id]);

  const resetHumanReview = useCallback(async (caseId) => {
    if (!redTeamRun?.run_id) {
      return;
    }
    const runId = redTeamRun.run_id;

    setRedTeamReviewItems((current) => current.map((item) => {
      if (item.case_id !== caseId) {
        return item;
      }
      const { human_review: _removedReview, ...rest } = item;
      return rest;
    }));
    setRedTeamRun((current) => {
      if (!current?.cases) {
        return current;
      }
      const updatedCases = current.cases.map((item) => {
        if (item.case_id !== caseId) {
          return item;
        }
        const { human_review: _removedReview, ...rest } = item;
        return rest;
      });
      return {
        ...current,
        cases: updatedCases,
        final_scores: recomputeRedTeamScores(updatedCases),
      };
    });
    setRedTeamAnalysis(null);
    setRedTeamAnalysisStatus('idle');

    if (redTeamRun.loaded_from_final_report) {
      const payload = await resetFinalReportReview({ runId, caseId });
      setRedTeamRun((current) => current ? { ...current, final_scores: payload.final_scores || current.final_scores } : current);
      await loadSavedRedTeamReports();
      return;
    }
    const payload = await resetRedTeamReview({ runId, caseId });
    setRedTeamRun((current) => current ? { ...current, final_scores: payload.final_scores || current.final_scores } : current);
  }, [loadSavedRedTeamReports, redTeamRun?.loaded_from_final_report, redTeamRun?.run_id]);

  async function finalizeRedTeamRun() {
    if (!redTeamRun?.run_id) {
      return;
    }
    await finalizeRunRequest(redTeamRun.run_id);
    await loadRedTeamRun(redTeamRun.run_id);
    await loadSavedRedTeamReports();
  }

  async function generateComputationalAnalysis() {
    if (!redTeamRun?.run_id) {
      return null;
    }
    setRedTeamAnalysisStatus('loading');
    try {
      try {
        await finalizeRunRequest(redTeamRun.run_id);
        await loadSavedRedTeamReports();
      } catch (finalizeError) {
        if (!redTeamRun.loaded_from_final_report) {
          throw finalizeError;
        }
      }
      const analysis = await generateAnalysisFromFinalReport(redTeamRun.run_id);
      setRedTeamAnalysis(analysis);
      setRedTeamAnalysisStatus('ready');
      if (!redTeamRun.loaded_from_final_report) {
        await loadRedTeamRun(redTeamRun.run_id);
      }
      return analysis;
    } catch (err) {
      setRedTeamAnalysisStatus('error');
      setRedTeamError(err.message);
      return null;
    }
  }

  function toggleRedTeamMethod(method) {
    setSelectedRedTeamMethods((current) => {
      if (current.includes(method)) {
        return current.filter((item) => item !== method);
      }
      return [...current, method];
    });
  }

  function updatePromptExpectedAnswer(promptId, value) {
    setRedTeamPromptSettings((current) => current.map((prompt) => (
      prompt.prompt_id === promptId ? { ...prompt, expected_answer: value } : prompt
    )));
  }

  function updatePromptCalibrationNote(promptId, value) {
    setRedTeamPromptSettings((current) => current.map((prompt) => (
      prompt.prompt_id === promptId ? { ...prompt, calibration_note: value } : prompt
    )));
  }

  function resetPromptExpectedAnswer(promptId) {
    setRedTeamPromptSettings((current) => current.map((prompt) => (
      prompt.prompt_id === promptId
        ? {
            ...prompt,
            calibration_note: prompt.original_calibration_note,
            expected_answer: prompt.original_expected_answer,
          }
        : prompt
    )));
  }

  function resetRedTeamRun() {
    setRedTeamRun(null);
    setRedTeamReviewItems([]);
    setRedTeamError(null);
    setRedTeamAnalysis(null);
    setRedTeamAnalysisStatus('idle');
  }

  const derived = useMemo(() => {
    const redTeamIsRunning = ['starting', 'created', 'running', 'cancelling'].includes(redTeamRun?.status);
    const redTeamScores = redTeamRun?.final_scores || {};
    const redTeamMethodScores = redTeamScores.method_scores || {};
    const redTeamStatus = String(redTeamRun?.status || '').replaceAll('_', ' ');
    const redTeamStatusTitle = redTeamIsRunning
      ? 'Red-team evaluation running'
      : `Red-team evaluation ${redTeamStatus || 'completed'}`;
    const visiblePromptSettings = redTeamPromptSettings.filter((prompt) => selectedRedTeamMethods.includes(prompt.method));
    const selectedPromptSetting = visiblePromptSettings.find((prompt) => prompt.prompt_id === selectedPromptId) || visiblePromptSettings[0] || null;
    const editedPromptCount = redTeamPromptSettings.filter((prompt) => (
      prompt.expected_answer.trim() !== prompt.original_expected_answer.trim()
      || (prompt.calibration_note || '').trim() !== (prompt.original_calibration_note || '').trim()
    )).length;

    return {
      editedPromptCount,
      redTeamMethodScores,
      redTeamScores,
      redTeamStatusTitle,
      selectedPromptSetting,
      visiblePromptSettings,
    };
  }, [redTeamPromptSettings, redTeamRun, selectedPromptId, selectedRedTeamMethods]);

  return {
    ...derived,
    cancelRedTeamRun,
    finalizeRedTeamRun,
    generateComputationalAnalysis,
    loadSavedRedTeamReports,
    loadRedTeamPromptSettings,
    loadRedTeamRun,
    openSavedRedTeamReport,
    redTeamError,
    redTeamAnalysis,
    redTeamAnalysisStatus,
    redTeamPromptSettingsStatus,
    redTeamReviewItems,
    redTeamRun,
    redTeamSettingsOpen,
    redTeamTargetMode,
    savedRedTeamReports,
    savedRedTeamReportsStatus,
    refreshRedTeamRun,
    resetPromptExpectedAnswer,
    resetRedTeamRun,
    resetHumanReview,
    selectedRedTeamProfileIds,
    selectedRedTeamMethods,
    setRedTeamSettingsOpen,
    setSelectedRedTeamProfileIds,
    setRedTeamTargetMode,
    setSelectedPromptId,
    startRedTeamRun,
    submitHumanReview,
    toggleRedTeamMethod,
    updatePromptCalibrationNote,
    updatePromptExpectedAnswer,
  };
}
