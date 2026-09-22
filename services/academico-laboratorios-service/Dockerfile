# =====================================================================
# ETAPA 1: build (compila el proyecto con Maven y genera el .jar)
# =====================================================================
FROM maven:3.9-eclipse-temurin-21-alpine AS build

WORKDIR /app

# Se copia primero el pom.xml para aprovechar el cache de capas de Docker:
# si no cambian las dependencias, Docker no las vuelve a descargar
# en builds posteriores aunque cambie el código fuente.
COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src/ src/

RUN mvn clean package -Dmaven.test.skip=true -B

# =====================================================================
# ETAPA 2: runtime (imagen final, liviana, solo con el JRE y el .jar)
# =====================================================================
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Usuario no root, por seguridad
RUN addgroup -S scli && adduser -S scli -G scli

COPY --from=build /app/target/*.jar app.jar

RUN chown scli:scli app.jar
USER scli

EXPOSE 8083

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8083/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
