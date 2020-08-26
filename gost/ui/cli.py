import click

# from gost.commands import comparison, merge, pbs, plotting, query, summarise
from .commands import comparison, merge, pbs, plotting, query, summarise
# from .. import scripts
# from gost.scripts import comparison, merge, pbs, plotting, query, summarise

@click.group()
def entry_point():
    """
    Entry point for the whole command module.
    """
    pass


entry_point.add_command(comparison.comparison)
entry_point.add_command(merge.merge)
entry_point.add_command(pbs.pbs)
entry_point.add_command(plotting.plotting)
entry_point.add_command(query.query)
entry_point.add_command(query.query_filesystem)
entry_point.add_command(summarise.summarise)
