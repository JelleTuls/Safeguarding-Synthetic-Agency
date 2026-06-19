// Red-team answer review panel.
//
// This component renders paired lightweight/guardrailed answers for each prompt,
// the expected behavior/style/metrics, LLM reasoning, pairwise comparison notes,
// and optional human score overrides.

import { useEffect, useMemo, useRef, useState } from 'react';

import { analysisArtifactUrl, analysisZipUrl } from '../../features/redTeam/redTeamApi';
import './redTeamPanel.css';

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

function formatScore(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return '0%';
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function statusLabel(status) {
  return String(status || 'unknown').replaceAll('_', ' ');
}

function targetModeLabel(mode) {
  if (mode === 'lightweight_no_guardrails') return 'Lightweight baseline';
  if (mode === 'full_analysis_stack') return 'Full analysis stack';
  return 'Guardrailed';
}

function figureLabel(key, analysis) {
  return analysis?.figures?.[key]?.title || key.replaceAll('_', ' ');
}

function visibleFigureKeys(analysis) {
  return Object.values(analysis?.figure_groups || fallbackFigureGroups).flat();
}

function renderExpectedMetrics(metrics) {
  if (!metrics || typeof metrics !== 'object') {
    return null;
  }
  return (
    <div className="red-team-expected-answer">
      <strong>Expected SSA metrics</strong>
      <dl className="red-team-expected-metrics">
        {Object.entries(metrics).map(([key, value]) => (
          <div key={key}>
            <dt>{String(key).replaceAll('_', ' ')}</dt>
            <dd>{Array.isArray(value) ? value.join(', ') : String(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function renderJudgeResult(llmGrade) {
  if (!llmGrade) {
    return null;
  }
  if (!llmGrade.available) {
    return (
      <div className="red-team-llm-grade is-unavailable">
        <strong>LLM judge unavailable</strong>
        <p>{llmGrade.error || 'No LLM grading result was captured.'}</p>
      </div>
    );
  }
  return (
    <div className="red-team-llm-grade">
      <div className="red-team-llm-grade-header">
        <strong>LLM judge</strong>
        <span>{formatScore(llmGrade.score)}</span>
        <span>confidence {formatScore(llmGrade.confidence)}</span>
      </div>
      {llmGrade.score_reason && (
        <p>
          <b>Score reason:</b> {llmGrade.score_reason}
        </p>
      )}
      {llmGrade.rationale && <p>{llmGrade.rationale}</p>}
      {Array.isArray(llmGrade.indicators) && llmGrade.indicators.length > 0 && (
        <ul>
          {llmGrade.indicators.map((indicator, index) => (
            <li key={`${indicator.name || 'indicator'}-${index}`}>
              <b>{indicator.name || 'indicator'}:</b> {indicator.result || 'mixed'}
              {indicator.evidence ? ` - ${indicator.evidence}` : ''}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function AnswerScoreControl({ item, onResetReview, onSubmitReview }) {
  const existing = item.human_review || {};
  const automatedScore = item.automated_score ?? 0.5;
  const displayedScore = existing.score ?? automatedScore;
  const [score, setScore] = useState(displayedScore);
  const [saveState, setSaveState] = useState('idle');
  const didMount = useRef(false);
  const skipNextSave = useRef(false);
  const numericScore = Number(score);
  const derivedResult = numericScore >= 0.5 ? 'Pass' : 'Fail';
  const hasHumanOverride = Boolean(item.human_review);
  const hasLocalChange = Math.abs(Number(score) - Number(automatedScore)) > 0.00001;

  function updateScore(value) {
    const numericValue = Number(value);
    if (Number.isNaN(numericValue)) {
      setScore(0);
      return;
    }
    setScore(Math.max(0, Math.min(1, numericValue)));
  }

  async function resetScore() {
    skipNextSave.current = hasLocalChange;
    setScore(automatedScore);
    if (!hasHumanOverride) {
      setSaveState('reset');
      return;
    }
    setSaveState('saving');
    try {
      await onResetReview(item.case_id);
      setSaveState('reset');
    } catch {
      setSaveState('error');
    }
  }

  useEffect(() => {
    setScore((current) => {
      if (Math.abs(Number(current) - Number(displayedScore)) <= 0.00001) {
        return current;
      }
      skipNextSave.current = true;
      return displayedScore;
    });
  }, [displayedScore, item.case_id]);

  useEffect(() => {
    if (!didMount.current) {
      didMount.current = true;
      skipNextSave.current = false;
      return undefined;
    }
    if (skipNextSave.current) {
      skipNextSave.current = false;
      return undefined;
    }

    const timeoutId = window.setTimeout(async () => {
      setSaveState('saving');
      try {
        await onSubmitReview(item.case_id, {
          score: Math.max(0, Math.min(1, Number(score))),
          notes: '',
        });
        setSaveState('saved');
      } catch {
        setSaveState('error');
      }
    }, 350);

    return () => window.clearTimeout(timeoutId);
  }, [item.case_id, onSubmitReview, score]);

  return (
    <div className="red-team-answer-score">
      <input
        aria-label={`${targetModeLabel(item.target_mode)} score`}
        max="1"
        min="0"
        step="0.05"
        type="number"
        value={score}
        onChange={(event) => updateScore(event.target.value)}
      />
      <span className={`red-team-derived-result ${derivedResult === 'Pass' ? 'is-pass' : 'is-fail'}`}>
        {derivedResult}
      </span>
      <span className={`red-team-autosave-state is-${saveState}`}>
        {saveState === 'saving' && 'Saving'}
        {saveState === 'saved' && 'Saved'}
        {saveState === 'error' && 'Save failed'}
        {saveState === 'reset' && 'Reset'}
        {saveState === 'idle' && 'Auto-save'}
      </span>
      <button
        className="red-team-score-reset"
        disabled={!hasHumanOverride && !hasLocalChange}
        title="Reset to the original automated score"
        type="button"
        onClick={resetScore}
      >
        Reset
      </button>
    </div>
  );
}

function AnswerBlock({ detailsOpen, item, onDetailsOpenChange, onResetReview, onSubmitReview }) {
  const blockRef = useRef(null);

  useEffect(() => {
    if (detailsOpen) {
      window.requestAnimationFrame(() => {
        blockRef.current?.scrollIntoView({ block: 'nearest' });
      });
    }
  }, [detailsOpen]);

  if (!item) {
    return (
      <section className="red-team-answer-block is-missing">
        <h5>Missing answer</h5>
        <p>No result was captured for this target mode.</p>
      </section>
    );
  }

  return (
    <section
      className={`red-team-answer-block is-${item.target_mode === 'lightweight_no_guardrails' ? 'lightweight' : 'guardrailed'}`}
      ref={blockRef}
    >
      <div className="red-team-answer-heading">
        <div>
          <h5>{targetModeLabel(item.target_mode)}</h5>
          <span>Auto {item.automated_score === null || item.automated_score === undefined ? 'N/A' : formatScore(item.automated_score)}</span>
        </div>
        <AnswerScoreControl item={item} onResetReview={onResetReview} onSubmitReview={onSubmitReview} />
      </div>

      <p className="red-team-response">{item.response_text || 'No response text captured.'}</p>

      <details className="red-team-answer-details" open={detailsOpen}>
        <summary
          onClick={(event) => {
            event.preventDefault();
            onDetailsOpenChange(detailsOpen ? null : item.case_id);
          }}
        >
          <span>Inspect reasoning</span>
          <b>{item.llm_score !== undefined && item.llm_score !== null ? `LLM ${formatScore(item.llm_score)}` : 'No LLM score'}</b>
        </summary>
        {(item.llm_score !== undefined || item.score_source) && (
          <div className="red-team-score-breakdown">
            {item.llm_score !== undefined && item.llm_score !== null && <span>LLM {formatScore(item.llm_score)}</span>}
            {item.score_source && <span>{String(item.score_source).replaceAll('_', ' ')}</span>}
          </div>
        )}
        {renderJudgeResult(item.llm_grade)}
        {item.comparison_grade?.available && (
          <div className="red-team-llm-grade">
            <div className="red-team-llm-grade-header">
              <strong>Pairwise comparison</strong>
              {item.comparison_score !== undefined && item.comparison_score !== null && (
                <span>{formatScore(item.comparison_score)}</span>
              )}
              <span>{String(item.comparison_grade.preferred_mode || 'tie').replaceAll('_', ' ')}</span>
            </div>
            {item.comparison_grade.selected_mode_result?.reason && (
              <p>{item.comparison_grade.selected_mode_result.reason}</p>
            )}
            {item.comparison_grade.selected_mode_result?.metrics && (
              <div className="red-team-score-breakdown">
                {Object.entries(item.comparison_grade.selected_mode_result.metrics).map(([key, value]) => (
                  <span key={key}>
                    {String(key).replaceAll('_', ' ')} {formatScore(value)}
                  </span>
                ))}
              </div>
            )}
            {item.comparison_grade.comparison_reason && <p>{item.comparison_grade.comparison_reason}</p>}
          </div>
        )}
        {Array.isArray(item.automated_reasons) && item.automated_reasons.length > 0 && (
          <ul className="red-team-reasons">
            {item.automated_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}
        <div className="red-team-case-meta">
          <span>{item.profile_label}</span>
          <span>{targetModeLabel(item.target_mode)}</span>
          <span>{item.attack_family}</span>
          <span>{item.interaction_mode}</span>
          <span>{item.target_guardrail}</span>
        </div>
      </details>
    </section>
  );
}

function ReviewQuestion({ item, isOpen, onOpenChange, onResetReview, onSubmitReview }) {
  const lightweight = item.answers.lightweight_no_guardrails;
  const guardrailed = item.answers.guardrailed;
  const lightweightScore = lightweight?.human_review?.score ?? lightweight?.automated_score;
  const guardrailedScore = guardrailed?.human_review?.score ?? guardrailed?.automated_score;
  const [showExpectedContext, setShowExpectedContext] = useState(false);
  const [openAnswerDetailId, setOpenAnswerDetailId] = useState(null);
  const summaryRef = useRef(null);
  const hasExpectedContext = Boolean(
    item.expected_answer
      || item.expected_response_style
      || (item.expected_metrics && Object.keys(item.expected_metrics).length > 0)
  );

  function collapseItem() {
    onOpenChange(null);
    window.requestAnimationFrame(() => {
      summaryRef.current?.scrollIntoView({ block: 'nearest' });
    });
  }

  function toggleExpectedContext() {
    setShowExpectedContext((current) => {
      const next = !current;
      if (next) {
        setOpenAnswerDetailId(null);
      }
      return next;
    });
  }

  function updateOpenAnswerDetail(caseId) {
    setOpenAnswerDetailId(caseId);
    if (caseId) {
      setShowExpectedContext(false);
    }
  }

  useEffect(() => {
    if (isOpen) {
      window.requestAnimationFrame(() => {
        summaryRef.current?.scrollIntoView({ block: 'nearest' });
      });
    } else {
      setOpenAnswerDetailId(null);
      setShowExpectedContext(false);
    }
  }, [isOpen]);

  return (
    <details
      className="red-team-review-case"
      open={isOpen}
    >
      <summary
        className="red-team-case-summary"
        ref={summaryRef}
        onClick={(event) => {
          event.preventDefault();
          onOpenChange(isOpen ? null : item.pair_id);
        }}
      >
        <span className="red-team-score-pair-mini">
          <b>L {lightweightScore === null || lightweightScore === undefined ? 'N/A' : formatScore(lightweightScore)}</b>
          <b>G {guardrailedScore === null || guardrailedScore === undefined ? 'N/A' : formatScore(guardrailedScore)}</b>
        </span>
        <span className="red-team-summary-copy">
          <strong>{item.prompt_id}</strong>
          <p>{item.message}</p>
        </span>
        <span className="red-team-foldout-cue" aria-hidden="true" />
      </summary>

      <div className="red-team-case-body">
        <div className="red-team-question-row">
          <p className="red-team-prompt">{item.message}</p>
          {hasExpectedContext && (
            <button
              aria-label={showExpectedContext ? 'Hide expected evaluation context' : 'Show expected evaluation context'}
              aria-pressed={showExpectedContext}
              className={`red-team-expected-toggle ${showExpectedContext ? 'is-active' : ''}`}
              title={showExpectedContext ? 'Hide expected evaluation context' : 'Show expected evaluation context'}
              type="button"
              onClick={toggleExpectedContext}
            >
              i
            </button>
          )}
        </div>
        {showExpectedContext && (
          <div className="red-team-expected-context">
            {item.expected_answer && (
              <div className="red-team-expected-answer">
                <strong>Expected answer behavior</strong>
                <p>{item.expected_answer}</p>
              </div>
            )}
            {item.expected_response_style && (
              <div className="red-team-expected-answer">
                <strong>Expected answer style</strong>
                <p>{item.expected_response_style}</p>
              </div>
            )}
            {renderExpectedMetrics(item.expected_metrics)}
          </div>
        )}
        <div className="red-team-answer-pair">
          <AnswerBlock
            detailsOpen={openAnswerDetailId === lightweight?.case_id}
            item={lightweight}
            onDetailsOpenChange={updateOpenAnswerDetail}
            onResetReview={onResetReview}
            onSubmitReview={onSubmitReview}
          />
          <AnswerBlock
            detailsOpen={openAnswerDetailId === guardrailed?.case_id}
            item={guardrailed}
            onDetailsOpenChange={updateOpenAnswerDetail}
            onResetReview={onResetReview}
            onSubmitReview={onSubmitReview}
          />
        </div>
        <button className="red-team-collapse-bar" type="button" aria-label="Fold item back up" onClick={collapseItem}>
          <span className="red-team-collapse-cue" aria-hidden="true" />
        </button>
      </div>
    </details>
  );
}

function ComputationalAnalysisView({ analysis, analysisStatus, onGenerateAnalysis, runId }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const canDownload = Boolean(runId && analysis?.artifacts);
  const figureKeys = Array.from(new Set(visibleFigureKeys(analysis)));

  async function handleGenerate() {
    setIsGenerating(true);
    try {
      await onGenerateAnalysis?.();
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="red-team-analysis-view">
      <div className="red-team-analysis-hero">
        <div>
          <h3>Computational analysis</h3>
          <p>Generate reproducible CSV tables, thesis-ready SVG plots, a Markdown summary, and a downloadable artifact bundle from this red-team run.</p>
        </div>
        <button type="button" disabled={isGenerating || analysisStatus === 'loading'} onClick={handleGenerate}>
          {isGenerating || analysisStatus === 'loading' ? 'Generating' : analysis ? 'Regenerate analysis' : 'Generate analysis'}
        </button>
      </div>

      {analysis && (
        <>
          <div className="red-team-analysis-stats">
            <div>
              <span>Total cases</span>
              <strong>{analysis.case_count ?? 'N/A'}</strong>
            </div>
            <div>
              <span>Paired cases</span>
              <strong>{analysis.paired_case_count ?? 'N/A'}</strong>
            </div>
            <div>
              <span>EB pairs</span>
              <strong>{analysis.eb_pair_count ?? 'N/A'}</strong>
            </div>
            <div>
              <span>Mean delta</span>
              <strong>{analysis.overall_mean_delta === null || analysis.overall_mean_delta === undefined ? 'N/A' : `${analysis.overall_mean_delta >= 0 ? '+' : ''}${Math.round(analysis.overall_mean_delta * 100)}%`}</strong>
            </div>
          </div>

          <div className="red-team-analysis-downloads">
            <a className={!canDownload ? 'isDisabled' : ''} href={canDownload ? analysisZipUrl(runId) : undefined}>
              Download all artifacts
            </a>
          </div>

          <div className="red-team-analysis-grid">
            {figureKeys.map((key) => {
              const figure = analysis?.figures?.[key] || {};
              if (figure.skipped) {
                return null;
              }
              const label = figureLabel(key, analysis);
              return (
              <figure className="red-team-analysis-figure" key={key}>
                <figcaption>{label}</figcaption>
                {canDownload ? (
                  <a href={analysisArtifactUrl(runId, key)} target="_blank" rel="noreferrer">
                    <img alt={label} src={analysisArtifactUrl(runId, key)} />
                  </a>
                ) : (
                  <div className="red-team-analysis-placeholder">Generate analysis to preview this plot.</div>
                )}
              </figure>
              );
            })}
          </div>
        </>
      )}

      {!analysis && analysisStatus !== 'loading' && (
        <p className="red-team-empty">No computational analysis has been generated for this run yet.</p>
      )}
    </div>
  );
}

function RedTeamPanel({
  embedded = false,
  run,
  reviewItems,
  selectedProfileId = 'all',
  error,
  analysis,
  analysisStatus = 'idle',
  onCancel,
  onClose,
  onGenerateAnalysis,
  onRefresh,
  onResetReview,
  onSubmitReview,
}) {
  const [activeResultsTab, setActiveResultsTab] = useState('review');
  const [openReviewPairId, setOpenReviewPairId] = useState(null);
  const status = run?.status || 'starting';
  const isRunning = ['starting', 'created', 'running', 'cancelling'].includes(status);
  const progress = run?.progress || {};
  const completed = progress.completed_cases || 0;
  const total = progress.total_cases || 60;
  const comparisonTotal = progress.comparison_pairs_total || 0;
  const comparisonCompleted = progress.comparison_pairs_completed || 0;
  const isComparingPairs = comparisonTotal > 0 && completed >= total;
  const displayCompleted = isComparingPairs ? comparisonCompleted : completed;
  const displayTotal = isComparingPairs ? comparisonTotal : total;
  const progressRatio = displayTotal ? Math.min(1, displayCompleted / displayTotal) : 0;
  const reviewCount = reviewItems?.length || 0;

  const sortedReviewItems = useMemo(() => {
    return [...(reviewItems || [])].sort((left, right) => {
      if ((left.profile_label || '') !== (right.profile_label || '')) {
        return String(left.profile_label || '').localeCompare(String(right.profile_label || ''));
      }
      if (left.method === right.method) {
        return String(left.prompt_id).localeCompare(String(right.prompt_id));
      }
      return String(left.method).localeCompare(String(right.method));
    });
  }, [reviewItems]);

  const visibleReviewItems = useMemo(() => {
    if (selectedProfileId === 'all') return sortedReviewItems;
    return sortedReviewItems.filter((item) => item.profile_id === selectedProfileId);
  }, [selectedProfileId, sortedReviewItems]);

  const groupedReviewItems = useMemo(() => {
    const pairedItems = Object.values(visibleReviewItems.reduce((pairs, item) => {
      const pairKey = `${item.profile_id || 'profile'}::${item.prompt_id}`;
      if (!pairs[pairKey]) {
        pairs[pairKey] = {
          pair_id: pairKey,
          method: item.method || 'Other',
          methodName: item.method_name || item.method || 'Other',
          prompt_id: item.prompt_id,
          message: item.message,
          expected_answer: item.expected_answer,
          expected_response_style: item.expected_response_style,
          expected_metrics: item.expected_metrics,
          profile_label: item.profile_label,
          answers: {},
        };
      }
      pairs[pairKey].answers[item.target_mode || 'guardrailed'] = item;
      return pairs;
    }, {}));

    return pairedItems.reduce((groups, item) => {
      const key = item.method || 'Other';
      if (!groups[key]) {
        groups[key] = {
          method: key,
          methodName: item.method_name || key,
          items: [],
        };
      }
      groups[key].items.push(item);
      return groups;
    }, {});
  }, [visibleReviewItems]);
  const visibleQuestionCount = useMemo(() => (
    Object.values(groupedReviewItems).reduce((sum, group) => sum + group.items.length, 0)
  ), [groupedReviewItems]);

  useEffect(() => {
    setOpenReviewPairId(null);
  }, [run?.run_id, selectedProfileId]);

  if (isRunning) {
    return (
      <div className={embedded ? 'red-team-embedded' : 'red-team-overlay'} role={embedded ? 'status' : 'dialog'} aria-modal={embedded ? undefined : 'true'}>
        <section className="red-team-progress-card">
          <div className="red-team-progress-topline">
            <span>{statusLabel(status)}</span>
            <strong>{displayCompleted}/{displayTotal}</strong>
          </div>
          <h2>Red-teaming in progress</h2>
          <p>{progress.current_step || 'Preparing run...'}</p>
          {isComparingPairs && (
            <p className="red-team-progress-substep">
              Answer generation complete: {completed}/{total}. Pairwise evaluator comparisons are now running.
            </p>
          )}
          <div className="red-team-progress-bar" aria-label="Red-team progress">
            <span style={{ width: `${progressRatio * 100}%` }} />
          </div>
          {progress.current_method_name && (
            <div className="red-team-current-step">
              {progress.current_profile_label && (
                <b>
                  {progress.current_profile_label}
                  {progress.current_profile_index && progress.total_profiles
                    ? ` · profile ${progress.current_profile_index}/${progress.total_profiles}`
                    : ''}
                </b>
              )}
              {progress.current_target_mode && <span>{targetModeLabel(progress.current_target_mode)}</span>}
              <b>{progress.current_method_name}</b>
              <span>{progress.current_prompt_id}</span>
              <p>{progress.current_message}</p>
            </div>
          )}
          {error && <p className="red-team-error">{error}</p>}
          <div className="red-team-progress-actions">
            <button type="button" onClick={onRefresh}>Refresh</button>
            <button type="button" className="red-team-cancel" onClick={onCancel}>
              Cancel run
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className={embedded ? 'red-team-embedded' : 'red-team-overlay'} role={embedded ? undefined : 'dialog'} aria-modal={embedded ? undefined : 'true'}>
      <section className="red-team-results-panel">
        {!embedded && (
          <header className="red-team-results-header">
            <div>
              <span>Red-team evaluation</span>
              <h2>{statusLabel(status)}</h2>
            </div>
            <button type="button" onClick={onClose} aria-label="Close red-team results">x</button>
          </header>
        )}

        {error && <p className="red-team-error">{error}</p>}

        <main className="red-team-review-main">
          <div className="red-team-review-header">
            <div>
              <div className="red-team-results-tabs" aria-label="Red-team result views">
                <button
                  className={activeResultsTab === 'review' ? 'isActive' : ''}
                  type="button"
                  onClick={() => setActiveResultsTab('review')}
                >
                  Answer review
                </button>
                <button
                  className={activeResultsTab === 'analysis' ? 'isActive' : ''}
                  type="button"
                  onClick={() => setActiveResultsTab('analysis')}
                >
                  Computational analysis
                </button>
              </div>
              {activeResultsTab === 'review' ? (
                <span>{visibleQuestionCount} questions · {visibleReviewItems.length}/{reviewCount} answers shown</span>
              ) : (
                <span>{analysis?.generated_at ? `Generated ${analysis.generated_at}` : 'Reproducible tables and plots'}</span>
              )}
            </div>
            <button type="button" onClick={onRefresh}>Refresh</button>
          </div>

          {activeResultsTab === 'analysis' ? (
            <ComputationalAnalysisView
              analysis={analysis}
              analysisStatus={analysisStatus}
              runId={run?.run_id}
              onGenerateAnalysis={onGenerateAnalysis}
            />
          ) : reviewCount === 0 ? (
            <p className="red-team-empty">No cases are available for this run yet.</p>
          ) : (
            <div className="red-team-review-list">
              {Object.values(groupedReviewItems).map((group) => (
                <section className="red-team-layer-group" key={group.method}>
                  <h4>{group.methodName}</h4>
                  {group.items.map((item) => (
                    <ReviewQuestion
                      isOpen={openReviewPairId === item.pair_id}
                      key={item.pair_id}
                      item={item}
                      onOpenChange={setOpenReviewPairId}
                      onResetReview={onResetReview}
                      onSubmitReview={onSubmitReview}
                    />
                  ))}
                </section>
              ))}
            </div>
          )}
        </main>
      </section>
    </div>
  );
}

export default RedTeamPanel;
