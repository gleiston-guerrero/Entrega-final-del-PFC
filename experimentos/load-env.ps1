# Dot-source this script. Parses literal KEY=VALUE entries, never executes env content.
param([string]$Path = (Join-Path $PSScriptRoot '../env'))
$allowed = @('RESERVAS_DB_USERNAME', 'RESERVAS_DB_PASSWORD', 'RESERVAS_JDBC_URL',
             'RESERVAS_PANDAS_URL', 'POSTGRES_JDBC_JAR', 'JAVA_HOME', 'HADOOP_HOME')
foreach ($line in [System.IO.File]::ReadAllLines((Resolve-Path -LiteralPath $Path))) {
    if ($line -match '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$') {
        $name = $Matches[1]
        $value = $Matches[2].Trim()
        if ($name -notin $allowed) { continue }
        if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'")))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}
Remove-Variable line, name, value -ErrorAction SilentlyContinue
if ($env:JAVA_HOME) { $env:PATH = "$env:JAVA_HOME\bin;$env:PATH" }
if ($env:HADOOP_HOME) { $env:PATH = "$env:HADOOP_HOME\bin;$env:PATH" }
