import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useWorldGeneration() {
  const qc = useQueryClient();

  const planMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await fetch(`${API_BASE}/world/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to generate world plan');
      return res.json();
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['world'] });
    },
  });

  const getWorld = useQuery({
    queryKey: ['world'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/world`);
      return res.json();
    },
    enabled: false,
  });

  return {
    generatePlan: planMutation.mutate,
    generating: planMutation.isPending,
    worldData: planMutation.data,
    fetchWorlds: getWorld.refetch,
  };
}
