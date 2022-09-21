#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""Tekton orchestrator flavor."""

from typing import TYPE_CHECKING, Type

from zenml.integrations.tekton import TEKTON_ORCHESTRATOR_FLAVOR
from zenml.orchestrators import BaseOrchestratorConfig, BaseOrchestratorFlavor

if TYPE_CHECKING:
    from zenml.integrations.tekton.orchestrators import TektonOrchestrator


DEFAULT_TEKTON_UI_PORT = 8080


class TektonOrchestratorConfig(BaseOrchestratorConfig):
    """Configuration for the Tekton orchestrator.

    Attributes:
        kubernetes_context: Name of a kubernetes context to run
            pipelines in.
        kubernetes_namespace: Name of the kubernetes namespace in which the
            pods that run the pipeline steps should be running.
        tekton_ui_port: A local port to which the Tekton UI will be forwarded.
        skip_ui_daemon_provisioning: If `True`, provisioning the Tekton UI
            daemon will be skipped.
    """

    kubernetes_context: str
    kubernetes_namespace: str = "zenml"
    tekton_ui_port: int = DEFAULT_TEKTON_UI_PORT
    skip_ui_daemon_provisioning: bool = False


class TektonOrchestratorFlavor(BaseOrchestratorFlavor):
    """Flavor for the Tekton orchestrator."""

    @property
    def name(self) -> str:
        return TEKTON_ORCHESTRATOR_FLAVOR

    @property
    def config_class(self) -> Type[TektonOrchestratorConfig]:
        return TektonOrchestratorConfig

    @property
    def implementation_class(self) -> Type["TektonOrchestrator"]:
        from zenml.integrations.tekton.orchestrators import TektonOrchestrator

        return TektonOrchestrator