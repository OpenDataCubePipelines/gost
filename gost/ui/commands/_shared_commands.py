import json
import click


class JsonType(click.ParamType):
    """
    Custom JSON type for handling interpretation from JSON
    """

    name = "json-dict"

    def convert(self, value, param, ctx):
        return json.loads(value)


def io_dir_options(option):
    """
    Decorator to specify the input/output directories.
    """

    option = click.option(
        "--outdir",
        required=True,
        type=click.Path(dir_okay=True, file_okay=False, writable=True),
        help="The results output directory.",
    )(option)

    return option


def db_query_options(option):
    """
    Decorator to specify the database query options.
    """
    option = click.option(
        "--product-name-test",
        required=True,
        type=click.STRING,
        help="Product name for the test data.",
    )(option)
    option = click.option(
        "--product-name-reference",
        required=True,
        type=click.STRING,
        help="Product name for the reference data.",
    )(option)
    option = click.option(
        "--db-env-test",
        required=True,
        type=click.STRING,
        help="Database environment containing the test data.",
    )(option)
    option = click.option(
        "--db-env-reference",
        required=True,
        type=click.STRING,
        help="Database environment containing the reference data.",
    )(option)
    option = click.option(
        "--time",
        required=True,
        nargs=2,
        type=click.DateTime(formats=["%Y-%m-%d"]),
        help="The time range to query.",
    )(option)
    option = click.option(
        "--lon",
        type=(float, float),
        default=(None, None),
        help="Longitudinal bounds.",
    )(option)
    option = click.option(
        "--lat",
        type=(float, float),
        default=(None, None),
        help="Latitudinal bounds.",
    )(option)
    option = click.option(
        "--additional-filters",
        type=JsonType(),
        default=None,
        help="Additional filters to use in the query. Specify as a JSON dictionary.",
    )(option)

    return option
