#!/usr/bin/env bash
# Launcher nativo para la campaña correctiva E2 en Ubuntu 24.04.
set -uo pipefail

scenario=""
repetition=""
attempt="1"
target_host=""
prometheus_url="http://localhost:9090"
compose_file="docker-compose.yml"
evidence_root=""
dry_run=false

while (($#)); do
  case "$1" in
    --scenario) scenario="$2"; shift 2 ;;
    --repetition) repetition="$2"; shift 2 ;;
    --attempt) attempt="$2"; shift 2 ;;
    --host) target_host="$2"; shift 2 ;;
    --prometheus-url) prometheus_url="$2"; shift 2 ;;
    --compose-file) compose_file="$2"; shift 2 ;;
    --evidence-root) evidence_root="$2"; shift 2 ;;
    --dry-run) dry_run=true; shift ;;
    *) echo "Argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

corrective="fiabilidad_nominal_50u_1h_refresh"
[[ "$scenario" == "$corrective" ]] || { echo "Sólo se admite $corrective" >&2; exit 2; }
[[ "$repetition" =~ ^([1-9]|10)$ ]] || { echo "--repetition debe estar entre 1 y 10" >&2; exit 2; }
[[ "$attempt" =~ ^[1-9][0-9]*$ ]] || { echo "--attempt debe ser mayor o igual que 1" >&2; exit 2; }
[[ "$target_host" =~ ^https?:// ]] || { echo "--host debe ser HTTP(S)" >&2; exit 2; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd "$script_dir/.." && pwd)"
compose_path="$repository_root/$compose_file"
[[ -n "$evidence_root" ]] || evidence_root="$script_dir/resultados/raw"
python_command="$(command -v python3 || command -v python || true)"
[[ -n "$python_command" ]] || { echo "No se encontró Python 3" >&2; exit 2; }
mkdir -p "$evidence_root"
evidence_root="$(cd "$evidence_root" && pwd)"
printf -v repetition_name 'rep-%02d' "$repetition"
if [[ "$attempt" -gt 1 ]]; then
  printf -v repetition_name 'rep-%02d-attempt-%02d' "$repetition" "$attempt"
fi
if $dry_run; then
  evidence_dir="$evidence_root/_dry-run/$scenario/$repetition_name"
else
  evidence_dir="$evidence_root/$scenario/$repetition_name"
fi
if [[ -e "$evidence_dir" && ! -d "$evidence_dir" ]]; then
  echo "La ruta de evidencia existe y no es un directorio: $evidence_dir" >&2
  exit 2
fi
if [[ -d "$evidence_dir" && -n "$(find "$evidence_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  echo "El directorio de evidencia ya contiene archivos: $evidence_dir" >&2
  exit 2
fi
if ! $dry_run && [[ "$attempt" -gt 1 ]]; then
  previous_attempt=$((attempt - 1))
  if [[ "$previous_attempt" -eq 1 ]]; then
    printf -v previous_name 'rep-%02d' "$repetition"
  else
    printf -v previous_name 'rep-%02d-attempt-%02d' "$repetition" "$previous_attempt"
  fi
  previous_metadata="$evidence_root/$scenario/$previous_name/metadata.json"
  [[ -f "$previous_metadata" ]] || {
    echo "No existe metadata del intento anterior: $previous_metadata" >&2; exit 2;
  }
  "$python_command" -c 'import json,sys; data=json.load(open(sys.argv[1],encoding="utf-8-sig")); expected_rep=int(sys.argv[2]); expected_attempt=int(sys.argv[3]); valid=data.get("repetition")==expected_rep and data.get("attempt",1)==expected_attempt and data.get("execution_completed") is not True; raise SystemExit(0 if valid else 1)' \
    "$previous_metadata" "$repetition" "$previous_attempt" || {
      echo "El intento anterior no consta como intento inválido auditable" >&2; exit 2;
    }
fi
git_sha="$(git -C "$repository_root" rev-parse HEAD)"
git_branch="$(git -C "$repository_root" symbolic-ref --quiet --short HEAD || printf 'detached@%s' "${git_sha:0:7}")"
git_experiment_status() {
  local relative_prefix=""
  if [[ "$evidence_root" == "$repository_root"/* ]]; then
    relative_prefix="${evidence_root#"$repository_root"/}/$scenario/"
  fi
  git -C "$repository_root" status --porcelain --untracked-files=all | awk \
    -v prefix="$relative_prefix" 'prefix == "" || index(substr($0, 4), prefix) != 1'
}
git_status_before="$(git_experiment_status)"
if ! $dry_run && [[ -n "$git_status_before" ]]; then
  echo "La campaña correctiva exige un árbol Git limpio antes de ejecutar." >&2
  exit 2
fi

locust_version=""
if ! $dry_run; then
  for required_command in git docker curl date; do
    command -v "$required_command" >/dev/null || {
      echo "Falta el comando requerido: $required_command" >&2; exit 2;
    }
  done
  docker compose version >/dev/null 2>&1 || {
    echo "Docker Compose no está disponible" >&2; exit 2;
  }
  [[ -n "${LOCUST_USERNAME:-}" && -n "${LOCUST_PASSWORD:-}" ]] || {
    echo "LOCUST_USERNAME y LOCUST_PASSWORD son obligatorios" >&2; exit 2;
  }
  [[ -f "$compose_path" ]] || { echo "No existe $compose_path" >&2; exit 2; }
  date -u -d '@0' +%s >/dev/null 2>&1 || {
    echo "date no admite la conversión UTC requerida (-d @epoch)" >&2; exit 2;
  }
  locust_version="$($python_command -m locust --version 2>&1)" || {
    echo "Locust no está disponible en $python_command" >&2; exit 2;
  }
  for service in api-gateway reservas-solicitudes-service; do
    service_id="$(docker compose -f "$compose_path" ps -q "$service" 2>/dev/null)"
    [[ -n "$service_id" ]] || {
      echo "El servicio Compose $service no está accesible" >&2; exit 2;
    }
  done
  curl --fail --silent --show-error "$prometheus_url/-/healthy" >/dev/null || {
    echo "Prometheus no está accesible" >&2; exit 2;
  }
  curl --fail --silent --show-error "$target_host/actuator/health" >/dev/null || {
    echo "API Gateway no está accesible" >&2; exit 2;
  }
fi

# La repetición se reserva únicamente después de superar todo el preflight.
mkdir -p "$evidence_dir"

users=50
spawn_rate=10
duration="1h"
duration_seconds=3600
csv_prefix="$evidence_dir/locust"
locust_log="$evidence_dir/locust.log"
locust_command=("$python_command" -m locust -f "$repository_root/tests/load/locustfile_e2_correctiva.py"
  --headless --host "$target_host" --users "$users" --spawn-rate "$spawn_rate"
  --run-time "$duration" --csv "$csv_prefix" --csv-full-history
  --html "$evidence_dir/locust-report.html")

job="reservas-solicitudes-service"
gateway_job="api-gateway"
five_xx_count="sum(increase(http_server_requests_seconds_count{job=\"$job\",status=~\"5..\"}[1h]))"
five_xx_percent="100 * sum(increase(http_server_requests_seconds_count{job=\"$job\",status=~\"5..\"}[1h])) / clamp_min(sum(increase(http_server_requests_seconds_count{job=\"$job\"}[1h])), 1)"
p95="1000 * histogram_quantile(0.95, sum by (le) (increase(http_request_duration_seconds_bucket{job=\"$job\"}[1h])))"
gateway_status="sum by (job, method, uri, status) (http_server_requests_seconds_count{job=\"$gateway_job\"})"
reservas_status="sum by (job, method, uri, status) (http_server_requests_seconds_count{job=\"$job\"})"
printf '%s\n' "$five_xx_count" > "$evidence_dir/prometheus-5xx-count.promql"
printf '%s\n' "$five_xx_percent" > "$evidence_dir/prometheus-5xx-percent.promql"
printf '%s\n' "$p95" > "$evidence_dir/prometheus-p95.promql"
printf '%s\n' "$gateway_status" > "$evidence_dir/prometheus-gateway-status-by-uri.promql"
printf '%s\n' "$reservas_status" > "$evidence_dir/prometheus-reservas-status-by-uri.promql"

command_display="$(printf '%q ' "${locust_command[@]}")"
export SCLI_METADATA_PATH="$evidence_dir/metadata.json"
export SCLI_SCENARIO="$scenario" SCLI_REPETITION="$repetition" SCLI_HOST="$target_host"
export SCLI_ATTEMPT="$attempt"
export SCLI_PROMETHEUS="$prometheus_url" SCLI_USERS="$users" SCLI_SPAWN="$spawn_rate"
export SCLI_COMMAND="$command_display" SCLI_GIT_BRANCH="$git_branch" SCLI_GIT_SHA="$git_sha"
export SCLI_DRY_RUN="$dry_run"
"$python_command" - <<'PY'
import json, os, platform
from datetime import datetime, timezone
metadata = {
    "status": "dry-run" if os.environ.get("SCLI_DRY_RUN") == "true" else "planned",
    "precheck": False, "official": True,
    "scenario": os.environ["SCLI_SCENARIO"], "repetition": int(os.environ["SCLI_REPETITION"]),
    "attempt": int(os.environ["SCLI_ATTEMPT"]),
    "host": os.environ["SCLI_HOST"], "prometheus_url": os.environ["SCLI_PROMETHEUS"],
    "users": int(os.environ["SCLI_USERS"]), "spawn_rate": int(os.environ["SCLI_SPAWN"]),
    "planned_duration": "1h", "planned_duration_seconds": 3600,
    "command": os.environ["SCLI_COMMAND"], "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "git_branch": os.environ["SCLI_GIT_BRANCH"], "git_sha": os.environ["SCLI_GIT_SHA"],
    "git_worktree_clean_before": True, "git_status_before": "",
    "python_version": platform.python_version(), "locust_version": None,
    "deployment_fingerprint_before": None, "deployment_fingerprint_after": None,
    "environment_consistent": False, "started_at_utc": None, "finished_at_utc": None,
    "elapsed_seconds": None, "locust_exit_code": None, "duration_completed": False,
    "reservas_log_capture_succeeded": False, "reservas_log_content_length": None,
    "gateway_log_capture_succeeded": False, "gateway_log_content_length": None,
    "execution_completed": False, "evidence_complete": False, "launcher_error": None,
}
with open(os.environ["SCLI_METADATA_PATH"], "w", encoding="utf-8") as stream:
    json.dump(metadata, stream, indent=2, ensure_ascii=False); stream.write("\n")
PY

echo "Evidencia: $evidence_dir"
echo "Comando: $command_display"
if $dry_run; then
  echo "DRY-RUN: no se ejecutó Locust ni se modificó ningún resultado."
  exit 0
fi

fingerprint() {
  local ids id
  ids="$(docker compose -f "$compose_path" ps -q)"
  [[ -n "$ids" ]] || return 1
  for id in $ids; do docker inspect --format '{{.Id}} {{.Config.Image}} {{.Image}}' "$id"; done | sort
}
prom_query() {
  local query="$1" epoch="$2" output="$3"
  curl --fail --silent --show-error --get "$prometheus_url/api/v1/query" \
    --data-urlencode "query=$query" --data-urlencode "time=$epoch" > "$output"
}
prom_range() {
  local query="$1" start="$2" end="$3" output="$4"
  curl --fail --silent --show-error --get "$prometheus_url/api/v1/query_range" \
    --data-urlencode "query=$query" --data-urlencode "start=$start" \
    --data-urlencode "end=$end" --data-urlencode "step=15" > "$output"
}
metadata_patch() {
  local payload="$1"
  SCLI_PATCH="$payload" "$python_command" - <<'PY'
import json, os
path = os.environ["SCLI_METADATA_PATH"]
with open(path, encoding="utf-8-sig") as stream: data = json.load(stream)
data.update(json.loads(os.environ["SCLI_PATCH"]))
with open(path, "w", encoding="utf-8") as stream:
    json.dump(data, stream, indent=2, ensure_ascii=False); stream.write("\n")
PY
}

deployment_before="$(fingerprint)" || { echo "No se pudo identificar el despliegue" >&2; exit 2; }
printf '%s\n' "$deployment_before" > "$evidence_dir/deployment-state-before.txt"
curl --fail --silent --show-error "$prometheus_url/-/healthy" > "$evidence_dir/prometheus-health-before.txt" || exit 2
curl --fail --silent --show-error "$target_host/actuator/health" > "$evidence_dir/gateway-health-before.json" || exit 2
docker compose -f "$compose_path" ps --format json reservas-solicitudes-service > "$evidence_dir/reservas-health-before.json" || exit 2
docker stats --no-stream > "$evidence_dir/docker-stats-before.txt" || exit 2
docker compose -f "$compose_path" ps --format json crdb-e3-1 crdb-e3-2 crdb-e3-3 > "$evidence_dir/cockroach-containers-before.txt" || exit 2
printf 'git_branch=%s\ngit_sha=%s\nhost=%s\nprometheus_url=%s\npython=%s\nlocust=%s\nos=%s\n' \
  "$git_branch" "$git_sha" "$target_host" "$prometheus_url" "$($python_command --version)" \
  "$locust_version" "$(uname -a)" > "$evidence_dir/environment.txt"

start_epoch="$(date -u +%s.%N)"
start_iso="$($python_command -c 'import sys; from datetime import datetime,timezone; print(datetime.fromtimestamp(float(sys.argv[1]),timezone.utc).isoformat())' "$start_epoch")"
export LOCUST_REQUEST_LOG="$evidence_dir/locust_requests.csv"
export LOCUST_FINAL_STATS="$evidence_dir/locust-final-stats.json"
metadata_patch "{\"status\":\"running\",\"started_at_utc\":\"$start_iso\",\"locust_version\":$("$python_command" -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$locust_version"),\"deployment_fingerprint_before\":$("$python_command" -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$deployment_before")}"

set +e
"${locust_command[@]}" > "$locust_log" 2>&1
locust_exit_code=$?
finish_epoch="$(date -u +%s.%N)"
finish_iso="$($python_command -c 'import sys; from datetime import datetime,timezone; print(datetime.fromtimestamp(float(sys.argv[1]),timezone.utc).isoformat())' "$finish_epoch")"
elapsed="$($python_command -c 'import sys; print(float(sys.argv[2])-float(sys.argv[1]))' "$start_epoch" "$finish_epoch")"

prom_query "$five_xx_count" "$finish_epoch" "$evidence_dir/prometheus-5xx-result.txt"
prom_query "$five_xx_percent" "$finish_epoch" "$evidence_dir/prometheus-5xx-percent-result.txt"
prom_query "$p95" "$finish_epoch" "$evidence_dir/prometheus-p95-result.txt"
prom_range "$gateway_status" "$start_epoch" "$finish_epoch" "$evidence_dir/prometheus-gateway-status-by-uri-result.json"
prom_range "$reservas_status" "$start_epoch" "$finish_epoch" "$evidence_dir/prometheus-reservas-status-by-uri-result.json"
curl --fail --silent --show-error "$prometheus_url/-/healthy" > "$evidence_dir/prometheus-health-after.txt"
curl --fail --silent --show-error "$target_host/actuator/health" > "$evidence_dir/gateway-health-after.json"
docker compose -f "$compose_path" ps --format json reservas-solicitudes-service > "$evidence_dir/reservas-health-after.json"
docker stats --no-stream > "$evidence_dir/docker-stats-after.txt"
docker compose -f "$compose_path" ps --format json crdb-e3-1 crdb-e3-2 crdb-e3-3 > "$evidence_dir/cockroach-containers-after.txt"
docker compose -f "$compose_path" logs --no-color --since "$start_iso" --until "$finish_iso" api-gateway > "$evidence_dir/gateway-service.log" 2>&1
gateway_log_exit=$?
docker compose -f "$compose_path" logs --no-color --since "$start_iso" --until "$finish_iso" reservas-solicitudes-service > "$evidence_dir/reservas-service.log" 2>&1
reservas_log_exit=$?
deployment_after="$(fingerprint)"
printf '%s\n' "$deployment_after" > "$evidence_dir/deployment-state-after.txt"
"$python_command" -c 'import json,sys; from datetime import datetime,timezone; start=float(sys.argv[3]); finish=float(sys.argv[4]); split=start+900.0; json.dump({"started_at_utc":sys.argv[1],"split_at_seconds":900,"split_at_utc":datetime.fromtimestamp(split,timezone.utc).isoformat(),"finished_at_utc":sys.argv[2],"start_epoch":start,"split_epoch":split,"finish_epoch":finish},open(sys.argv[5],"w",encoding="utf-8"),indent=2)' \
  "$start_iso" "$finish_iso" "$start_epoch" "$finish_epoch" "$evidence_dir/phase-boundaries.json"

git_sha_after="$(git -C "$repository_root" rev-parse HEAD)"
git_status_after="$(git_experiment_status)"
environment_consistent=false
[[ "$git_sha_after" == "$git_sha" && "$git_status_after" == "$git_status_before" && "$deployment_after" == "$deployment_before" ]] && environment_consistent=true
duration_completed=false
"$python_command" -c 'import sys; raise SystemExit(0 if float(sys.argv[1]) >= 3595 else 1)' "$elapsed" \
  && [[ -s "$evidence_dir/locust_stats.csv" ]] && duration_completed=true
reservas_log_ok=false; [[ "$reservas_log_exit" -eq 0 ]] && reservas_log_ok=true
gateway_log_ok=false; [[ "$gateway_log_exit" -eq 0 ]] && gateway_log_ok=true
metadata_patch "{\"finished_at_utc\":\"$finish_iso\",\"elapsed_seconds\":$elapsed,\"locust_exit_code\":$locust_exit_code,\"duration_completed\":$duration_completed,\"environment_consistent\":$environment_consistent,\"git_sha_after\":\"$git_sha_after\",\"deployment_fingerprint_after\":$("$python_command" -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$deployment_after"),\"reservas_log_capture_succeeded\":$reservas_log_ok,\"reservas_log_content_length\":$(wc -c < "$evidence_dir/reservas-service.log"),\"gateway_log_capture_succeeded\":$gateway_log_ok,\"gateway_log_content_length\":$(wc -c < "$evidence_dir/gateway-service.log")}"

cd "$repository_root"
"$python_command" -m experimentos.finalizar_evidencia_iso25010 \
  --evidence-dir "$evidence_dir" --scenario "$scenario" --repetition "$repetition" \
  --attempt "$attempt"
finalizer_exit=$?
echo "Código real de Locust: $locust_exit_code"
if [[ "$finalizer_exit" -eq 0 ]]; then
  echo "Ejecución experimental completada: true"
  exit 0
fi
echo "Ejecución experimental completada: false"
exit 2
