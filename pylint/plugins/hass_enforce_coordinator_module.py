"""Plugin for checking if coordinator is in its own module."""

from __future__ import annotations

from astroid import nodes
from astroid.nodes.node_classes import Assign
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter


class HassEnforceCoordinatorModule(BaseChecker):
    """Checker for coordinators own module."""

    name = "hass_enforce_coordinator_module"
    priority = -1
    msgs = {
        "C7461": (
            "Derived data update coordinator is recommended to be placed in the 'coordinator' module",
            "hass-enforce-coordinator-module",
            "Used when derived data update coordinator should be placed in its own module.",
        ),
    }
    options = (
        (
            "ignore-wrong-coordinator-module",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y or n>",
                "help": "Set to ``no`` if you wish to check if derived data update coordinator "
                "is placed in its own module.",
            },
        ),
    )

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Check if derived data update coordinator is placed in its own module."""
        if self.linter.config.ignore_wrong_coordinator_module:
            return

        root_name = node.root().name

        # we only want to check component update coordinators
        if not root_name.startswith("homeassistant.components"):
            return

        is_coordinator_module = root_name.endswith(".coordinator")
        for ancestor in node.ancestors():
            if ancestor.name == "DataUpdateCoordinator" and not is_coordinator_module:
                self.add_message("hass-enforce-coordinator-module", node=node)
                return


class UpdateIntervalChecker(BaseChecker):
    """Checker for coordinators update_interval usage."""

    name = "hass_enforce_update_coordinator_attributes"
    priority = -1
    msgs = {
        "W7462": (
            "Do not define 'update_interval' in a subclass of 'DataUpdateCoordinator'. Use '_update_interval' instead",
            "hass-enforce-update-coordinator-attributes",
            "Used when an update coordinator uses the public update_interal",
        ),
    }
    options = ()

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Check if update coordinator sets update_interval during construction."""

        if all(a.name != "DataUpdateCoordinator" for a in node.ancestors()):
            return
        for attr in node.body:
            if (
                not isinstance(attr, Assign)
                or attr.targets[0].as_string() != "update_interval"
                or any(
                    msg.obj == node.name and msg.line == node.lineno
                    for msg in self.linter.reporter.messages
                )
            ):
                continue
            self.add_message("hass-enforce-update-coordinator-attributes", node=node)
            return


def register(linter: PyLinter) -> None:
    """Register the checker."""
    linter.register_checker(HassEnforceCoordinatorModule(linter))
    linter.register_checker(UpdateIntervalChecker(linter))
