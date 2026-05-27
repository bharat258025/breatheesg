import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchRecord,
  fetchRecordLogs,
  fetchRecords,
  fetchSources,
  updateRecordStatus,
  uploadCsv
} from "../api/esgApi";

export function useSources() {
  return useQuery({ queryKey: ["sources"], queryFn: fetchSources });
}

export function useUploadCsv() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sourceSystemId, file }: { sourceSystemId: number; file: File }) =>
      uploadCsv(sourceSystemId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records"] });
    }
  });
}

export function useRecords(status?: string) {
  return useQuery({
    queryKey: ["records", status ?? "all"],
    queryFn: () => fetchRecords(status)
  });
}

export function useRecord(recordId?: string) {
  return useQuery({
    queryKey: ["record", recordId],
    queryFn: () => fetchRecord(recordId!),
    enabled: Boolean(recordId)
  });
}

export function useRecordLogs(recordId?: number) {
  return useQuery({
    queryKey: ["record-logs", recordId],
    queryFn: () => fetchRecordLogs(recordId!),
    enabled: Boolean(recordId)
  });
}

export function useUpdateRecordStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      recordId,
      status,
      rejection_reason
    }: {
      recordId: number;
      status: "approved" | "rejected" | "pending";
      rejection_reason?: string;
    }) => updateRecordStatus(recordId, { status, rejection_reason }),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["record", String(vars.recordId)] });
      queryClient.invalidateQueries({ queryKey: ["records"] });
      queryClient.invalidateQueries({ queryKey: ["record-logs", vars.recordId] });
    }
  });
}
