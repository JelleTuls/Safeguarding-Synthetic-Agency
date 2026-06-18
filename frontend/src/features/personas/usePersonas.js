// Persona loading and selection hook.
//
// This hook owns the frontend state for the cached 30-profile persona set,
// including the active chat persona, loading/error state, and target profile
// count shown in the sidebar.

import { useEffect, useState } from 'react';

import { fetchPersonas } from './personaApi';


export function usePersonas() {
  const [personas, setPersonas] = useState([]);
  const [activePersona, setActivePersona] = useState(null);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [targetCount, setTargetCount] = useState(30);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadPersonas() {
      try {
        setLoading(true);
        const payload = await fetchPersonas({ country: 'netherlands', limit: 30 });
        if (!cancelled) {
          setPersonas(payload.personas ?? []);
          setSelectedPersona((current) => current || payload.personas?.[0] || null);
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

  return {
    activePersona,
    error,
    isComplete,
    loading,
    personas,
    selectedPersona,
    setActivePersona,
    setSelectedPersona,
    targetCount,
  };
}
