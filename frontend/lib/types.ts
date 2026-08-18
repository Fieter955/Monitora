export type Role = "admin" | "viewer";
export type DeviceKind =
  | "linux_server"
  | "router"
  | "switch"
  | "access_point"
  | "cctv"
  | "hub"
  | "website"
  | "other";

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export interface Device {
  id: number;
  name: string;
  kind: DeviceKind;
  address: string;
  location: string;
  prometheus_job: string;
  prometheus_target: string;
  notes: string;
  is_active: boolean;
  room_id: number | null;
  credential_profile_id: number | null;
  librenms_device_id: number | null;
  capabilities: Record<string, unknown>;
  monitoring_level: string;
  stream_url: string;
  floorplan_x: number | null;
  floorplan_y: number | null;
  last_seen_at: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CredentialSecret {
  name: string;
  kind: "snmp_v2c" | "snmp_v3" | "onvif_rtsp";
  community?: string;
  username?: string;
  password?: string;
  auth_protocol?: string;
  privacy_protocol?: string;
  privacy_password?: string;
}

export interface DeviceInput {
  name: string;
  kind: DeviceKind;
  address: string;
  location: string;
  prometheus_job: string;
  prometheus_target: string;
  notes: string;
  is_active: boolean;
  room_id: number | null;
  credential_profile_id: number | null;
  stream_url: string;
  floorplan_x: number | null;
  floorplan_y: number | null;
  credential?: CredentialSecret;
}

export type LocationKind = "site" | "building" | "floor" | "room";

export interface Location {
  id: number;
  name: string;
  kind: LocationKind;
  parent_id: number | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Floorplan {
  id: number;
  location_id: number;
  filename: string;
  content_type: string;
  image_url: string;
  updated_at: string;
}

export type PortExpectation = "required" | "spare" | "ignored";

export interface NetworkPort {
  id: number;
  device_id: number;
  source_port_id: number;
  if_index: number | null;
  name: string;
  description: string;
  alias: string;
  admin_status: string;
  oper_status: string;
  speed_bps: number | null;
  rx_bps: number | null;
  tx_bps: number | null;
  utilization_percent: number | null;
  errors_in: number | null;
  errors_out: number | null;
  discards_in: number | null;
  discards_out: number | null;
  mac_address: string;
  expectation: PortExpectation;
  expected_device_id: number | null;
  expectation_label: string;
  condition: string;
  last_seen_at: string;
}

export interface DeviceIssue {
  code: string;
  severity: "warning" | "critical";
  title: string;
  detail: string;
  port_id: number | null;
}

export interface DeviceHealth {
  device_id: number;
  status: "healthy" | "warning" | "critical" | "unknown";
  monitoring_level: string;
  checked_at: string | null;
  last_seen_at: string | null;
  reason: string;
  issues: DeviceIssue[];
  ports: NetworkPort[];
}

export interface DiscoveryResult {
  device_id: number;
  state: "ready" | "partial" | "unavailable" | "failed";
  message: string;
  capabilities: string[];
  ports: NetworkPort[];
}

export interface TopologyNode {
  id: number;
  name: string;
  kind: DeviceKind;
  address: string;
  room_id: number | null;
  location: string;
  status: "healthy" | "warning" | "critical" | "unknown";
  monitoring_level: string;
}

export interface TopologyEdge {
  id: string;
  origin: string;
  source_device_id: number;
  target_device_id: number | null;
  source_port: string;
  target_port: string;
  target_name: string;
  active: boolean;
  utilization_percent: number | null;
}

export interface Topology {
  generated_at: string;
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export interface DeviceMetric {
  device_id: number;
  status: "online" | "offline" | "unknown";
  cpu_percent: number | null;
  memory_percent: number | null;
  disk_percent: number | null;
  uptime_seconds: number | null;
  receive_bytes_per_second: number | null;
  transmit_bytes_per_second: number | null;
}

export interface MonitoringSummary {
  available: boolean;
  checked_at: string;
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  unknown_devices: number;
  firing_alerts: number;
  devices: DeviceMetric[];
  message: string | null;
}

export interface AlertItem {
  name: string;
  severity: string;
  state: string;
  instance: string;
  summary: string;
  active_since: string | null;
}
