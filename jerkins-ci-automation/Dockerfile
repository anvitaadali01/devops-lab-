FROM jenkins/jenkins:lts-jdk21

USER root
RUN apt-get update \
    && apt-get install --yes --no-install-recommends git python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*
USER jenkins
 
