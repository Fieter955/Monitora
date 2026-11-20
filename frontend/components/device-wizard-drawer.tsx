"use client";

import {FormEvent, useEffect, useState} from "react";
import {Icon} from "@/components/icons";
import {EmptyState, StatusBadge} from "@/components/status";
import {api, ApiError} from "@/lib/api";
import type {
  CredentialSecret,
  Device,
  DeviceInput,
  DeviceKind,
  DiscoveryResult,
  Location,
  NetworkPort,
  PortExpectation,
} from "@/lib/types";

export const kindLabels: Record<DeviceKind, string> = {
  linux_server: "Server Linux",
  windows_server: "Server Windows",
  router: "Router",
  switch: "Switch",
  access_point: "Access point",
  cctv: "CCTV",
  hub: "Hub",
  website: "Website",
  other: "Komputer / client",
};

const initialInput: DeviceInput = {
  name: "",
  kind: "switch",
  address: "",
  location: "",
  prometheus_job: "snmp",
  prometheus_target: "",
  notes: "",
  is_active: true,
  room_id: null,
  credential_profile_id: null,
  stream_url: "",
  floorplan_x: null,
  floorplan_y: null,
  asset_tag: null,
  physical_group: "",
  physical_position: "",
  network_role: "endpoint",
  isp_name: "",
  wan_if_name: "",
  wan_if_index: null,
};

const wizardSteps = [
  {id: 1, label: "Identitas", subtitle: "Identitas dan lokasi"},
  {id: 2, label: "Akses", subtitle: "Akses monitoring"},
  {id: 3, label: "Port", subtitle: "Konfirmasi fungsi port"},
] as const;

export interface DeviceWizardDrawerProps {
  device: Device | null;
  locations: Location[];
  onClose: () => void;
  onSaved: (message: string) => Promise<void>;
}

/**
 * Drawer wizard tiga tahap untuk menambah atau mengubah konfigurasi perangkat dan fungsi port.
 */
export function DeviceWizardDrawer({
  device,
  locations,
  onClose,
  onSaved,
}: DeviceWizardDrawerProps) {
  const [form, setForm] = useState<DeviceInput>(
    device
      ? {
          name: device.name,
          kind: device.kind,
          address: device.address,
          location: device.location,
          prometheus_job: device.prometheus_job,
          prometheus_target: device.prometheus_target,
          notes: device.notes,
          is_active: device.is_active,
          room_id: device.room_id,
          credential_profile_id: device.credential_profile_id,
          stream_url: device.stream_url,
          floorplan_x: device.floorplan_x,
          floorplan_y: device.floorplan_y,
          asset_tag: device.asset_tag,
          physical_group: device.physical_group,
          physical_position: device.physical_position,
          network_role: device.network_role,
          isp_name: device.isp_name,
          wan_if_name: device.wan_if_name,
          wan_if_index: device.wan_if_index,
        }
      : initialInput,
  );
  const [credential, setCredential] = useState<CredentialSecret>({
    name: device ? `Akses ${device.name}` : "",
    kind: "snmp_v2c",
    community: "",
  });
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState("");
  const [savedDevice, setSavedDevice] = useState<Device | null>(device);
  const [discovery, setDiscovery] = useState<DiscoveryResult | null>(null);
  const [portModes, setPortModes] = useState<Record<number, PortExpectation>>({});

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  function setField<K extends keyof DeviceInput>(key: K, value: DeviceInput[K]) {
    setForm((current) => ({...current, [key]: value}));
  }

  function changeKind(kind: DeviceKind) {
    const prometheus_job =
      kind === "linux_server"
        ? "node"
        : kind === "windows_server"
          ? "windows"
          : kind === "website"
            ? "blackbox"
            : kind === "switch"
              ? "snmp"
              : ["router", "access_point", "other"].includes(kind)
                ? "icmp"
                : kind === "cctv"
                  ? "cctv"
                  : "none";
    setForm((current) => ({
      ...current,
      kind,
      prometheus_job,
      credential_profile_id: prometheus_job === "icmp" ? null : current.credential_profile_id,
      prometheus_target: current.prometheus_target || current.address,
    }));
    setCredential((current) => ({
      ...current,
      kind: kind === "cctv" ? "onvif_rtsp" : "snmp_v2c",
    }));
  }

  function secret(): CredentialSecret | undefined {
    if (form.kind === "cctv") {
      return credential.username || credential.password
        ? {...credential, name: credential.name || `Akses ${form.name}`}
        : undefined;
    }
    if (!["router", "switch", "access_point"].includes(form.kind) || form.prometheus_job !== "snmp") {
      return undefined;
    }
    if (credential.kind === "snmp_v2c" && !credential.community) return undefined;
    return {...credential, name: credential.name || `Akses ${form.name}`};
  }

  function goToAccess() {
    if (!form.name.trim() || !form.address.trim()) {
      setError("Nama dan alamat perangkat wajib diisi.");
      return;
    }
    setError("");
    setStep(2);
  }

  function goToStep(targetStep: number) {
    if (targetStep === 1) {
      setError("");
      setStep(1);
      return;
    }
    if (targetStep === 2) {
      goToAccess();
      return;
    }
    if (targetStep === 3 && discovery) {
      setError("");
      setStep(3);
    }
  }

  async function testConnection() {
    setError("");
    setTestResult("Menguji koneksi…");
    try {
      const result = await api<{message: string}>("/devices/test-connection", {
        method: "POST",
        body: JSON.stringify({
          address: form.address,
          kind: form.kind,
          prometheus_job: form.prometheus_job,
          stream_url: form.stream_url,
          credential: secret(),
        }),
      });
      setTestResult(result.message);
    } catch (reason) {
      setTestResult("");
      setError(reason instanceof ApiError ? reason.message : "Koneksi tidak dapat diuji");
    }
  }

  async function saveAndDiscover() {
    setError("");
    setSaving(true);
    try {
      const payload = {
        ...form,
        credential_profile_id: form.prometheus_job === "icmp" ? null : form.credential_profile_id,
        prometheus_target: form.prometheus_target || form.address,
        credential: secret(),
      };
      const stored = device
        ? await api<Device>(`/devices/${device.id}`, {method: "PATCH", body: JSON.stringify(payload)})
        : await api<Device>("/devices", {method: "POST", body: JSON.stringify(payload)});
      setSavedDevice(stored);
      const result = await api<DiscoveryResult>(`/devices/${stored.id}/discover`, {method: "POST"});
      if (form.prometheus_job === "icmp") {
        await onSaved(`${stored.name} tersimpan dan monitoring ICMP telah diaktifkan.`);
        return;
      }
      setDiscovery(result);
      setPortModes(Object.fromEntries(result.ports.map((port) => [port.id, port.expectation])));
      setStep(3);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Perangkat tidak dapat disimpan");
    } finally {
      setSaving(false);
    }
  }

  async function finish() {
    if (!savedDevice) return;
    setSaving(true);
    setError("");
    try {
      if (form.network_role === "gateway" && form.prometheus_job === "snmp") {
        await api(`/devices/${savedDevice.id}`, {
          method: "PATCH",
          body: JSON.stringify({
            isp_name: form.isp_name,
            wan_if_name: form.wan_if_name,
            wan_if_index: form.wan_if_index,
          }),
        });
      }
      if (discovery?.ports.length) {
        await api(`/devices/${savedDevice.id}/port-expectations`, {
          method: "PUT",
          body: JSON.stringify({
            ports: discovery.ports.map((port) => ({
              port_id: port.id,
              mode: portModes[port.id] ?? "spare",
              expected_device_id: null,
              label: port.alias || port.name,
            })),
          }),
        });
      }
      await onSaved(`${savedDevice.name} tersimpan. Selanjutnya tempatkan melalui Peta Lokasi.`);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Aturan port tidak dapat disimpan");
    } finally {
      setSaving(false);
    }
  }

  function handleFormSubmit(event: FormEvent) {
    event.preventDefault();
    if (step === 1) {
      goToAccess();
      return;
    }
    if (step === 3) {
      void finish();
      return;
    }
    void saveAndDiscover();
  }

  const currentMeta = wizardSteps[step - 1];
  const headerSubtitle = device ? `${device.name} · ${device.address}` : currentMeta.subtitle;

  return (
    <>
      <button className="drawer-scrim" type="button" aria-label="Tutup formulir" onClick={onClose} />
      <section
        className="drawer drawer-wide drawer-wizard"
        role="dialog"
        aria-modal="true"
        aria-labelledby="device-form-title"
      >
        <header className="drawer-header">
          <div>
            <h2 id="device-form-title">{device ? "Edit perangkat" : "Tambah perangkat"}</h2>
            <p>{headerSubtitle}</p>
          </div>
          <button className="icon-button" type="button" aria-label="Tutup" onClick={onClose}>
            <Icon name="close" />
          </button>
        </header>

        <ol className="wizard-steps" aria-label="Tahap konfigurasi">
          {wizardSteps.map((item) => {
            const stateClass =
              step === item.id ? "current" : step > item.id ? "completed" : "";
            const isDisabled = item.id === 3 && discovery === null;
            return (
              <li key={item.id} className={stateClass}>
                <button
                  type="button"
                  className="wizard-step-button"
                  aria-current={step === item.id ? "step" : undefined}
                  disabled={isDisabled}
                  onClick={() => goToStep(item.id)}
                >
                  <span className="wizard-step-index">{item.id}</span>
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ol>

        <div className="drawer-body">
          <form id="device-wizard-form" onSubmit={handleFormSubmit}>
            {error && (
              <div className="form-error" role="alert">
                {error}
              </div>
            )}
            {step === 1 && (
              <IdentityStep
                form={form}
                locations={locations}
                setField={setField}
                changeKind={changeKind}
              />
            )}
            {step === 2 && (
              <AccessStep
                form={form}
                credential={credential}
                setField={setField}
                setCredential={setCredential}
                testResult={testResult}
              />
            )}
            {step === 3 && (
              <PortConfirmation
                discovery={discovery}
                portModes={portModes}
                setPortModes={setPortModes}
                gateway={form.network_role === "gateway"}
                ispName={form.isp_name}
                wanIfIndex={form.wan_if_index}
                setIspName={(value) => setField("isp_name", value)}
                setWan={(port) => {
                  setField("wan_if_index", port.if_index);
                  setField("wan_if_name", port.name);
                }}
                clearWan={() => {
                  setField("wan_if_index", null);
                  setField("wan_if_name", "");
                }}
              />
            )}
          </form>
        </div>

        <footer className="drawer-footer">
          <button
            className="button"
            type="button"
            onClick={
              step === 1
                ? onClose
                : () => {
                    setError("");
                    setStep(step - 1);
                  }
            }
          >
            {step === 1 ? "Batal" : "Kembali"}
          </button>

          <div className="drawer-footer-group">
            {step === 1 && (
              <button className="button button-primary" type="button" onClick={goToAccess}>
                Lanjut ke akses
              </button>
            )}
            {step === 2 && (
              <>
                <button className="button" type="button" onClick={() => void testConnection()}>
                  Uji koneksi
                </button>
                <button
                  className="button button-primary"
                  type="submit"
                  form="device-wizard-form"
                  disabled={saving}
                >
                  {saving
                    ? "Menyimpan…"
                    : form.prometheus_job === "icmp"
                      ? "Simpan & aktifkan ICMP"
                      : "Simpan & temukan port"}
                </button>
              </>
            )}
            {step === 3 && (
              <button
                className="button button-primary"
                type="button"
                onClick={() => void finish()}
                disabled={saving}
              >
                {saving ? "Menyimpan…" : "Simpan aturan port"}
              </button>
            )}
          </div>
        </footer>
      </section>
    </>
  );
}

function IdentityStep({
  form,
  locations,
  setField,
  changeKind,
}: {
  form: DeviceInput;
  locations: Location[];
  setField: <K extends keyof DeviceInput>(key: K, value: DeviceInput[K]) => void;
  changeKind: (kind: DeviceKind) => void;
}) {
  return (
    <div className="wizard-stack">
      <section className="wizard-section" aria-labelledby="identity-section-title">
        <div className="wizard-section-head">
          <h3 id="identity-section-title">Identitas &amp; jaringan</h3>
          <p>Informasi utama perangkat dan alamat jaringan yang dipantau.</p>
        </div>
        <div className="form-grid">
          <div className="field field-full">
            <label htmlFor="name">Nama perangkat</label>
            <input
              id="name"
              required
              value={form.name}
              onChange={(event) => setField("name", event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="kind">Jenis</label>
            <select
              id="kind"
              value={form.kind}
              onChange={(event) => changeKind(event.target.value as DeviceKind)}
            >
              {Object.entries(kindLabels).map(([value, label]) => (
                <option value={value} key={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="network-role">Peran jaringan</label>
            <select
              id="network-role"
              value={form.network_role}
              onChange={(event) =>
                setField("network_role", event.target.value as DeviceInput["network_role"])
              }
            >
              <option value="gateway">Gateway ISP</option>
              <option value="distribution">Distribusi pusat</option>
              <option value="access">Akses/cabang</option>
              <option value="endpoint">Perangkat akhir</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="address">IP atau hostname</label>
            <input
              id="address"
              required
              value={form.address}
              onChange={(event) => {
                setField("address", event.target.value);
                if (!form.prometheus_target) setField("prometheus_target", event.target.value);
              }}
            />
          </div>
          <div className="field">
            <label htmlFor="asset-tag">Label aset</label>
            <input
              id="asset-tag"
              value={form.asset_tag ?? ""}
              onChange={(event) => setField("asset_tag", event.target.value || null)}
              placeholder="SW-RS-01"
            />
          </div>
        </div>
      </section>

      <section className="wizard-section" aria-labelledby="physical-section-title">
        <div className="wizard-section-head">
          <h3 id="physical-section-title">Lokasi fisik &amp; catatan</h3>
          <p>Memudahkan tim teknisi menemukan perangkat saat terjadi gangguan.</p>
        </div>
        <div className="form-grid">
          <div className="field field-full">
            <label htmlFor="room">Ruang</label>
            <select
              id="room"
              value={form.room_id ?? ""}
              onChange={(event) =>
                setField("room_id", event.target.value ? Number(event.target.value) : null)
              }
            >
              <option value="">Belum dipetakan</option>
              {locations
                .filter((item) => item.kind === "room")
                .map((item) => (
                  <option value={item.id} key={item.id}>
                    {locationPath(item, locations)}
                  </option>
                ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="physical-group">Rak atau patokan</label>
            <input
              id="physical-group"
              value={form.physical_group}
              onChange={(event) => setField("physical_group", event.target.value)}
              placeholder="Rack 01 / Koridor timur"
            />
          </div>
          <div className="field">
            <label htmlFor="physical-position">Posisi fisik</label>
            <input
              id="physical-position"
              value={form.physical_position}
              onChange={(event) => setField("physical_position", event.target.value)}
              placeholder="U12 / plafon dekat pintu"
            />
          </div>
          <div className="field field-full">
            <label htmlFor="location-label">Keterangan posisi lama</label>
            <input
              id="location-label"
              value={form.location}
              onChange={(event) => setField("location", event.target.value)}
              placeholder="Opsional untuk kompatibilitas data lama"
            />
          </div>
          <div className="field field-full">
            <label htmlFor="notes">Catatan</label>
            <textarea
              id="notes"
              value={form.notes}
              onChange={(event) => setField("notes", event.target.value)}
            />
          </div>
        </div>
      </section>
    </div>
  );
}

function AccessStep({
  form,
  credential,
  setField,
  setCredential,
  testResult,
}: {
  form: DeviceInput;
  credential: CredentialSecret;
  setField: <K extends keyof DeviceInput>(key: K, value: DeviceInput[K]) => void;
  setCredential: React.Dispatch<React.SetStateAction<CredentialSecret>>;
  testResult: string;
}) {
  const network = ["router", "switch", "access_point"].includes(form.kind);
  return (
    <div className="wizard-stack">
      <section className="wizard-section" aria-labelledby="monitoring-section-title">
        <div className="wizard-section-head">
          <h3 id="monitoring-section-title">Pengaturan monitoring</h3>
          <p>Tentukan alamat target dan metode pengambilan metrik perangkat.</p>
        </div>
        <div className="form-grid">
          <div className="field field-full">
            <label htmlFor="target">Target monitoring</label>
            <input
              id="target"
              required
              value={form.prometheus_target}
              onChange={(event) => setField("prometheus_target", event.target.value)}
            />
            <small>
              {form.kind === "linux_server"
                ? "Contoh: 10.0.0.1:9100"
                : "Biasanya sama dengan IP perangkat."}
            </small>
          </div>
          {network ? (
            <div className="field field-full">
              <label htmlFor="job">Metode monitoring</label>
              <select
                id="job"
                value={form.prometheus_job}
                onChange={(event) => {
                  const job = event.target.value;
                  setField("prometheus_job", job);
                  if (job === "icmp") setField("credential_profile_id", null);
                }}
              >
                <option value="icmp">ICMP saja (tanpa SNMP)</option>
                <option value="snmp">SNMP dan discovery port</option>
              </select>
            </div>
          ) : (
            <div className="field field-full">
              <label htmlFor="job">Job</label>
              <input
                id="job"
                required
                value={form.prometheus_job}
                onChange={(event) => setField("prometheus_job", event.target.value)}
              />
            </div>
          )}
        </div>

        <div className="wizard-toggle-row">
          <input
            id="active"
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => setField("is_active", event.target.checked)}
          />
          <div>
            <label htmlFor="active">Aktifkan monitoring</label>
            <small>Perangkat dimasukkan ke jadwal pemeriksaan dan pelaporan status otomatis.</small>
          </div>
        </div>

        {network && form.prometheus_job === "icmp" && (
          <div className="notice wizard-notice">
            <span className="notice-mark">i</span>
            <div>
              <strong>Monitoring tanpa SNMP</strong>
              <p>
                Monitora akan memeriksa online/offline dan latensi melalui ICMP. Port, klien Wi-Fi,
                dan metrik internal tidak tersedia.
              </p>
            </div>
          </div>
        )}
      </section>

      {form.kind === "cctv" && (
        <section className="wizard-section" aria-labelledby="cctv-section-title">
          <div className="wizard-section-head">
            <h3 id="cctv-section-title">Akses kamera CCTV</h3>
            <p>Digunakan untuk verifikasi stream RTSP dan status kamera.</p>
          </div>
          <div className="wizard-subsection">
            <div className="form-grid">
              <div className="field field-full">
                <label htmlFor="stream">URL stream RTSP</label>
                <input
                  id="stream"
                  required
                  value={form.stream_url}
                  onChange={(event) => setField("stream_url", event.target.value)}
                  placeholder="rtsp://alamat:554/path"
                />
              </div>
              <SecretField
                id="camera-user"
                label="Username kamera"
                value={credential.username}
                onChange={(value) => setCredential((current) => ({...current, username: value}))}
              />
              <SecretField
                id="camera-password"
                label="Password kamera"
                password
                value={credential.password}
                onChange={(value) => setCredential((current) => ({...current, password: value}))}
              />
            </div>
          </div>
        </section>
      )}

      {network && form.prometheus_job === "snmp" && (
        <section className="wizard-section" aria-labelledby="snmp-section-title">
          <div className="wizard-section-head">
            <h3 id="snmp-section-title">Kredensial SNMP</h3>
            <p>Isi hanya jika ingin memperbarui community atau kredensial akses yang tersimpan.</p>
          </div>
          <div className="wizard-subsection">
            <div className="form-grid">
              <div className="field">
                <label htmlFor="snmp-kind">Versi SNMP</label>
                <select
                  id="snmp-kind"
                  value={credential.kind}
                  onChange={(event) =>
                    setCredential((current) => ({
                      ...current,
                      kind: event.target.value as CredentialSecret["kind"],
                    }))
                  }
                >
                  <option value="snmp_v2c">SNMP v2c</option>
                  <option value="snmp_v3">SNMP v3</option>
                </select>
              </div>
              {credential.kind === "snmp_v2c" ? (
                <SecretField
                  id="community"
                  label="Community read-only"
                  password
                  value={credential.community}
                  onChange={(value) =>
                    setCredential((current) => ({...current, community: value}))
                  }
                />
              ) : (
                <>
                  <SecretField
                    id="snmp-user"
                    label="Username SNMPv3"
                    value={credential.username}
                    onChange={(value) =>
                      setCredential((current) => ({...current, username: value}))
                    }
                  />
                  <SecretField
                    id="snmp-pass"
                    label="Auth password"
                    password
                    value={credential.password}
                    onChange={(value) =>
                      setCredential((current) => ({...current, password: value}))
                    }
                  />
                  <SecretField
                    id="privacy-pass"
                    label="Privacy password"
                    password
                    value={credential.privacy_password}
                    onChange={(value) =>
                      setCredential((current) => ({...current, privacy_password: value}))
                    }
                  />
                </>
              )}
            </div>
          </div>
        </section>
      )}

      {testResult && (
        <div className="notice wizard-notice">
          <span className="notice-mark">i</span>
          <div>
            <strong>Hasil pemeriksaan</strong>
            <p>{testResult}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function SecretField({
  id,
  label,
  value,
  onChange,
  password = false,
}: {
  id: string;
  label: string;
  value?: string;
  onChange: (value: string) => void;
  password?: boolean;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type={password ? "password" : "text"}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function PortConfirmation({
  discovery,
  portModes,
  setPortModes,
  gateway,
  ispName,
  wanIfIndex,
  setIspName,
  setWan,
  clearWan,
}: {
  discovery: DiscoveryResult | null;
  portModes: Record<number, PortExpectation>;
  setPortModes: React.Dispatch<React.SetStateAction<Record<number, PortExpectation>>>;
  gateway: boolean;
  ispName: string;
  wanIfIndex: number | null;
  setIspName: (value: string) => void;
  setWan: (port: NetworkPort) => void;
  clearWan: () => void;
}) {
  if (!discovery) {
    return (
      <EmptyState
        title="Menunggu discovery"
        description="Sistem sedang memeriksa kemampuan perangkat."
      />
    );
  }

  const activeCount = discovery.ports.filter((port) => port.oper_status === "up").length;
  const downCount = discovery.ports.length - activeCount;

  function markActiveAsRequired() {
    if (!discovery) return;
    setPortModes((current) => {
      const next = {...current};
      for (const port of discovery.ports) {
        if (port.oper_status === "up") next[port.id] = "required";
      }
      return next;
    });
  }

  return (
    <div className="wizard-stack">
      <div
        className={`notice wizard-notice ${
          discovery.state === "unavailable" ? "notice-warning" : ""
        }`}
      >
        <span className="notice-mark">i</span>
        <div>
          <strong>
            {discovery.state === "ready" ? "Discovery selesai" : "Discovery sebagian"}
          </strong>
          <p>{discovery.message}</p>
        </div>
      </div>

      {gateway && (
        <section className="wizard-subsection" aria-labelledby="gateway-isp-title">
          <div className="wizard-section-head">
            <h3 id="gateway-isp-title">Koneksi ISP (Gateway)</h3>
            <p>Menandai interface WAN utama agar status konektivitas internet terbaca akurat.</p>
          </div>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="isp-name">Nama ISP</label>
              <input
                id="isp-name"
                value={ispName}
                onChange={(event) => setIspName(event.target.value)}
                placeholder="Contoh: Telkom"
              />
            </div>
            <div className="field">
              <label htmlFor="wan-interface">Interface penerima ISP</label>
              <select
                id="wan-interface"
                value={wanIfIndex ?? ""}
                onChange={(event) => {
                  if (!event.target.value) {
                    clearWan();
                    return;
                  }
                  const port = discovery.ports.find(
                    (item) => item.if_index === Number(event.target.value),
                  );
                  if (port) setWan(port);
                }}
              >
                <option value="">Pilih interface WAN</option>
                {discovery.ports
                  .filter((port) => port.if_index != null)
                  .map((port) => {
                    const distinct = distinctPortDescription(port);
                    return (
                      <option value={port.if_index ?? ""} key={port.id}>
                        {port.name}
                        {distinct ? ` — ${distinct}` : ""}
                      </option>
                    );
                  })}
              </select>
              <small>
                Pilih port MikroTik yang menerima koneksi ISP, misalnya ether1 atau pppoe-out1.
              </small>
            </div>
          </div>
        </section>
      )}

      {discovery.ports.length === 0 ? (
        <EmptyState
          title="Tidak ada port untuk dikonfirmasi"
          description="Simpan perangkat dan audit kembali setelah mesin monitoring tersedia."
        />
      ) : (
        <section className="port-section" aria-labelledby="port-list-heading">
          <div className="port-list-toolbar">
            <div className="port-list-title">
              <h3 id="port-list-heading">Daftar port</h3>
              <span className="port-list-summary">
                {discovery.ports.length} port · {activeCount} aktif · {downCount} kosong/down
              </span>
            </div>
            {activeCount > 0 && (
              <button
                type="button"
                className="port-quick-action"
                onClick={markActiveAsRequired}
              >
                Tandai aktif sebagai wajib
              </button>
            )}
          </div>

          <div className="port-config-table">
            <div className="port-config-head" aria-hidden="true">
              <span>Interface</span>
              <span>Status link</span>
              <span>Fungsi port</span>
            </div>
            <div className="port-config-list">
              {discovery.ports.map((port) => (
                <PortConfigRow
                  key={port.id}
                  port={port}
                  isWan={gateway && port.if_index != null && wanIfIndex === port.if_index}
                  mode={portModes[port.id] ?? "spare"}
                  onChange={(mode) =>
                    setPortModes((current) => ({...current, [port.id]: mode}))
                  }
                />
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

function PortConfigRow({
  port,
  isWan,
  mode,
  onChange,
}: {
  port: NetworkPort;
  isWan: boolean;
  mode: PortExpectation;
  onChange: (mode: PortExpectation) => void;
}) {
  const description = distinctPortDescription(port);
  const speed = formatLinkSpeed(port.speed_bps);
  const meta = [description, speed].filter(Boolean).join(" · ");

  return (
    <div className="port-config">
      <div className="port-config-identity">
        <div className="port-config-name-row">
          <strong className="port-config-name" title={port.name}>
            {port.name}
          </strong>
          {isWan && <span className="port-wan-tag">WAN</span>}
        </div>
        {meta && (
          <span className="port-config-meta" title={meta}>
            {meta}
          </span>
        )}
      </div>
      <div className="port-config-status">
        <StatusBadge
          status={port.oper_status === "up" ? "online" : "unknown"}
          label={port.oper_status === "up" ? "Sedang aktif" : "Kosong/down"}
        />
      </div>
      <select
        className="port-mode-select"
        aria-label={`Fungsi ${port.name}`}
        value={mode}
        onChange={(event) => onChange(event.target.value as PortExpectation)}
      >
        <option value="required">Wajib terisi</option>
        <option value="spare">Cadangan</option>
        <option value="ignored">Diabaikan</option>
      </select>
    </div>
  );
}

function distinctPortDescription(port: NetworkPort): string {
  const normalizedName = port.name.trim().toLowerCase();
  for (const candidate of [port.alias, port.description]) {
    const trimmed = candidate?.trim();
    if (trimmed && trimmed.toLowerCase() !== normalizedName) {
      return trimmed;
    }
  }
  return "";
}

function formatLinkSpeed(speedBps: number | null): string {
  if (!speedBps || speedBps <= 0) return "";
  if (speedBps >= 1_000_000_000) {
    return `${Number((speedBps / 1_000_000_000).toFixed(1))} Gbps`;
  }
  if (speedBps >= 1_000_000) {
    return `${Math.round(speedBps / 1_000_000)} Mbps`;
  }
  if (speedBps >= 1_000) {
    return `${Math.round(speedBps / 1_000)} Kbps`;
  }
  return "";
}

function locationPath(location: Location, locations: Location[]): string {
  const names = [location.name];
  let parent = location.parent_id;
  while (parent) {
    const item = locations.find((entry) => entry.id === parent);
    if (!item) break;
    names.unshift(item.name);
    parent = item.parent_id;
  }
  return names.join(" / ");
}
