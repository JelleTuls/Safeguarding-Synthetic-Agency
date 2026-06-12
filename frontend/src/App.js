import { useEffect, useState } from 'react';

import './App.css';
import { PersonaWorkspace, usePersonas } from './features/personas';
import {
  RedTeamSettingsView,
  RedTeamSetupPanel,
  useRedTeamController,
} from './features/redTeam';
import PersonaChat from './modules/persona_chat_modules/personaChat';
import RedTeamPanel from './modules/red_team_modules/redTeamPanel';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [chatPipelineMode, setChatPipelineMode] = useState('guardrailed');
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
    loadRedTeamPromptSettings,
    refreshRedTeamRun,
    redTeamError,
    redTeamMethodScores,
    redTeamPromptSettingsStatus,
    redTeamReviewItems,
    redTeamRun,
    redTeamScores,
    redTeamSettingsOpen,
    redTeamStatusTitle,
    redTeamTargetMode,
    resetPromptExpectedAnswer,
    resetRedTeamRun,
    selectedPromptSetting,
    selectedRedTeamMethods,
    setRedTeamSettingsOpen,
    setRedTeamTargetMode,
    setSelectedPromptId,
    startRedTeamRun,
    submitHumanReview,
    toggleRedTeamMethod,
    updatePromptExpectedAnswer,
    visiblePromptSettings,
  } = useRedTeamController();

  useEffect(() => {
    if (activeTab === 'red-team' && redTeamPromptSettingsStatus === 'idle') {
      loadRedTeamPromptSettings();
    }
  }, [activeTab, loadRedTeamPromptSettings, redTeamPromptSettingsStatus]);

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
              onClick={() => setActiveTab('chat')}
            >
              Chat
            </button>
            <button
              className={activeTab === 'red-team' ? 'isActive' : ''}
              type="button"
              onClick={() => setActiveTab('red-team')}
            >
              Red-teaming
            </button>
          </nav>
        </header>

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
                updatePromptExpectedAnswer={updatePromptExpectedAnswer}
                visiblePromptSettings={visiblePromptSettings}
              />
            </div>
          )}

          {activeTab === 'red-team' && !redTeamSettingsOpen && (
            <div className="redTeamWorkspace">
              <RedTeamSetupPanel
                redTeamError={redTeamError}
                redTeamMethodScores={redTeamMethodScores}
                redTeamRun={redTeamRun}
                redTeamScores={redTeamScores}
                redTeamStatusTitle={redTeamStatusTitle}
                redTeamTargetMode={redTeamTargetMode}
                resetRedTeamRun={resetRedTeamRun}
                selectedRedTeamMethods={selectedRedTeamMethods}
                setRedTeamSettingsOpen={setRedTeamSettingsOpen}
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
                    error={redTeamError}
                    onCancel={cancelRedTeamRun}
                    onClose={resetRedTeamRun}
                    onRefresh={refreshRedTeamRun}
                    onSaveFinalResults={finalizeRedTeamRun}
                    onSubmitReview={submitHumanReview}
                  />
                ) : (
                  <div className="redTeamEmptyState">
                    <h2 className="unbounded-weight400">Ready to evaluate</h2>
                    <p>Select methods, choose the guardrail version, then start a run. Results and human review items will appear here.</p>
                  </div>
                )}
              </section>
            </div>
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
