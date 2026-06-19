// Main React shell for the Safeguarding Synthetic Agency prototype.
//
// This component coordinates persona loading, the chat/red-team top-level tabs,
// lightweight-vs-guardrailed chat selection, and the red-team run controller.

import { useEffect, useRef, useState } from 'react';

import './App.css';
import { ComputationalAnalysisWorkspace } from './features/analysis';
import { PersonaWorkspace, usePersonas } from './features/personas';
import {
  RedTeamSettingsView,
  RedTeamSetupPanel,
  useRedTeamController,
} from './features/redTeam';
import PersonaChat from './modules/persona_chat_modules/personaChat';
import RedTeamPanel from './modules/red_team_modules/redTeamPanel';

function formatRunDate(value) {
  if (!value) return 'Unknown date';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString([], {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function SavedRedTeamRunsView({
  reports,
  status,
  error,
  onRefresh,
  onSelectReport,
}) {
  const hasReports = reports.length > 0;
  return (
    <div className="redTeamSavedRunsView">
      <div className="redTeamSavedRunsHeader">
        <div>
          <span>Previous red-team evaluations</span>
          <h2 className="unbounded-weight400">Ready to evaluate</h2>
          <p>Select a saved run to inspect its answer review, scores, profiles, and downloads.</p>
        </div>
        <button type="button" onClick={onRefresh}>
          {status === 'loading' ? 'Loading' : 'Refresh'}
        </button>
      </div>

      {error && <p className="statusText errorText">{error}</p>}

      {!hasReports && status !== 'loading' ? (
        <div className="redTeamSavedRunsEmpty">
          <h3>No saved red-team runs yet</h3>
          <p>Start and finalize an evaluation. Saved JSON/PDF results will appear here automatically.</p>
        </div>
      ) : (
        <div className="redTeamSavedRunList">
          {reports.map((report) => (
            <button
              className="redTeamSavedRunCard"
              key={report.run_id}
              type="button"
              onClick={() => onSelectReport(report.run_id)}
            >
              <span>{formatRunDate(report.finalized_at || report.completed_at || report.created_at)}</span>
              <strong>{report.run_id}</strong>
              <div className="redTeamSavedRunMeta">
                <b>{report.profile_count || 0} profiles</b>
                <b>{report.case_count || 0} answers</b>
                <b>{Math.round((report.overall_score || 0) * 100)}% overall</b>
              </div>
              <small>
                Guardrailed {report.guardrailed_score === undefined || report.guardrailed_score === null ? 'N/A' : `${Math.round(report.guardrailed_score * 100)}%`}
                {' · '}
                Lightweight {report.lightweight_score === undefined || report.lightweight_score === null ? 'N/A' : `${Math.round(report.lightweight_score * 100)}%`}
              </small>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [tabHistory, setTabHistory] = useState([]);
  const [chatPipelineMode, setChatPipelineMode] = useState('guardrailed');
  const [redTeamDetailsMode, setRedTeamDetailsMode] = useState('guardrailed');
  const [selectedResultProfileId, setSelectedResultProfileId] = useState('all');
  const initializedRedTeamProfiles = useRef(false);
  const analysisBackHandlerRef = useRef(null);
  const {
    activePersona,
    error,
    isComplete,
    loading,
    personas,
    selectedPersona,
    setActivePersona,
    setSelectedPersona,
    targetCount,
  } = usePersonas();
  const {
    cancelRedTeamRun,
    editedPromptCount,
    finalizeRedTeamRun,
    generateComputationalAnalysis,
    loadRedTeamPromptSettings,
    refreshRedTeamRun,
    redTeamAnalysis,
    redTeamAnalysisStatus,
    redTeamError,
    redTeamPromptSettingsStatus,
    redTeamReviewItems,
    redTeamRun,
    redTeamScores,
    redTeamSettingsOpen,
    redTeamTargetMode,
    loadSavedRedTeamReports,
    openSavedRedTeamReport,
    resetPromptExpectedAnswer,
    resetRedTeamRun,
    resetHumanReview,
    savedRedTeamReports,
    savedRedTeamReportsStatus,
    selectedPromptSetting,
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
    visiblePromptSettings,
  } = useRedTeamController();

  useEffect(() => {
    if (activeTab === 'red-team' && redTeamPromptSettingsStatus === 'idle') {
      loadRedTeamPromptSettings();
    }
  }, [activeTab, loadRedTeamPromptSettings, redTeamPromptSettingsStatus]);

  const redTeamAvailableProfileCount = personas.length || targetCount || 30;

  function navigateToTab(nextTab) {
    setActiveTab((currentTab) => {
      if (currentTab === nextTab) {
        return currentTab;
      }
      setTabHistory((currentHistory) => [...currentHistory, currentTab].slice(-20));
      return nextTab;
    });
  }

  function handleGlobalBack() {
    if (activePersona) {
      setActivePersona(null);
      return;
    }

    if (activeTab === 'red-team' && redTeamSettingsOpen) {
      setRedTeamSettingsOpen(false);
      return;
    }

    if (activeTab === 'red-team' && redTeamRun) {
      resetRedTeamRun();
      setSelectedResultProfileId('all');
      return;
    }

    if (activeTab === 'analysis' && analysisBackHandlerRef.current?.()) {
      return;
    }

    if (tabHistory.length > 0) {
      const previousTab = tabHistory[tabHistory.length - 1];
      setTabHistory((currentHistory) => currentHistory.slice(0, -1));
      setActiveTab(previousTab);
      return;
    }

    if (window.history.length > 1) {
      window.history.back();
    }
  }

  async function handleOpenSavedRedTeamReport(runId) {
    setSelectedResultProfileId('all');
    await openSavedRedTeamReport(runId);
  }

  useEffect(() => {
    if (!initializedRedTeamProfiles.current && selectedRedTeamProfileIds.length === 0 && personas[0]?.id) {
      initializedRedTeamProfiles.current = true;
      setSelectedRedTeamProfileIds([personas[0].id]);
    }
  }, [personas, selectedRedTeamProfileIds.length, setSelectedRedTeamProfileIds]);

  return (
    <main className={`ChatApp unbounded-weight300 ${activePersona ? 'isBlurred' : ''}`}>
      <div className="pageSurface">
        <header className="appHeader">
          <div>
            <p className="eyebrow">Synthetic social agent integrity</p>
            <h1 className="unbounded-weight400">Safeguarding Synthetic Agency</h1>
          </div>
          <nav className="workspaceTabs" aria-label="Workspace tabs">
            <button
              className={activeTab === 'chat' ? 'isActive' : ''}
              type="button"
              onClick={() => navigateToTab('chat')}
            >
              Chat
            </button>
            <button
              className={activeTab === 'red-team' ? 'isActive' : ''}
              type="button"
              onClick={() => navigateToTab('red-team')}
            >
              Red-teaming
            </button>
            <button
              className={activeTab === 'analysis' ? 'isActive' : ''}
              type="button"
              onClick={() => navigateToTab('analysis')}
            >
              Analysis
            </button>
          </nav>
        </header>

        <div className="workspaceBackRow">
          <button
            aria-label="Go back one step"
            className="workspaceBackButton"
            title="Go back"
            type="button"
            onClick={handleGlobalBack}
          >
            <span aria-hidden="true" />
          </button>
        </div>

        <section className="workspaceShell">
          {activeTab === 'chat' && (
            <PersonaWorkspace
              error={error}
              isComplete={isComplete}
              loading={loading}
              personas={personas}
              selectedPersona={selectedPersona}
              chatPipelineMode={chatPipelineMode}
              setActivePersona={setActivePersona}
              setChatPipelineMode={setChatPipelineMode}
              setSelectedPersona={setSelectedPersona}
              targetCount={targetCount}
            />
          )}

          {activeTab === 'red-team' && redTeamSettingsOpen && (
            <div className="redTeamSettingsFullWindow">
              <RedTeamSettingsView
                editedPromptCount={editedPromptCount}
                loadPromptSettings={loadRedTeamPromptSettings}
                promptSettingsStatus={redTeamPromptSettingsStatus}
                resetPromptExpectedAnswer={resetPromptExpectedAnswer}
                selectedPromptSetting={selectedPromptSetting}
                setRedTeamSettingsOpen={setRedTeamSettingsOpen}
                setSelectedPromptId={setSelectedPromptId}
                updatePromptCalibrationNote={updatePromptCalibrationNote}
                updatePromptExpectedAnswer={updatePromptExpectedAnswer}
                visiblePromptSettings={visiblePromptSettings}
              />
            </div>
          )}

          {activeTab === 'red-team' && !redTeamSettingsOpen && (
            <div className="redTeamWorkspace">
              <RedTeamSetupPanel
                redTeamError={redTeamError}
                redTeamRun={redTeamRun}
                redTeamScores={redTeamScores}
                redTeamTargetMode={redTeamTargetMode}
                redTeamAvailableProfileCount={redTeamAvailableProfileCount}
                redTeamDetailsMode={redTeamDetailsMode}
                personas={personas}
                finalizeRedTeamRun={finalizeRedTeamRun}
                resetRedTeamRun={resetRedTeamRun}
                selectedResultProfileId={selectedResultProfileId}
                selectedRedTeamProfileIds={selectedRedTeamProfileIds}
                selectedRedTeamMethods={selectedRedTeamMethods}
                setRedTeamSettingsOpen={setRedTeamSettingsOpen}
                setRedTeamDetailsMode={setRedTeamDetailsMode}
                setSelectedResultProfileId={setSelectedResultProfileId}
                setSelectedRedTeamProfileIds={setSelectedRedTeamProfileIds}
                setRedTeamTargetMode={setRedTeamTargetMode}
                startRedTeamRun={startRedTeamRun}
                toggleRedTeamMethod={toggleRedTeamMethod}
              />

              <section className="redTeamContentPanel">
                {redTeamRun ? (
                  <RedTeamPanel
                    embedded
                    run={redTeamRun}
                    reviewItems={redTeamReviewItems}
                    selectedProfileId={selectedResultProfileId}
                    error={redTeamError}
                    analysis={redTeamAnalysis}
                    analysisStatus={redTeamAnalysisStatus}
                    onCancel={cancelRedTeamRun}
                    onClose={resetRedTeamRun}
                    onGenerateAnalysis={generateComputationalAnalysis}
                    onRefresh={redTeamRun.loaded_from_final_report ? () => handleOpenSavedRedTeamReport(redTeamRun.run_id) : refreshRedTeamRun}
                    onResetReview={resetHumanReview}
                    onSubmitReview={submitHumanReview}
                  />
                ) : (
                  <SavedRedTeamRunsView
                    reports={savedRedTeamReports}
                    status={savedRedTeamReportsStatus}
                    error={redTeamError}
                    onRefresh={loadSavedRedTeamReports}
                    onSelectReport={handleOpenSavedRedTeamReport}
                  />
                )}
              </section>
            </div>
          )}

          {activeTab === 'analysis' && (
            <ComputationalAnalysisWorkspace
              onRegisterBackHandler={(handler) => {
                analysisBackHandlerRef.current = handler;
              }}
            />
          )}
        </section>
      </div>

      {activePersona && (
        <PersonaChat
          personaProfile={activePersona}
          personaDetails={activePersona.details}
          personaCountry={activePersona.country}
          pipelineMode={chatPipelineMode}
          showChat={() => setActivePersona(null)}
        />
      )}

    </main>
  );
}

export default App;
