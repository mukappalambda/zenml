from typing import Optional

from pydantic import BaseModel, Field

from zenml.enums import StackComponentType
from zenml.models.base_models import (
    WorkspaceScopedRequestModel,
    WorkspaceScopedResponseModel,
)
from zenml.models.constants import MODEL_CONFIG_SCHEMA_MAX_LENGTH

# TODO: Add example schemas and analytics fields

# ---- #
# BASE #
# ---- #


class FlavorBaseModel(BaseModel):
    name: str = Field(
        title="The name of the Flavor.",
    )
    type: StackComponentType = Field(
        title="The type of the Flavor.",
    )
    config_schema: str = Field(
        title="The JSON schema of this flavor's corresponding configuration.",
        max_length=MODEL_CONFIG_SCHEMA_MAX_LENGTH,
    )
    source: str = Field(
        title="The path to the module which contains this Flavor."
    )
    integration: Optional[str] = Field(
        title="The name of the integration that the Flavor belongs to."
    )


# -------- #
# RESPONSE #
# -------- #


class FlavorResponseModel(FlavorBaseModel, WorkspaceScopedResponseModel):
    """Domain model representing the custom implementation of a flavor."""


# ------- #
# REQUEST #
# ------- #


class FlavorRequestModel(FlavorBaseModel, WorkspaceScopedRequestModel):
    """ """
