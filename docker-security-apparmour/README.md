# Docker Security with AppArmor and Python

This lab follows the exercise described in the DevOps Lab AppArmor exercise and is designed for a Linux host with AppArmor support.

## Important compatibility note

AppArmor is a Linux security module. It does not run natively on Docker Desktop for Windows. If you are using Docker Desktop on Windows, the simplest working approach is to run the lab inside a Linux VM (for example Ubuntu 22.04 LTS) or on a Linux Docker host.

This repository contains the lab files and the exact Linux steps needed for a supported environment. The AppArmor restrictions themselves were not executed in this Windows host because Windows + Docker Desktop does not provide AppArmor support for the Docker daemon.

## Files in this project

- `app.py` — simple Flask web app
- `Dockerfile` — container definition
- `my-apparmor-profile` — AppArmor policy file
- `apply_apparmor.py` — Docker SDK script to build and run the container with AppArmor
- `test_restricted_actions.py` — validation script for restricted reads and binary execution
- `requirements.txt` — Python dependencies

## 1. Linux environment setup

Run the following commands in a Linux VM or Linux host:

```bash
sudo apt-get update
sudo apt-get install -y apparmor-utils docker.io python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If Docker is not running, start it:

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

## 2. Copy the AppArmor profile to the correct location

```bash
sudo cp my-apparmor-profile /etc/apparmor.d/my-apparmor-profile
sudo apparmor_parser -r /etc/apparmor.d/my-apparmor-profile
```

## 3. Build the container image

```bash
docker build -t flask-apparmor .
```

Expected result: the image builds successfully and the Flask app is available on port 5000 when the container runs.

## 4. Run the container with AppArmor enabled

```bash
docker run --rm -d -p 5000:5000 --security-opt="apparmor=my-apparmor-profile" --name flask-apparmor-demo flask-apparmor
```

Then verify the app:

```bash
curl http://localhost:5000
```

Expected response:

```text
Hello, this is a secure Flask application running inside a Docker container!
```

## 5. Run the Python automation script

```bash
python3 apply_apparmor.py
```

This script:

- builds the Docker image
- starts the container with the AppArmor profile
- inspects the container to confirm HostConfig.SecurityOpt includes AppArmor
- stops the container

## 6. Test restricted operations

```bash
python3 test_restricted_actions.py
```

Expected behavior on a Linux host with a loaded AppArmor profile:

- reading `/etc/passwd` is denied
- executing `/bin/bash` is denied

For demonstration purposes, the script prints the exit code and output for each action.

## Questions and answers

### 1. What is the purpose of using AppArmor with Docker containers?

AppArmor is used to confine container processes to a limited set of files, capabilities, and network access. This helps reduce the impact of a compromise inside a container.

### 2. How do AppArmor profiles help secure a Docker container?

AppArmor profiles define a policy that says what the application may access and what it must be denied. Sensitive directories, unauthorized binaries, and dangerous capabilities can be blocked before they are used.

### 3. Why is it important to restrict access to sensitive directories such as /etc/ and /var/?

These locations contain configuration and system state that should not be exposed to application workloads. Restricting them reduces the risk of data exposure and misuse of host-like dependencies.

### 4. What other capabilities can you restrict using AppArmor profiles?

You can restrict file reads and writes, network access, execution of binaries, and special Linux capabilities such as `sys_admin` and port binding permissions.

### 5. How can you verify if an AppArmor profile is successfully applied to a Docker container?

You can inspect the container with the Docker API or CLI and check `HostConfig.SecurityOpt` for the value `apparmor=my-apparmor-profile`. You can also test denied actions such as reading `/etc/passwd` or running `/bin/bash`.

## Notes for this lab

- The exercise is designed for a Linux machine with AppArmor enabled.
- Docker Desktop for Windows cannot enforce AppArmor natively.
- A Linux VM is the simplest route if you want to complete the AppArmor enforcement step fully.
- The scripts are intentionally simple and suitable for a college DevOps lab.

## Files to upload to GitHub

Upload the complete project directory, including:

- `app.py`
- `Dockerfile`
- `requirements.txt`
- `my-apparmor-profile`
- `apply_apparmor.py`
- `test_restricted_actions.py`
- `README.md`

Do not upload any unrelated files beyond this lab folder.
