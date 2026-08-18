export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    credentials: "include",
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let message = "Permintaan tidak dapat diproses";
    try {
      const payload = await response.json();
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // The default message is clearer than an HTML proxy error.
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function apiForm<T>(path: string, form: FormData): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    body: form,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(payload.detail ?? "Berkas tidak dapat diunggah", response.status);
  }
  return response.json() as Promise<T>;
}

export function formatPercent(value: number | null): string {
  return value == null ? "—" : `${Math.round(value)}%`;
}

export function formatBytes(value: number | null): string {
  if (value == null) return "—";
  const units = ["B/s", "KB/s", "MB/s", "GB/s"];
  let amount = value;
  let index = 0;
  while (amount >= 1024 && index < units.length - 1) {
    amount /= 1024;
    index += 1;
  }
  return `${amount.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatBits(value: number | null): string {
  if (value == null) return "—";
  const units = ["bit/s", "Kbit/s", "Mbit/s", "Gbit/s"];
  let amount = value;
  let index = 0;
  while (amount >= 1000 && index < units.length - 1) {
    amount /= 1000;
    index += 1;
  }
  return `${amount.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatUptime(seconds: number | null): string {
  if (seconds == null) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return days > 0 ? `${days} hari ${hours} jam` : `${hours} jam`;
}
