"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mpysds011` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``pysds011.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``pysds011.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import click


@click.command()
@click.option('--port', default='/dev/ttyUSB0', help='UART port to communicate with dust sensor.')
@click.argument('names', nargs=-1)
def main(port, names):
    """cli interface to SD011 driver"""
    click.echo(repr(names))
