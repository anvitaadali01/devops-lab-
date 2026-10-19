import os
import sys
import time
from pathlib import Path

import docker

IMAGE_NAME = 'flask-apparmor'
PROFILE_NAME = 'my-apparmor-profile'


def main():
    client = docker.from_env()

    if os.name != 'posix' or sys.platform.startswith('win'):
        print('AppArmor is not supported on Docker Desktop for Windows hosts. Run this lab inside a Linux VM or Linux Docker host.')
        return 1

    profile_path = Path('/etc/apparmor.d') / PROFILE_NAME
    if not profile_path.exists():
        print(f'AppArmor profile is missing at {profile_path}. Copy the project file to that path before running on Linux.')
        return 1

    print('Building image from Dockerfile...')
    client.images.build(path='.', tag=IMAGE_NAME)

    print('Running container with AppArmor profile...')
    container = client.containers.run(
        IMAGE_NAME,
        ports={'5000/tcp': 5000},
        detach=True,
        security_opt=[f'apparmor={PROFILE_NAME}'],
    )

    time.sleep(3)
    container.reload()
    security_options = container.attrs.get('HostConfig', {}).get('SecurityOpt', [])

    print(f'Container started: {container.short_id}')
    print(f'AppArmor profile applied: {security_options}')

    if not any(f'apparmor={PROFILE_NAME}' in item for item in security_options):
        raise RuntimeError('AppArmor profile was not applied to the container.')

    print('Verifying HTTP endpoint on localhost:5000...')
    try:
        exec_result = container.exec_run('python -c "import urllib.request; print(urllib.request.urlopen(\'http://127.0.0.1:5000\').read().decode())"')
        exit_code, output = exec_result
        print(f'HTTP verification exit code: {exit_code}')
        print(output.decode(errors='replace').strip())
    except Exception as exc:
        print(f'HTTP verification failed: {exc}')

    print('Stopping the container...')
    container.stop()
    print('Container stopped')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
