"use client";

import { useCallback, useState } from "react";

import { DEFAULT_USER_ID, fetchBriefing } from "@/lib/api";
import type { BriefingResponse } from "@/lib/briefing-schema";

type UseBriefingOptions = {
  userId?: string;
  onSuccess?: (response: BriefingResponse) => void;
};

export function useBriefing(options: UseBriefingOptions = {}) {
  const { userId = DEFAULT_USER_ID, onSuccess } = options;
  const [data, setData] = useState<BriefingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const parsed = await fetchBriefing(userId);
      setData(parsed);
      onSuccess?.(parsed);
      return parsed;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to generate briefing";
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [onSuccess, userId]);

  return { data, isLoading, error, refetch };
}
