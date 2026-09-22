# Verificación posterior al E3 — Checkstyle

Esta carpeta contiene una verificación posterior al E3 ejecutada sobre el estado actual reproducible del repositorio.

No constituye evidencia histórica contemporánea de E3 y no sustituye la ausencia de artefactos cuantitativos Checkstyle en el paquete E3 original.

## Commit verificado

HEAD:

d8f4d60a566bf493aa3d399474a1363cc25d2eda

## Entorno

- Sistema: Linux
- Java: OpenJDK 17.0.20
- Maven: Apache Maven 3.9.16
- Maven Wrapper utilizado: services/usuarios-service/mvnw

## Usuarios

Servicio:

services/usuarios-service

Comando:

bash ./mvnw checkstyle:check

Resultado:

- Violaciones Checkstyle: 119
- Exit code: 1
- Estado: BUILD FAILURE

Artefacto:

usuarios-checkstyle-result.xml

Configuración:

services/usuarios-service/checkstyle.xml

SHA-256 de la configuración:

80842ef33e5ad4edf0e005887b4c2b380c76586ed9a335c8bfbf20cfa56d0278

## Académico

Servicio:

services/academico-laboratorios-service

Comando:

bash ./services/usuarios-service/mvnw \
  -f services/academico-laboratorios-service/pom.xml \
  checkstyle:check

Resultado:

- Violaciones Checkstyle: 0
- Exit code: 0
- Estado: BUILD SUCCESS

Artefacto:

academico-checkstyle-result.xml

Configuración:

services/academico-laboratorios-service/checkstyle.xml

SHA-256 de la configuración:

36bb6414c7e7c86b2a3a363a5d88406671164c91444303db2fd3af1c522e5d65

## Alcance y limitación histórica

La evidencia histórica E3 no conserva reportes XML/TXT/JSON, conteo de violaciones ni exit code de Checkstyle.

Por esta razón, estos resultados deben interpretarse únicamente como una verificación posterior del estado correspondiente al commit indicado.

No se modificaron los artefactos históricos E3 ni sus manifests.
