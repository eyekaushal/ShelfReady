import { useQuery } from '@tanstack/react-query'

import { aiApi } from '../api/aiApi'

/** Is AI switched on on the server? Cached for 5 minutes; while unknown, buttons stay enabled. */
export function useAiStatus() {
  const query = useQuery({ queryKey: ['ai-status'], queryFn: aiApi.status, staleTime: 5 * 60 * 1000 })
  return { enabled: query.data ? query.data.enabled : true, isLoading: query.isPending }
}
