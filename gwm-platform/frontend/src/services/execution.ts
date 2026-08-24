import { useQuery, useMutation } from '@tanstack/react-query';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useExecution() {
  const startMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await fetch(`${API_BASE}/execution/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to start execution');
      return res.json();
    },
  });

  const stopMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const res = await fetch(`${API_BASE}/execution/${sessionId}/stop`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to stop execution');
      return res.json();
    },
  });

  const getSession = useQuery({
    queryKey: ['execution'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/execution`);
      return res.json();
    },
    enabled: false,
  });

  return {
    startExecution: startMutation.mutate,
    starting: startMutation.isPending,
    stopExecution: stopMutation.mutate,
    stopping: stopMutation.isPending,
    sessionData: startMutation.data,
    fetchSession: getSession.refetch,
  };
}
