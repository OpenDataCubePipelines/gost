import click

from ._shared_commands import io_dir_options, db_query_options


@click.command()
@io_dir_options
def plotting(
    outdir,
):
    """
    Using the framing geometry, plot the results of the intercomparison evaluation.
    """
