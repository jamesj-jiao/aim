import signal
import sys
import click

from aim.engine.aim_container import AimContainer
from aim.engine.configs import AIM_CONTAINER_DEFAULT_PORT


@click.group()
@click.pass_obj
def view_entry_point(repo):
    if repo is None:
        click.echo('Repository does not exist')
        exit()

    if not AimContainer.is_docker_installed():
        click.echo('Oops! You don\'t have docker installed. ' +
                   'AimBoard needs docker to run. Please install docker.')
        exit()


@view_entry_point.command()
@click.option('--dev', is_flag=True)
@click.option('-p', '--port', default=AIM_CONTAINER_DEFAULT_PORT, type=int)
@click.option('-v', '--version', default='latest', type=str)
@click.pass_obj
def up(repo, dev, port, version):
    cont = AimContainer(repo, dev=dev)

    click.echo(
        click.style('Running board on repo `{}`'.format(repo), fg='yellow'))

    # Check if image exist
    if not cont.image_exist(version):
        click.echo('Pulling aim board image, please wait...')
        if not cont.pull(version):
            click.echo('An error occurred. If you don\'t have access to ' +
                       'board docker image, please share you DockerID ' +
                       'with AimHub to get access and continue ' +
                       'tracking your ML experiments.')
            click.echo('    (use "docker login" for authentication)')
            return
        else:
            click.echo('Successfully pulled aim board image')

    if cont.get_container(running_only=True):
        kill = click.confirm('Board is already running. ' +
                             'Do you want to restart it?')
        if not kill:
            return

    # Kill all identical running containers
    cont.kill()

    # Run container
    if not cont.up(port, version):
        click.echo('Failed to run aim board.')
        click.echo(('    Please check if port {c} is ' +
                    'accessible.').format(c=port))
        return

    # Implement SIGINT signal handler to kill container after
    # keyboard interruption
    def signal_handler(sig, frame):
        click.echo('')
        click.echo('Shutting down...')
        try:
            cont.kill()
        except Exception:
            pass
        click.echo('Shutdown')
        sys.exit(0)

    # Add keyboard signal interruption listener
    signal.signal(signal.SIGINT, signal_handler)

    click.echo('Open http://127.0.0.1:{}'.format(port))
    click.echo('Press Ctrl+C to exit')

    # Wait for signal
    signal.pause()


@view_entry_point.command()
@click.pass_obj
def down(repo):
    cont = AimContainer(repo)

    # Kill all identical running containers
    cont.kill()


@view_entry_point.command()
@click.pass_obj
def upgrade(repo):
    cont = AimContainer(repo)

    click.echo('Pulling latest aim board release')

    update = cont.pull()
    if update:
        click.echo('Done')
    else:
        click.echo('An error occurred')
        click.echo('    (use "docker login" for authentication)')


@view_entry_point.command()
@click.option('-v', '--version', required=True, type=str)
@click.pass_obj
def pull(repo, version):
    cont = AimContainer(repo)

    click.echo('Pulling aim board v{}'.format(version))

    update = cont.pull(version)
    if update:
        click.echo('Done')
    else:
        click.echo('An error occurred')
        click.echo('    (use "docker login" for authentication)')
