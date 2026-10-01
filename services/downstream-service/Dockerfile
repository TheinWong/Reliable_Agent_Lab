FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml .
RUN mvn -B -ntp dependency:go-offline
COPY src src
RUN mvn -B -ntp verify

FROM eclipse-temurin:21-jre
WORKDIR /app
RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
ARG OTEL_JAVA_AGENT_VERSION=2.31.1
RUN curl --fail --silent --show-error --location \
      "https://repo.maven.apache.org/maven2/io/opentelemetry/javaagent/opentelemetry-javaagent/${OTEL_JAVA_AGENT_VERSION}/opentelemetry-javaagent-${OTEL_JAVA_AGENT_VERSION}.jar" \
      --output /app/opentelemetry-javaagent.jar \
    && echo "bbf83c151b6400709e2f225bdd07a04f839d9d13b8b93464241333fd25d3e3ba  /app/opentelemetry-javaagent.jar" | sha256sum --check
RUN useradd --system --uid 10001 appuser
COPY --from=build /workspace/target/downstream-service-*.jar app.jar
USER appuser
EXPOSE 8080
ENTRYPOINT ["java", "-javaagent:/app/opentelemetry-javaagent.jar", "-jar", "/app/app.jar"]
