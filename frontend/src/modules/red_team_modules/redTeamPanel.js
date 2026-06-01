import { useEffect, useMemo, useRef, useState } from 'react';

import './redTeamPanel.css';

function formatScore(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return '0%';
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function statusLabel(status) {
  return String(status || 'unknown').replaceAll('_', ' ');
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

function ReviewCase({ item, onSubmitReview }) {
  const existing = item.human_review || {};
  const [score, setScore] = useState(existing.score ?? item.automated_score ?? 0.5);
  const [notes, setNotes] = useState(existing.notes ?? '');
  const [saveState, setSaveState] = useState('idle');
  const didMount = useRef(false);
  const numericScore = Number(score);
  const derivedResult = numericScore >= 0.5 ? 'Pass' : 'Fail';

  function updateScore(value) {
    const numericValue = Number(value);
    if (Number.isNaN(numericValue)) {
      setScore(0);
      return;
    }
    setScore(Math.max(0, Math.min(1, numericValue)));
  }

  useEffect(() => {
    if (!didMount.current) {
      didMount.current = true;
      return undefined;
    }

    const timeoutId = window.setTimeout(async () => {
      setSaveState('saving');
      try {
        await onSubmitReview(item.case_id, {
          score: Math.max(0, Math.min(1, Number(score))),
          notes,
        });
        setSaveState('saved');
      } catch {
        setSaveState('error');
      }
    }, 350);

    return () => window.clearTimeout(timeoutId);
  }, [item.case_id, notes, onSubmitReview, score]);

  return (
    <details className="red-team-review-case">
      <summary className="red-team-case-summary">
        <span className={`red-team-live-score ${derivedResult === 'Pass' ? 'is-pass' : 'is-fail'}`}>
          {formatScore(numericScore)}
        </span>
        <span className="red-team-summary-copy">
          <strong>{item.prompt_id}</strong>
          <p>{item.message}</p>
        </span>
        <span className="red-team-foldout-cue" aria-hidden="true" />
      </summary>

      <div className="red-team-case-body">
        <div className="red-team-case-heading">
          <div>
            <strong>{item.prompt_id}</strong>
          </div>
          <b>auto {formatScore(item.automated_score)}</b>
        </div>

        {(item.rule_score !== undefined || item.llm_score !== undefined) && (
          <div className="red-team-score-breakdown">
            {item.rule_score !== undefined && <span>rule {formatScore(item.rule_score)}</span>}
            {item.llm_score !== undefined && item.llm_score !== null && <span>LLM {formatScore(item.llm_score)}</span>}
            {item.score_source && <span>{String(item.score_source).replaceAll('_', ' ')}</span>}
          </div>
        )}

        <p className="red-team-prompt">{item.message}</p>
        {item.expected_answer && (
          <div className="red-team-expected-answer">
            <strong>Expected answer behavior</strong>
            <p>{item.expected_answer}</p>
          </div>
        )}
        <p className="red-team-response">{item.response_text || 'No response text captured.'}</p>

        {renderJudgeResult(item.llm_grade)}

        <div className="red-team-case-meta">
          <span>{item.attack_family}</span>
          <span>{item.interaction_mode}</span>
          <span>{item.target_guardrail}</span>
        </div>

        {Array.isArray(item.automated_reasons) && item.automated_reasons.length > 0 && (
          <ul className="red-team-reasons">
            {item.automated_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}

        <div className="red-team-review-form">
          <label>
            Score
            <input
              max="1"
              min="0"
              step="0.05"
              type="number"
              value={score}
              onChange={(event) => updateScore(event.target.value)}
            />
          </label>
          <div className={`red-team-derived-result ${derivedResult === 'Pass' ? 'is-pass' : 'is-fail'}`}>
            <span>Derived result</span>
            <strong>{derivedResult}</strong>
          </div>
          <label className="red-team-notes">
            Notes
            <textarea value={notes} onChange={(event) => setNotes(event.target.value)} />
          </label>
          <div className={`red-team-autosave-state is-${saveState}`}>
            {saveState === 'saving' && 'Saving'}
            {saveState === 'saved' && 'Saved'}
            {saveState === 'error' && 'Save failed'}
            {saveState === 'idle' && 'Auto-save'}
          </div>
        </div>
        <button
          aria-label="Collapse review case"
          className="red-team-collapse-bar"
          type="button"
          onClick={(event) => {
            const reviewCase = event.currentTarget.closest('details');
            if (reviewCase) {
              reviewCase.open = false;
              reviewCase.scrollIntoView({ block: 'nearest' });
            }
          }}
        >
          <span aria-hidden="true" />
        </button>
      </div>
    </details>
  );
}

function RedTeamPanel({
  embedded = false,
  run,
  reviewItems,
  error,
  onCancel,
  onClose,
  onRefresh,
  onSaveFinalResults,
  onSubmitReview,
}) {
  const [finalizeError, setFinalizeError] = useState(null);
  const [finalizing, setFinalizing] = useState(false);
  const status = run?.status || 'starting';
  const isRunning = ['starting', 'created', 'running', 'cancelling'].includes(status);
  const progress = run?.progress || {};
  const scores = run?.final_scores || {};
  const methodScores = scores.method_scores || {};
  const completed = progress.completed_cases || 0;
  const total = progress.total_cases || 60;
  const progressRatio = total ? Math.min(1, completed / total) : 0;
  const reviewCount = reviewItems?.length || 0;
  const finalReport = run?.final_report || null;
  const canFinalize = !isRunning && (scores.pending_human_reviews ?? 0) === 0 && status === 'completed';

  const sortedReviewItems = useMemo(() => {
    return [...(reviewItems || [])].sort((left, right) => {
      if (left.method === right.method) {
        return String(left.prompt_id).localeCompare(String(right.prompt_id));
      }
      return String(left.method).localeCompare(String(right.method));
    });
  }, [reviewItems]);

  const groupedReviewItems = useMemo(() => {
    return sortedReviewItems.reduce((groups, item) => {
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
  }, [sortedReviewItems]);

  if (isRunning) {
    return (
      <div className={embedded ? 'red-team-embedded' : 'red-team-overlay'} role={embedded ? 'status' : 'dialog'} aria-modal={embedded ? undefined : 'true'}>
        <section className="red-team-progress-card">
          <div className="red-team-progress-topline">
            <span>{statusLabel(status)}</span>
            <strong>{completed}/{total}</strong>
          </div>
          <h2>Red-teaming in progress</h2>
          <p>{progress.current_step || 'Preparing run...'}</p>
          <div className="red-team-progress-bar" aria-label="Red-team progress">
            <span style={{ width: `${progressRatio * 100}%` }} />
          </div>
          {progress.current_method_name && (
            <div className="red-team-current-step">
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
        {finalizeError && <p className="red-team-error">{finalizeError}</p>}

        {!embedded && (
          <div className="red-team-summary-grid">
            <div>
              <span>Overall score</span>
              <strong>{formatScore(scores.overall_score)}</strong>
            </div>
            <div>
              <span>Pending human review</span>
              <strong>{scores.pending_human_reviews ?? 0}</strong>
            </div>
            <div>
              <span>Completed review</span>
              <strong>{scores.completed_human_reviews ?? 0}</strong>
            </div>
            <div>
              <span>Profile tested</span>
              <strong>{run?.profile?.label || 'Random profile'}</strong>
            </div>
            <div>
              <span>Target mode</span>
              <strong>{run?.target_mode === 'lightweight_no_guardrails' ? 'No guardrails' : 'Guardrailed'}</strong>
            </div>
          </div>
        )}

        {!embedded && (
          <div className="red-team-method-scores">
            {Object.entries(methodScores).map(([method, value]) => (
              <div key={method}>
                <span>{method}</span>
                <b>{formatScore(value)}</b>
              </div>
            ))}
          </div>
        )}

        {!embedded && (
          <div className="red-team-final-actions">
            <button
              aria-label={finalReport ? 'Re-save final results' : 'Save final results'}
              className="red-team-save-final"
              type="button"
              disabled={!canFinalize || finalizing}
              onClick={async () => {
                setFinalizeError(null);
                setFinalizing(true);
                try {
                  await onSaveFinalResults();
                } catch (err) {
                  setFinalizeError(err.message);
                } finally {
                  setFinalizing(false);
                }
              }}
            >
              <span aria-hidden="true" />
            </button>
            {finalReport?.download_url && (
              <a href={`${process.env.REACT_APP_RED_TEAM_API_URL || 'http://127.0.0.1:8010'}${finalReport.download_url}`}>
                Download JSON report
              </a>
            )}
            {!canFinalize && status === 'completed' && (
              <span>Complete all pending human reviews before saving the final report.</span>
            )}
          </div>
        )}

        <div className="red-team-review-header">
          <h3>Human mediation</h3>
          <button type="button" onClick={onRefresh}>Refresh results</button>
        </div>

        {reviewCount === 0 ? (
          <p className="red-team-empty">No human review items were flagged for this run.</p>
        ) : (
          <div className="red-team-review-list">
            {Object.values(groupedReviewItems).map((group) => (
              <section className="red-team-layer-group" key={group.method}>
                <h4>{group.methodName}</h4>
                {group.items.map((item) => (
                  <ReviewCase key={item.case_id} item={item} onSubmitReview={onSubmitReview} />
                ))}
              </section>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default RedTeamPanel;
