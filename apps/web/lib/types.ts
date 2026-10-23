export const SERVICE_IDS = [
  "A_COMPLIANCE",
  "B_CV_FIT",
  "C_MANAGED_CV",
  "D_PROPOSAL",
  "R_RESEARCH",
] as const;
export type ServiceId = (typeof SERVICE_IDS)[number];
export type Role = "OWNER" | "STAFF" | "CUSTOMER";
export interface User {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  role: Role;
}
export interface Envelope {
  version: "pen-envelope-v0.1";
  key_id: string;
  wrapped_key: string;
  iv: string;
  ciphertext: string;
  aad: string;
  result_mac?: string;
}
export interface Project {
  id: string;
  tenant_id: string;
  owner_id: string;
  assigned_to: string | null;
  title: string;
  bidder: string;
  issuer: string;
  deadline: string;
  service_id: ServiceId;
  version: number;
  state: string;
  created_at: string;
  updated_at: string;
}
export interface Job {
  id: string;
  tenant_id: string;
  case_id: string;
  service_id: ServiceId;
  action: string;
  state: string;
  snapshot_digest: string;
  project_version: number;
  attempts: number;
  created_at: string;
  updated_at: string;
  lease_until: string | null;
  result_envelope?: Envelope | null;
  [key: string]: unknown;
}
