import { useCallback, useEffect, useMemo, useState } from 'react';

import { backendApiUrl } from '../../config/api';
import {
  cancelRedTeamRun as cancelRunRequest,
  createRedTeamRun,
  fetchPromptSettings,
  fetchRedTeamReviewItems,
  fetchRedTeamRun,
  finalizeRedTeamRun as finalizeRunRequest,
  startRedTeamService,
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
  const [redTeamTargetMode, setRedTeamTargetMode] = useState('guardrailed');
  const [redTeamPromptSettings, setRedTeamPromptSettings] = useState([]);
  const [redTeamPromptSettingsStatus, setRedTeamPromptSettingsStatus] = useState('idle');
  const [selectedPromptId, setSelectedPromptId] = useState(null);
  const [redTeamSettingsOpen, setRedTeamSettingsOpen] = useState(false);

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
    const totalCases = methodsToRun.length * 10;
    const expectedAnswerOverrides = Object.fromEntries(
      promptSettingsForRun
        .filter((prompt) => methodsToRun.includes(prompt.method))
        .filter((prompt) => prompt.expected_answer.trim() !== prompt.original_expected_answer.trim())
        .map((prompt) => [prompt.prompt_id, prompt.expected_answer.trim()])
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
        expected_answer_overrides: expectedAnswerOverrides,
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
    await submitRedTeamReview({ runId, caseId, review: boundedReview });
  }, [redTeamRun?.run_id]);

  async function finalizeRedTeamRun() {
    if (!redTeamRun?.run_id) {
      return;
    }
    await finalizeRunRequest(redTeamRun.run_id);
    await loadRedTeamRun(redTeamRun.run_id);
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

  function resetPromptExpectedAnswer(promptId) {
    setRedTeamPromptSettings((current) => current.map((prompt) => (
      prompt.prompt_id === promptId
        ? { ...prompt, expected_answer: prompt.original_expected_answer }
        : prompt
    )));
  }

  function resetRedTeamRun() {
    setRedTeamRun(null);
    setRedTeamReviewItems([]);
    setRedTeamError(null);
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
    loadRedTeamPromptSettings,
    loadRedTeamRun,
    redTeamError,
    redTeamPromptSettingsStatus,
    redTeamReviewItems,
    redTeamRun,
    redTeamSettingsOpen,
    redTeamTargetMode,
    refreshRedTeamRun,
    resetPromptExpectedAnswer,
    resetRedTeamRun,
    selectedRedTeamMethods,
    setRedTeamSettingsOpen,
    setRedTeamTargetMode,
    setSelectedPromptId,
    startRedTeamRun,
    submitHumanReview,
    toggleRedTeamMethod,
    updatePromptExpectedAnswer,
  };
}
