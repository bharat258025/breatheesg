import { api } from "./client";
import type { NormalizedRecord, RecordLog, SourceSystem, UploadResponse } from "../types/esg";

export async function fetchSources(): Promise<SourceSystem[]> {
  const { data } = await api.get<SourceSystem[]>("sources/");
  return data;
}

export async function uploadCsv(sourceSystemId: number, file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("source_system_id", String(sourceSystemId));
  form.append("file", file);
  const { data } = await api.post<UploadResponse>("ingestion/upload-csv/", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function fetchRecords(status?: string): Promise<NormalizedRecord[]> {
  const { data } = await api.get<NormalizedRecord[]>("records/", {
    params: status ? { status } : undefined
  });
  return data;
}

export async function fetchRecord(recordId: string): Promise<NormalizedRecord> {
  const { data } = await api.get<NormalizedRecord>(`records/${recordId}/`);
  return data;
}

export async function updateRecordStatus(
  recordId: number,
  payload: Partial<Pick<NormalizedRecord, "status" | "rejection_reason">>
): Promise<NormalizedRecord> {
  const { data } = await api.patch<NormalizedRecord>(`records/${recordId}/`, payload);
  return data;
}

export async function fetchRecordLogs(recordId: number): Promise<RecordLog[]> {
  const { data } = await api.get<RecordLog[]>("record-logs/", { params: { record: recordId } });
  return data;
}
