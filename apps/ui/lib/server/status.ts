import http from "node:http";
import https from "node:https";
import net from "node:net";

import { loadEnv } from "@/lib/server/env";

type Reachability = {
  reachable: boolean;
  detail?: string;
};

type OpenSearchStatus = Reachability & {
  indices?: string[];
  indexCount?: number;
};

type QdrantStatus = Reachability & {
  collections?: string[];
  pointsCount?: number;
};

type MinioStatus = Reachability;

type PostgresStatus = Reachability;

export type BackendStatus = {
  timestamp: string;
  services: {
    postgres: PostgresStatus;
    opensearch: OpenSearchStatus;
    qdrant: QdrantStatus;
    minio: MinioStatus;
  };
};

type RequestOptions = {
  headers?: Record<string, string>;
  timeoutMs?: number;
  verifyCerts?: boolean;
};

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  return value.toLowerCase() === "true";
}

function tcpCheck(host: string, port: number, timeoutMs = 1500): Promise<Reachability> {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    const onFailure = (detail: string) => {
      socket.destroy();
      resolve({ reachable: false, detail });
    };
    socket.setTimeout(timeoutMs);
    socket.once("error", (err) => onFailure(err.message));
    socket.once("timeout", () => onFailure("timeout"));
    socket.connect(port, host, () => {
      socket.end();
      resolve({ reachable: true });
    });
  });
}

function requestJson(
  url: string,
  options: RequestOptions = {}
): Promise<{ ok: boolean; status: number; data?: any; error?: string }> {
  return new Promise((resolve) => {
    const parsed = new URL(url);
    const isHttps = parsed.protocol === "https:";
    const requester = isHttps ? https : http;
    const verifyCerts = options.verifyCerts ?? true;
    const agent = isHttps ? new https.Agent({ rejectUnauthorized: verifyCerts }) : undefined;

    const req = requester.request(
      {
        method: "GET",
        hostname: parsed.hostname,
        port: parsed.port,
        path: `${parsed.pathname}${parsed.search}`,
        headers: options.headers,
        agent,
        timeout: options.timeoutMs ?? 2000,
      },
      (res) => {
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          const status = res.statusCode ?? 0;
          if (!body) {
            resolve({ ok: status >= 200 && status < 300, status });
            return;
          }
          try {
            const data = JSON.parse(body);
            resolve({ ok: status >= 200 && status < 300, status, data });
          } catch (err) {
            if (status >= 200 && status < 300) {
              resolve({ ok: true, status, data: body });
            } else {
              resolve({ ok: false, status, error: "invalid_json" });
            }
          }
        });
      }
    );

    req.on("error", (err) => {
      resolve({ ok: false, status: 0, error: err.message });
    });
    req.on("timeout", () => {
      req.destroy();
      resolve({ ok: false, status: 0, error: "timeout" });
    });
    req.end();
  });
}

export async function getBackendStatus(): Promise<BackendStatus> {
  loadEnv();

  const postgresHost = process.env.POSTGRES_HOST ?? "localhost";
  const postgresPort = Number(process.env.POSTGRES_PORT ?? 5432);
  const opensearchHost = process.env.OPENSEARCH_HOST ?? "localhost";
  const opensearchPort = Number(process.env.OPENSEARCH_PORT ?? 9200);
  const opensearchScheme = process.env.OPENSEARCH_SCHEME ?? "https";
  const opensearchUser = process.env.OPENSEARCH_USER;
  const opensearchPassword = process.env.OPENSEARCH_PASSWORD;
  const opensearchVerify = parseBoolean(process.env.OPENSEARCH_VERIFY_CERTS, false);
  const opensearchIndex = process.env.OPENSEARCH_INDEX ?? "plk_chunks_v1";

  const qdrantHost = process.env.QDRANT_HOST ?? "localhost";
  const qdrantPort = Number(process.env.QDRANT_PORT ?? 6333);
  const qdrantHttps = parseBoolean(process.env.QDRANT_HTTPS, false);
  const qdrantCollection = process.env.QDRANT_COLLECTION ?? "plk_chunks_v1";

  const minioEndpoint = process.env.MINIO_ENDPOINT ?? "localhost:9000";

  const postgres = await tcpCheck(postgresHost, postgresPort);

  const minioUrl = minioEndpoint.startsWith("http")
    ? new URL(minioEndpoint)
    : new URL(`http://${minioEndpoint}`);
  const minioHealth = await requestJson(`${minioUrl.origin}/minio/health/ready`, {
    timeoutMs: 1500,
  });
  const minio: MinioStatus = minioHealth.ok
    ? { reachable: true }
    : { reachable: false, detail: minioHealth.error ?? `status_${minioHealth.status}` };

  const osAuth = opensearchUser && opensearchPassword
    ? Buffer.from(`${opensearchUser}:${opensearchPassword}`).toString("base64")
    : undefined;
  const osHeaders = osAuth ? { Authorization: `Basic ${osAuth}` } : undefined;
  const osBase = `${opensearchScheme}://${opensearchHost}:${opensearchPort}`;

  const osIndicesResp = await requestJson(`${osBase}/_cat/indices?format=json`, {
    headers: osHeaders,
    verifyCerts: opensearchVerify,
  });
  const opensearch: OpenSearchStatus = osIndicesResp.ok
    ? {
        reachable: true,
        indices: Array.isArray(osIndicesResp.data)
          ? osIndicesResp.data.map((row: any) => row.index).filter(Boolean)
          : [],
      }
    : {
        reachable: false,
        detail: osIndicesResp.error ?? `status_${osIndicesResp.status}`,
      };

  if (opensearch.reachable) {
    const countResp = await requestJson(`${osBase}/${opensearchIndex}/_count`, {
      headers: osHeaders,
      verifyCerts: opensearchVerify,
    });
    if (countResp.ok) {
      opensearch.indexCount = Number(countResp.data?.count ?? 0);
    } else {
      opensearch.detail = countResp.error ?? `count_status_${countResp.status}`;
    }
  }

  const qdrantBase = `${qdrantHttps ? "https" : "http"}://${qdrantHost}:${qdrantPort}`;
  const qdrantCollections = await requestJson(`${qdrantBase}/collections`, { timeoutMs: 1500 });
  const qdrant: QdrantStatus = qdrantCollections.ok
    ? {
        reachable: true,
        collections: Array.isArray(qdrantCollections.data?.result?.collections)
          ? qdrantCollections.data.result.collections.map((item: any) => item.name).filter(Boolean)
          : [],
      }
    : {
        reachable: false,
        detail: qdrantCollections.error ?? `status_${qdrantCollections.status}`,
      };

  if (qdrant.reachable) {
    const collectionResp = await requestJson(`${qdrantBase}/collections/${qdrantCollection}`);
    if (collectionResp.ok) {
      qdrant.pointsCount = Number(collectionResp.data?.result?.points_count ?? 0);
    } else {
      qdrant.detail = collectionResp.error ?? `collection_status_${collectionResp.status}`;
    }
  }

  return {
    timestamp: new Date().toISOString(),
    services: {
      postgres,
      opensearch,
      qdrant,
      minio,
    },
  };
}
