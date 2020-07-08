"""Console script for derp_me."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for derp_me."""
    click.echo("Replace this message by putting your code into "
               "derp_me.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
