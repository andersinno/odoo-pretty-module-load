import logging
import re
from typing import NamedTuple

import odoo.tools
from odoo.cli.server import Server

from ..module_load_prints import override_logging_for_module_loading

try:
    from click_odoo_contrib.update import _update_db as click_odoo_update
except ImportError:
    click_odoo_update = None

LOG = logging.getLogger(__name__)


class ParsedArgs(NamedTuple):
    odoo_run_args: list[str]
    verbosity: int


class PrettyModuleLoadCommand(Server):
    """Load modules with a pretty progress bar."""

    name = "pretty_module_load"

    def run(self, args):
        modified_args, verbosity = self._parse_args(args)
        odoo.tools.config.parse_config(modified_args)
        db = self._get_database_name()
        has_logfile = bool(odoo.tools.config["logfile"])
        with override_logging_for_module_loading(verbosity, has_logfile, db):
            if has_logfile:
                LOG.info("Running command: %s %s", self.name, " ".join(args))
            self._run_real(modified_args, verbosity)

    def _run_real(self, args: list[str], verbosity: int) -> None:
        super().run(args)

    def _parse_args(self, args: list[str]) -> ParsedArgs:
        verbosity = 1
        modified_args = [
            "--stop-after-init",  # Exit after done with module operations
            "--no-http",  # Prevent server startup
            "--max-cron-threads=0",  # Don't start the cron
        ]

        for arg in args:
            modified_args.append(arg)

            v_match = re.match(r"^(-v{1,9}|-v([0-9]))$", arg)
            if v_match:
                modified_args.pop()
                number_part = v_match.group(2)
                if number_part:
                    verbosity = int(number_part)
                else:
                    verbosity = arg.count("v") + 1

        return ParsedArgs(modified_args, verbosity)

    def _get_database_name(self) -> str:
        db_name = odoo.tools.config["db_name"]
        if not db_name:
            raise SystemExit(
                "Error: No database name given or configured\n\n"
                "Specify either '-d dbname' on the command line or"
                "configure db_name in your odoo.conf."
            )
        return db_name


class ModuleCommandMixin:
    name: str
    module_operation: str
    usage: str = "Usage: odoo {name} [-d db] [-v[v]] MODULE [MODULE...]"
    auto_mode: bool = False

    def _parse_args(self, args: list[str]) -> ParsedArgs:
        modules, options = self._get_modules_and_options(args)

        missing_modules = bool(not modules and not self.auto_mode)
        if missing_modules or "--help" in options or "-h" in options:
            name = self.name
            raise SystemExit(self.usage.format(name=name))

        module_args = [self.module_operation, ",".join(modules)]
        new_args = (module_args if not self.auto_mode else []) + options
        return super()._parse_args(new_args)  # type: ignore

    def _get_modules_and_options(
        self,
        args: list[str],
    ) -> tuple[list[str], list[str]]:
        modules = []
        options = []
        next_arg_is_option = False
        for arg in args:
            if arg.startswith("-") or next_arg_is_option:
                next_arg_is_option = False
                options.append(arg)
                if arg in {"-d", "--database", "-c", "--config", "--logfile"}:
                    next_arg_is_option = True
            else:
                modules.append(arg)
        return modules, options


class ModuleInstallCommand(ModuleCommandMixin, PrettyModuleLoadCommand):
    """
    Install modules (with pretty output)
    """

    name = "module-install"
    module_operation = "-i"


class ModuleUpdateCommand(ModuleCommandMixin, PrettyModuleLoadCommand):
    """
    Update modules (with pretty output)
    """

    name = "module-update"
    module_operation = "-u"
    usage = (
        "Usage: odoo {name} [OPTIONS] [MODULE...]\n\n"
        "where OPTIONS could be:\n"
        "  --database, -d db_name For specifying the database name\n"
        "  --config, -c config    For using a different odoo config file\n"
        "  --auto                 For updating only changed modules\n"
        "  -v, -vv, -vvv          For tuning the verbosity level\n"
        "or other options accepted by Odoo, e.g.:\n"
        "  --i18n-overwrite       For overwriting existing translation terms\n"
        "\n"
        "If no MODULE names are given, the --auto mode is assumed.\n"
    )
    i18n_overwrite = False

    def _parse_args(self, args: list[str]) -> ParsedArgs:
        modules = self._get_modules_and_options(args)[0]
        if "--auto" in args or "-a" in args or not modules:
            self.auto_mode = True
            args = [x for x in args if x not in {"--auto", "-a"}]
            if "--i18n-overwrite" in args:
                self.i18n_overwrite = True
                args = [x for x in args if x != "--i18n-overwrite"]
        return super()._parse_args(args)

    def _run_real(self, args: list[str], verbosity: int) -> None:
        if self.auto_mode:
            if not click_odoo_update:
                raise SystemExit("click-odoo-contrib is not installed")
            click_odoo_update(
                database=self._get_database_name(),
                update_all=False,
                i18n_overwrite=self.i18n_overwrite,
            )
        else:
            super()._run_real(args, verbosity)


class IAlias(ModuleInstallCommand):
    """
    Install modules (with pretty output)
    """

    name = "i"


class UAlias(ModuleUpdateCommand):
    """
    Update modules (with pretty output)
    """

    name = "u"
