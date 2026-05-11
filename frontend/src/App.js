import { useEffect, useState } from 'react';

import './App.css';
import PersonaChat from './modules/persona_chat_modules/personaChat';

function App() {
  const [personas, setPersonas] = useState([]);
  const [activePersona, setActivePersona] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [targetCount, setTargetCount] = useState(30);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadPersonas() {
      try {
        setLoading(true);
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/chat/personas?country=netherlands&limit=30`);

        if (!response.ok) {
          throw new Error(`Persona request failed with status ${response.status}`);
        }

        const payload = await response.json();
        if (!cancelled) {
          setPersonas(payload.personas ?? []);
          setTargetCount(payload.target_count ?? 30);
          setIsComplete(Boolean(payload.is_complete));
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPersonas();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className={`ChatApp unbounded-weight300 ${activePersona ? 'isBlurred' : ''}`}>
      <div className="pageSurface">
        <section className="chatHero">
          <p className="eyebrow">Synthetic social agent integrity</p>
          <h1 className="unbounded-weight400">Safeguarding Synthetic Agency</h1>
          <p>
            A framework for measuring and operationalizing system integrity in synthetic social agent systems.
          </p>
        </section>

        {loading && <p className="statusText">Loading personas...</p>}
        {!loading && !error && !isComplete && (
          <p className="statusText">
            Showing {personas.length} saved agents while the profile set completes to {targetCount}.
          </p>
        )}
        {error && <p className="statusText errorText">{error}</p>}

        <section className="personaGrid" aria-label="Synthetic social agent profiles">
          {personas.map((persona) => (
            <article className="personaCard" key={persona.id}>
              <div className="personaCardHeader">
                <h2 className="unbounded-weight400">{persona.label}</h2>
                <span>{persona.traits?.municipality}</span>
              </div>

              <div className="traitList">
                {Object.entries(persona.traits ?? {}).map(([key, value]) => (
                  <span key={key}>{value}</span>
                ))}
              </div>

              <p>{persona.biography}</p>

              <button type="button" onClick={() => setActivePersona(persona)}>
                Open agent
              </button>
            </article>
          ))}
        </section>
      </div>

      {activePersona && (
        <PersonaChat
          personaDetails={activePersona.details}
          personaCountry={activePersona.country}
          showChat={() => setActivePersona(null)}
        />
      )}
    </main>
  );
}

export default App;
