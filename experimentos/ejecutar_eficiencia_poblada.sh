#!/usr/bin/env bash
# Evidencia real para #32; no genera resultados derivados ni altera raws previos.
set -euo pipefail

scenario="eficiencia_nominal_50u_5m_poblada"
mode="official"; repetition=""; host=""; evidence_root=""; duration="5m"; planned_duration_seconds=300
# Tolerancia explícita para el cierre normal de Locust y la toma de timestamps.
duration_tolerance_seconds=5
while (($#)); do case "$1" in
  --smoke) mode="smoke"; shift;; --repetition) repetition="$2"; shift 2;;
  --host) host="$2"; shift 2;; --evidence-root) evidence_root="$2"; shift 2;;
  *) echo "Argumento desconocido: $1" >&2; exit 2;; esac; done
[[ "$host" =~ ^https?:// ]] || { echo '--host es obligatorio' >&2; exit 2; }
if [[ "$mode" == official ]]; then [[ "$repetition" =~ ^([1-9]|10)$ ]] || { echo '--repetition 1..10 es obligatorio' >&2; exit 2; }; fi
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
evidence_root="${evidence_root:-$root/experimentos/resultados/raw}"
runtime_containers=(
  scli-prod-api-gateway-1
  scli-prod-auth-service-1
  scli-prod-usuarios-service-1
  scli-prod-academico-laboratorios-service-1
  scli-prod-reservas-solicitudes-service-1
)

# Lee el runtime, nunca el compose del checkout. Además de producir evidencia,
# deja en deployed_software_sha el único SHA de 40 hex admitido para los cinco.
capture_runtime_deployment() {
  local output="$1" container image image_id project working_dir config_files sha
  local -a shas=()
  : > "$output"
  for container in "${runtime_containers[@]}"; do
    if ! docker inspect "$container" >/dev/null 2>&1; then
      echo "Contenedor runtime ausente: $container" >&2
      return 1
    fi
    image="$(docker inspect --format '{{.Config.Image}}' "$container")"
    image_id="$(docker inspect --format '{{.Image}}' "$container")"
    project="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' "$container")"
    working_dir="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' "$container")"
    config_files="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}' "$container")"
    if [[ ! "$image" =~ :([[:xdigit:]]{40})$ ]]; then
      echo "La imagen runtime no termina en SHA Git de 40 hex: $container = $image" >&2
      return 1
    fi
    sha="${BASH_REMATCH[1],,}"
    shas+=("$sha")
    printf 'container=%s\nConfig.Image=%s\nImage ID=%s\ncompose project=%s\ncompose working_dir=%s\ncompose config_files=%s\n\n' \
      "$container" "$image" "$image_id" "$project" "$working_dir" "$config_files" >> "$output"
  done
  deployed_software_sha="${shas[0]}"
  for sha in "${shas[@]}"; do
    [[ "$sha" == "$deployed_software_sha" ]] || {
      echo "Los contenedores runtime tienen SHA Git diferentes" >&2; return 1;
    }
  done
}
preflight="$evidence_root/$scenario/preflight"
destination="$evidence_root/$scenario/rep-$(printf '%02d' "${repetition:-1}")"
[[ "$mode" == smoke ]] && destination="$evidence_root/${scenario}_smoke/run-01"
if [[ "$mode" == smoke ]]; then duration="1m"; planned_duration_seconds=60; fi
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
dataset_verified=true
curl --fail --silent --show-error "$host/actuator/health" > "$preflight/gateway-health.json"
login="$(curl --fail --silent --show-error -H 'Content-Type: application/json' -d "{\"username\":\"${LOCUST_USERNAME:?}\",\"password\":\"${LOCUST_PASSWORD:?}\"}" "$host/api/v1/auth/login")"
token="$(python3 -c 'import json,sys; x=json.load(sys.stdin); assert isinstance(x.get("accessToken"),str) and x["accessToken"]; print(x["accessToken"])' <<< "$login")"
curl --fail --silent --show-error -H "Authorization: Bearer $token" "$host/api/v1/reservas?pagina=0&tamanio=20" > "$preflight/preflight-reservas-list.json"
reservation_id="$(python3 -c 'import json,sys; x=json.load(sys.stdin); c=x.get("contenido"); assert isinstance(c,list) and c and isinstance(c[0],dict) and c[0].get("id"); print(c[0]["id"])' < "$preflight/preflight-reservas-list.json")"
curl --fail --silent --show-error -H "Authorization: Bearer $token" "$host/api/v1/reservas/$reservation_id" > "$preflight/preflight-reserva-byid.json"
python3 -c 'import json,sys; x=json.load(sys.stdin); assert isinstance(x,dict) and x.get("id")' < "$preflight/preflight-reserva-byid.json"
git -C "$root" rev-parse HEAD > "$preflight/evidence-git-sha.txt"
capture_runtime_deployment "$preflight/deployment-state.txt"
printf '%s\n' "$deployed_software_sha" > "$preflight/deployed-software-sha.txt"
sha256sum "$root/tests/load/locustfile.py" "$root/tests/load/locustfile_e2_correctiva.py" > "$preflight/harness-sha256.txt"
{ date -u --iso-8601=seconds; python3 --version; python3 -m locust --version; } > "$preflight/environment.txt"

mkdir -p "$destination"
cp "$preflight/dataset.csv" "$preflight/dataset-metadata.json" "$destination/"
sha256sum "$destination/dataset.csv" "$destination/dataset-metadata.json" > "$destination/dataset-sha256.txt"
destination_dataset_sha="$(awk '$2=="dataset.csv" {print $1}' "$destination/dataset-sha256.txt")"
[[ "$destination_dataset_sha" == "$expected" ]] || dataset_verified=false
cp "$preflight/evidence-git-sha.txt" "$preflight/deployed-software-sha.txt" "$preflight/harness-sha256.txt" "$destination/"
sha256sum "$root/tests/load/locustfile.py" "$root/tests/load/locustfile_e2_correctiva.py" > "$destination/harness-before-sha256.txt"
cmp -s "$destination/harness-sha256.txt" "$destination/harness-before-sha256.txt" || { echo 'Harness cambió antes de iniciar Locust' >&2; exit 2; }
capture_runtime_deployment "$destination/deployment-before.txt"
before_software_sha="$deployed_software_sha"
start="$(date -u +%s)"; date -u --iso-8601=seconds > "$destination/start_utc.txt"; echo "$start" > "$destination/start_epoch.txt"
export LOCUST_REQUEST_LOG="$destination/locust_requests.csv" LOCUST_FINAL_STATS="$destination/locust-final-stats.json"
set +e
python3 -m locust -f "$root/tests/load/locustfile_e2_correctiva.py" --headless --host "$host" --users 50 --spawn-rate 10 --run-time "$duration" --csv "$destination/locust" --csv-full-history --html "$destination/locust-report.html" > "$destination/locust.log" 2>&1
code=$?; end="$(date -u +%s)"; date -u --iso-8601=seconds > "$destination/end_utc.txt"; echo "$end" > "$destination/end_epoch.txt"; elapsed_seconds=$((end-start)); echo "$elapsed_seconds" > "$destination/elapsed-seconds.txt"; echo "$code" > "$destination/locust-exit-code.txt"
set -e
harness_consistent=false
if sha256sum "$root/tests/load/locustfile.py" "$root/tests/load/locustfile_e2_correctiva.py" > "$destination/harness-after-sha256.txt"; then
  cmp -s "$destination/harness-before-sha256.txt" "$destination/harness-after-sha256.txt" && harness_consistent=true
else
  # No se pierde la repetición si el harness desaparece/cambia tras Locust.
  : > "$destination/harness-after-sha256.txt"
fi
deployment_after_valid=false
after_software_sha=""
if capture_runtime_deployment "$destination/deployment-after.txt"; then
  deployment_after_valid=true
  after_software_sha="$deployed_software_sha"
fi
software_sha_consistent=false
[[ "$deployment_after_valid" == true && "$before_software_sha" == "$after_software_sha" && "$before_software_sha" == "$(<"$preflight/deployed-software-sha.txt")" ]] && software_sha_consistent=true
duration_completed=false
[[ "$elapsed_seconds" -ge $((planned_duration_seconds - duration_tolerance_seconds)) ]] && duration_completed=true
evidence_complete=true
for evidence_file in \
  locust_requests.csv \
  locust-final-stats.json \
  locust_stats.csv \
  locust.log \
  start_utc.txt \
  end_utc.txt \
  start_epoch.txt \
  end_epoch.txt \
  elapsed-seconds.txt \
  locust-exit-code.txt \
  deployment-before.txt \
  deployment-after.txt \
  evidence-git-sha.txt \
  deployed-software-sha.txt \
  harness-sha256.txt \
  harness-before-sha256.txt \
  harness-after-sha256.txt \
  dataset-sha256.txt \
  dataset.csv \
  dataset-metadata.json; do
  [[ -s "$destination/$evidence_file" ]] || evidence_complete=false
done
SCLI_DESTINATION="$destination" SCLI_SCENARIO="$scenario" SCLI_REPETITION="${repetition:-0}" SCLI_MODE="$mode" SCLI_DURATION="$duration" SCLI_DURATION_SECONDS="$planned_duration_seconds" SCLI_ELAPSED_SECONDS="$elapsed_seconds" SCLI_CODE="$code" SCLI_EVIDENCE_GIT_SHA="$(<"$preflight/evidence-git-sha.txt")" SCLI_DEPLOYED_SOFTWARE_SHA="$(<"$preflight/deployed-software-sha.txt")" SCLI_DATASET_VERIFIED="$dataset_verified" SCLI_DURATION_COMPLETED="$duration_completed" SCLI_EVIDENCE_COMPLETE="$evidence_complete" SCLI_SOFTWARE_SHA_CONSISTENT="$software_sha_consistent" SCLI_DEPLOYMENT_AFTER_VALID="$deployment_after_valid" SCLI_HARNESS_CONSISTENT="$harness_consistent" python3 - <<'PY'
import json, os
p = os.environ["SCLI_DESTINATION"]
metadata = {"scenario": os.environ["SCLI_SCENARIO"], "repetition": int(os.environ["SCLI_REPETITION"]),
 "mode": os.environ["SCLI_MODE"], "evidence_git_sha": os.environ["SCLI_EVIDENCE_GIT_SHA"],
 "deployed_software_sha": os.environ["SCLI_DEPLOYED_SOFTWARE_SHA"],
 "planned_duration": os.environ["SCLI_DURATION"], "planned_duration_seconds": int(os.environ["SCLI_DURATION_SECONDS"]),
 "elapsed_seconds": int(os.environ["SCLI_ELAPSED_SECONDS"]),
 "duration_completed": os.environ["SCLI_DURATION_COMPLETED"] == "true",
 "evidence_complete": os.environ["SCLI_EVIDENCE_COMPLETE"] == "true",
 "dataset_verified": os.environ["SCLI_DATASET_VERIFIED"] == "true",
 "software_sha_consistent": os.environ["SCLI_SOFTWARE_SHA_CONSISTENT"] == "true",
 "deployment_after_valid": os.environ["SCLI_DEPLOYMENT_AFTER_VALID"] == "true",
 "harness_consistent": os.environ["SCLI_HARNESS_CONSISTENT"] == "true",
 "locust_exit_code": int(os.environ["SCLI_CODE"])}
open(p + "/metadata.json", "w", encoding="utf-8").write(json.dumps(metadata, indent=2) + "\n")
PY
sha256sum "$destination"/* > "$destination/SHA256SUMS"
