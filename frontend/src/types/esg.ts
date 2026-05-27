export type SourceSystem = {
  id: number;
  source_type: "sap_fuel" | "utility_electricity" | "corp_travel";
  display_name: string;
};

export type UploadSummary = {
  total_rows: number;
  parsed_rows: number;
  error_rows: number;
};

export type UploadResponse = {
  batch_id: number;
  status: string;
  summary: UploadSummary;
};

export type NormalizedRecord = {
  id: number;
  activity_date: string;
  activity_type: string;
  scope: "scope1" | "scope2" | "scope3";
  normalized_quantity: string;
  normalized_unit: string;
  emissions_tco2e: string;
  status: "pending" | "suspicious" | "approved" | "rejected";
  suspicion_score: string;
  validation_flags: string[];
  rejection_reason: string;
  is_locked: boolean;
};

export type RecordLog = {
  id: number;
  event_type: string;
  reason: string;
  created_at: string;
};
