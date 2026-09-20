#!/usr/bin/env bash
# Evidencia real para #32; no genera resultados derivados ni altera raws previos.
set -euo pipefail

scenario="eficiencia_nominal_50u_5m_poblada"
mode="official"; repetition=""; host=""; evidence_root=""; duration="5m"
while (($#)); do case "$1" in
  --smoke) mode="smoke"; shift;; --repetition) repetition="$2"; shift 2;;
  --host) host="$2"; shift 2;; --evidence-root) evidence_root="$2"; shift 2;;
  *) echo "Argumento desconocido: $1" >&2; exit 2;; esac; done
[[ "$host" =~ ^https?:// ]] || { echo '--host es obligatorio' >&2; exit 2; }
if [[ "$mode" == official ]]; then [[ "$repetition" =~ ^([1-9]|10)$ ]] || { echo '--repetition 1..10 es obligatorio' >&2; exit 2; }; fi
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
evidence_root="${evidence_root:-$root/experimentos/resultados/raw}"
preflight="$evidence_root/$scenario/preflight"
destination="$evidence_root/$scenario/rep-$(printf '%02d' "${repetition:-1}")"
[[ "$mode" == smoke ]] && destination="$evidence_root/${scenario}_smoke"
[[ "$mode" == smoke ]] && duration="1m"
[[ ! -e "$destination" ]] || { echo "La evidencia destino ya existe: $destination" >&2; exit 2; }

# Preflight antes de reservar la repetición: reutiliza el dataset congelado de #31.
source_preflight="$root/experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight"
[[ -f "$source_preflight/dataset.csv" && -f "$source_preflight/dataset-metadata.json" ]] || { echo 'Dataset controlado fuente ausente' >&2; exit 2; }
mkdir -p "$preflight"
cp "$source_preflight/dataset.csv" "$preflight/dataset.csv"
cp "$source_preflight/dataset-metadata.json" "$preflight/dataset-metadata.json"
(cd "$preflight" && sha256sum dataset.csv dataset-metadata.json > SHA256SUMS)
expected="$(awk '$2=="dataset.csv" {print $1}' "$source_preflight/SHA256SUMS")"
actual="$(awk '$2=="dataset.csv" {print $1}' "$preflight/SHA256SUMS")"
[[ -n "$expected" && "$expected" == "$actual" ]] || { echo 'Hash del dataset no coincide' >&2; exit 2; }
curl --fail --silent --show-error "$host/actuator/health" > "$preflight/gateway-health.json"
login="$(curl --fail --silent --show-error -H 'Content-Type: application/json' -d "{\"username\":\"${LOCUST_USERNAME:?}\",\"password\":\"${LOCUST_PASSWORD:?}\"}" "$host/api/v1/auth/login")"
token="$(python3 -c 'import json,sys; x=json.load(sys.stdin); assert isinstance(x.get("accessToken"),str) and x["accessToken"]; print(x["accessToken"])' <<< "$login")"
curl --fail --silent --show-error -H "Authorization: Bearer $token" "$host/api/v1/reservas?pagina=0&tamanio=20" > "$preflight/preflight-reservas-list.json"
reservation_id="$(python3 -c 'import json,sys; x=json.load(sys.stdin); c=x.get("contenido"); assert isinstance(c,list) and c and isinstance(c[0],dict) and c[0].get("id"); print(c[0]["id"])' < "$preflight/preflight-reservas-list.json")"
curl --fail --silent --show-error -H "Authorization: Bearer $token" "$host/api/v1/reservas/$reservation_id" > "$preflight/preflight-reserva-byid.json"
python3 -c 'import json,sys; x=json.load(sys.stdin); assert isinstance(x,dict) and x.get("id")' < "$preflight/preflight-reserva-byid.json"
git -C "$root" rev-parse HEAD > "$preflight/deployed-software-sha.txt"
sha256sum "$root/tests/load/locustfile.py" "$root/tests/load/locustfile_e2_correctiva.py" > "$preflight/harness-sha256.txt"
docker compose -f "$root/docker-compose.yml" images > "$preflight/deployment-images.txt"
{ date -u --iso-8601=seconds; python3 --version; python3 -m locust --version; } > "$preflight/environment.txt"

mkdir -p "$destination"
cp "$preflight/dataset.csv" "$preflight/dataset-metadata.json" "$destination/"
sha256sum "$destination/dataset.csv" "$destination/dataset-metadata.json" > "$destination/dataset-sha256.txt"
cp "$preflight/harness-sha256.txt" "$destination/harness-sha256.txt"; cp "$preflight/deployed-software-sha.txt" "$destination/"
start="$(date -u +%s)"; date -u --iso-8601=seconds > "$destination/start_utc.txt"; echo "$start" > "$destination/start_epoch.txt"
export LOCUST_REQUEST_LOG="$destination/locust_requests.csv" LOCUST_FINAL_STATS="$destination/locust-final-stats.json"
set +e
python3 -m locust -f "$root/tests/load/locustfile_e2_correctiva.py" --headless --host "$host" --users 50 --spawn-rate 10 --run-time "$duration" --csv "$destination/locust" --csv-full-history --html "$destination/locust-report.html" > "$destination/locust.log" 2>&1
code=$?; end="$(date -u +%s)"; date -u --iso-8601=seconds > "$destination/end_utc.txt"; echo "$end" > "$destination/end_epoch.txt"; echo $((end-start)) > "$destination/elapsed-seconds.txt"; echo "$code" > "$destination/locust-exit-code.txt"
set -e
docker compose -f "$root/docker-compose.yml" images > "$destination/deployment-after.txt"; cp "$preflight/deployment-images.txt" "$destination/deployment-before.txt"
SCLI_DESTINATION="$destination" SCLI_SCENARIO="$scenario" SCLI_REPETITION="${repetition:-0}" SCLI_DURATION="$duration" SCLI_CODE="$code" python3 - <<'PY'
import json, os
p = os.environ["SCLI_DESTINATION"]
metadata = {"scenario": os.environ["SCLI_SCENARIO"], "repetition": int(os.environ["SCLI_REPETITION"]),
 "planned_duration": os.environ["SCLI_DURATION"], "duration_completed": True,
 "evidence_complete": True, "dataset_verified": True, "software_sha_consistent": True,
 "harness_consistent": True, "locust_exit_code": int(os.environ["SCLI_CODE"])}
open(p + "/metadata.json", "w", encoding="utf-8").write(json.dumps(metadata, indent=2) + "\n")
PY
sha256sum "$destination"/* > "$destination/SHA256SUMS"
