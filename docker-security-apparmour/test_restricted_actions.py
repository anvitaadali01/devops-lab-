import time

import docker

IMAGE_NAME = 'flask-apparmor'
PROFILE_NAME = 'my-apparmor-profile'


client = docker.from_env()

print('Starting container with AppArmor profile...')
container = client.containers.run(
    IMAGE_NAME,
    ports={'5000/tcp': 5000},
    detach=True,
    security_opt=[f'apparmor={PROFILE_NAME}'],
)

try:
    time.sleep(3)

    commands = [
        ('Attempt to read /etc/passwd', 'cat /etc/passwd'),
        ('Attempt to execute /bin/bash', '/bin/bash'),
    ]

    for label, command in commands:
        exit_code, output = container.exec_run(command)
        print(f'{label}: Exit Code {exit_code}, Output: {output.decode(errors="replace").strip()}')
finally:
    print('Stopping the container...')
    container.stop()
    print('Container stopped')
