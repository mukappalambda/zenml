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
"""ZenML Store interface."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Union
from uuid import UUID

from zenml.enums import StackComponentType
from zenml.models import (
    ArtifactRequestModel,
    ArtifactResponseModel,
    ComponentRequestModel,
    ComponentResponseModel,
    ComponentUpdateModel,
    FlavorRequestModel,
    FlavorResponseModel,
    PipelineRequestModel,
    PipelineResponseModel,
    PipelineRunRequestModel,
    PipelineRunResponseModel,
    PipelineRunUpdateModel,
    PipelineUpdateModel,
    WorkspaceRequestModel,
    WorkspaceResponseModel,
    WorkspaceUpdateModel,
    RoleAssignmentRequestModel,
    RoleAssignmentResponseModel,
    RoleRequestModel,
    RoleResponseModel,
    RoleUpdateModel,
    StackRequestModel,
    StackResponseModel,
    StackUpdateModel,
    StepRunRequestModel,
    StepRunResponseModel,
    StepRunUpdateModel,
    TeamRequestModel,
    TeamResponseModel,
    TeamUpdateModel,
    UserAuthModel,
    UserRequestModel,
    UserResponseModel,
    UserUpdateModel,
)
from zenml.models.server_models import ServerModel

if TYPE_CHECKING:
    from ml_metadata.proto.metadata_store_pb2 import (
        ConnectionConfig,
        MetadataStoreClientConfig,
    )


class ZenStoreInterface(ABC):
    """ZenML store interface.

    All ZenML stores must implement the methods in this interface.

    The methods in this interface are organized in the following way:

     * they are grouped into categories based on the type of resource
       that they operate on (e.g. stacks, stack components, etc.)

     * each category has a set of CRUD methods (create, read, update, delete)
       that operate on the resources in that category. The order of the methods
       in each category should be:

       * create methods - store a new resource. These methods
         should fill in generated fields (e.g. UUIDs, creation timestamps) in
         the resource and return the updated resource.
       * get methods - retrieve a single existing resource identified by a
         unique key or identifier from the store. These methods should always
         return a resource and raise an exception if the resource does not
         exist.
       * list methods - retrieve a list of resources from the store. These
         methods should accept a set of filter parameters that can be used to
         filter the list of resources retrieved from the store.
       * update methods - update an existing resource in the store. These
         methods should expect the updated resource to be correctly identified
         by its unique key or identifier and raise an exception if the resource
         does not exist.
       * delete methods - delete an existing resource from the store. These
         methods should expect the resource to be correctly identified by its
         unique key or identifier. If the resource does not exist,
         an exception should be raised.

    Best practices for implementing and keeping this interface clean and easy to
    maintain and extend:

      * keep methods organized by resource type and ordered by CRUD operation
      * for resources with multiple keys, don't implement multiple get or list
      methods here if the same functionality can be achieved by a single get or
      list method. Instead, implement them in the BaseZenStore class and have
      them call the generic get or list method in this interface.
      * keep the logic required to convert between ZenML domain Model classes
      and internal store representations outside the ZenML domain Model classes
      * methods for resources that have two or more unique keys (e.g. a Workspace
      is uniquely identified by its name as well as its UUID) should reflect
      that in the method variants and/or method arguments:
        * methods that take in a resource identifier as argument should accept
        all variants of the identifier (e.g. `workspace_name_or_uuid` for methods
        that get/list/update/delete Workspaces)
        * if a compound key is involved, separate get methods should be
        implemented (e.g. `get_pipeline` to get a pipeline by ID and
        `get_pipeline_in_workspace` to get a pipeline by its name and the ID of
        the workspace it belongs to)
      * methods for resources that are scoped as children of other resources
      (e.g. a Stack is always owned by a Workspace) should reflect the
      key(s) of the parent resource in the provided methods and method
      arguments:
        * create methods should take the parent resource UUID(s) as an argument
        (e.g. `create_stack` takes in the workspace ID)
        * get methods should be provided to retrieve a resource by the compound
        key that includes the parent resource key(s)
        * list methods should feature optional filter arguments that reflect
        the parent resource key(s)
    """

    # ---------------------------------
    # Initialization and configuration
    # ---------------------------------

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the store.

        This method is called immediately after the store is created. It should
        be used to set up the backend (database, connection etc.).
        """

    @abstractmethod
    def get_store_info(self) -> ServerModel:
        """Get information about the store.

        Returns:
            Information about the store.
        """

    # ------------
    # TFX Metadata
    # ------------

    @abstractmethod
    def get_metadata_config(
        self, expand_certs: bool = False
    ) -> Union["ConnectionConfig", "MetadataStoreClientConfig"]:
        """Get the TFX metadata config of this ZenStore.

        Args:
            expand_certs: Whether to expand the certificate paths in the
                connection config to their value.

        Returns:
            The TFX metadata config of this ZenStore.
        """

    # ------
    # Stacks
    # ------

    @abstractmethod
    def create_stack(self, stack: StackRequestModel) -> StackResponseModel:
        """Create a new stack.

        Args:
            stack: The stack to create.

        Returns:
            The created stack.

        Raises:
            StackExistsError: If a stack with the same name is already owned
                by this user in this workspace.
        """

    @abstractmethod
    def get_stack(self, stack_id: UUID) -> StackResponseModel:
        """Get a stack by its unique ID.

        Args:
            stack_id: The ID of the stack to get.

        Returns:
            The stack with the given ID.

        Raises:
            KeyError: if the stack doesn't exist.
        """

    @abstractmethod
    def list_stacks(
        self,
        workspace_name_or_id: Optional[Union[str, UUID]] = None,
        user_name_or_id: Optional[Union[str, UUID]] = None,
        component_id: Optional[UUID] = None,
        name: Optional[str] = None,
        is_shared: Optional[bool] = None,
    ) -> List[StackResponseModel]:
        """List all stacks matching the given filter criteria.

        Args:
            workspace_name_or_id: ID or name of the Workspace containing the stack
            user_name_or_id: Optionally filter stacks by their owner
            component_id: Optionally filter for stacks that contain the
                          component
            name: Optionally filter stacks by their name
            is_shared: Optionally filter out stacks by whether they are shared
                or not


        Returns:
            A list of all stacks matching the filter criteria.

        Raises:
            KeyError: if the workspace doesn't exist.
        """

    @abstractmethod
    def update_stack(
        self, stack_id: UUID, stack_update: StackUpdateModel
    ) -> StackResponseModel:
        """Update a stack.

        Args:
            stack_id: The ID of the stack update.
            stack_update: The update request on the stack.

        Returns:
            The updated stack.

        Raises:
            KeyError: if the stack doesn't exist.
        """

    @abstractmethod
    def delete_stack(self, stack_id: UUID) -> None:
        """Delete a stack.

        Args:
            stack_id: The ID of the stack to delete.

        Raises:
            KeyError: if the stack doesn't exist.
        """

    # ----------------
    # Stack components
    # ----------------

    @abstractmethod
    def create_stack_component(
        self, component: ComponentRequestModel
    ) -> ComponentResponseModel:
        """Create a stack component.

        Args:
            component: The stack component to create.

        Returns:
            The created stack component.

        Raises:
            StackComponentExistsError: If a stack component with the same name
                and type is already owned by this user in this workspace.
        """

    @abstractmethod
    def list_stack_components(
        self,
        workspace_name_or_id: Optional[Union[str, UUID]] = None,
        user_name_or_id: Optional[Union[str, UUID]] = None,
        type: Optional[str] = None,
        flavor_name: Optional[str] = None,
        name: Optional[str] = None,
        is_shared: Optional[bool] = None,
    ) -> List[ComponentResponseModel]:
        """List all stack components matching the given filter criteria.

        Args:
            workspace_name_or_id: The ID or name of the Workspace to which the stack
                components belong
            user_name_or_id: Optionally filter stack components by the owner
            type: Optionally filter by type of stack component
            flavor_name: Optionally filter by flavor
            name: Optionally filter stack component by name
            is_shared: Optionally filter out stack component by whether they are
                shared or not

        Returns:
            A list of all stack components matching the filter criteria.

        Raises:
            KeyError: if the workspace doesn't exist.
        """

    @abstractmethod
    def get_stack_component(self, component_id: UUID) -> ComponentResponseModel:
        """Get a stack component by ID.

        Args:
            component_id: The ID of the stack component to get.

        Returns:
            The stack component.

        Raises:
            KeyError: if the stack component doesn't exist.
        """

    @abstractmethod
    def update_stack_component(
        self,
        component_id: UUID,
        component_update: ComponentUpdateModel,
    ) -> ComponentResponseModel:
        """Update an existing stack component.

        Args:
            component_id: The ID of the stack component to update.
            component_update: The update to be applied to the stack component.

        Returns:
            The updated stack component.

        Raises:
            KeyError: if the stack component doesn't exist.
        """

    @abstractmethod
    def delete_stack_component(self, component_id: UUID) -> None:
        """Delete a stack component.

        Args:
            component_id: The ID of the stack component to delete.

        Raises:
            KeyError: if the stack component doesn't exist.
            ValueError: if the stack component is part of one or more stacks.
        """

    # -----------------------
    # Stack component flavors
    # -----------------------

    @abstractmethod
    def create_flavor(
        self,
        flavor: FlavorRequestModel,
    ) -> FlavorResponseModel:
        """Creates a new stack component flavor.

        Args:
            flavor: The stack component flavor to create.

        Returns:
            The newly created flavor.

        Raises:
            EntityExistsError: If a flavor with the same name and type
                is already owned by this user in this workspace.
        """

    @abstractmethod
    def get_flavor(self, flavor_id: UUID) -> FlavorResponseModel:
        """Get a stack component flavor by ID.

        Args:
            flavor_id: The ID of the flavor to get.

        Returns:
            The stack component flavor.

        Raises:
            KeyError: if the stack component flavor doesn't exist.
        """

    @abstractmethod
    def list_flavors(
        self,
        workspace_name_or_id: Optional[Union[str, UUID]] = None,
        user_name_or_id: Optional[Union[str, UUID]] = None,
        component_type: Optional[StackComponentType] = None,
        name: Optional[str] = None,
        is_shared: Optional[bool] = None,
    ) -> List[FlavorResponseModel]:
        """List all stack component flavors matching the given filter criteria.

        Args:
            workspace_name_or_id: Optionally filter by the Workspace to which the
                component flavors belong
            user_name_or_id: Optionally filter by the owner
            component_type: Optionally filter by type of stack component
            name: Optionally filter flavors by name
            is_shared: Optionally filter out flavors by whether they are
                shared or not

        Returns:
            List of all the stack component flavors matching the given criteria.

        Raises:
            KeyError: if the workspace doesn't exist.
        """

    @abstractmethod
    def delete_flavor(self, flavor_id: UUID) -> None:
        """Delete a stack component flavor.

        Args:
            flavor_id: The ID of the stack component flavor to delete.

        Raises:
            KeyError: if the stack component flavor doesn't exist.
        """

    # -----
    # Users
    # -----
    @property
    @abstractmethod
    def active_user_name(self) -> str:
        """Gets the active username.

        Returns:
            The active username.
        """

    @abstractmethod
    def create_user(self, user: UserRequestModel) -> UserResponseModel:
        """Creates a new user.

        Args:
            user: User to be created.

        Returns:
            The newly created user.

        Raises:
            EntityExistsError: If a user with the given name already exists.
        """

    @abstractmethod
    def get_user(self, user_name_or_id: Union[str, UUID]) -> UserResponseModel:
        """Gets a specific user.

        Args:
            user_name_or_id: The name or ID of the user to get.

        Returns:
            The requested user, if it was found.

        Raises:
            KeyError: If no user with the given name or ID exists.
        """

    def get_auth_user(self, user_name_or_id: Union[str, UUID]) -> UserAuthModel:
        """Gets the auth model to a specific user.

        Args:
            user_name_or_id: The name or ID of the user to get.

        Returns:
            The requested user, if it was found.
        """

    @abstractmethod
    def list_users(self, name: Optional[str] = None) -> List[UserResponseModel]:
        """List all users.

        Args:
            name: Optionally filter by name

        Returns:
            A list of all users.
        """

    @abstractmethod
    def update_user(
        self, user_name_or_id: Union[str, UUID], user_update: UserUpdateModel
    ) -> UserResponseModel:
        """Updates an existing user.

        Args:
            user_name_or_id: The id of the user to update.
            user_update: The update to be applied to the user.

        Returns:
            The updated user.

        Raises:
            KeyError: If no user with the given name exists.
        """

    @abstractmethod
    def delete_user(self, user_name_or_id: Union[str, UUID]) -> None:
        """Deletes a user.

        Args:
            user_name_or_id: The name or ID of the user to delete.

        Raises:
            KeyError: If no user with the given ID exists.
        """

    # -----
    # Teams
    # -----

    @abstractmethod
    def create_team(self, team: TeamRequestModel) -> TeamResponseModel:
        """Creates a new team.

        Args:
            team: The team model to create.

        Returns:
            The newly created team.
        """

    @abstractmethod
    def get_team(self, team_name_or_id: Union[str, UUID]) -> TeamResponseModel:
        """Gets a specific team.

        Args:
            team_name_or_id: Name or ID of the team to get.

        Returns:
            The requested team.

        Raises:
            KeyError: If no team with the given name or ID exists.
        """

    @abstractmethod
    def list_teams(self, name: Optional[str] = None) -> List[TeamResponseModel]:
        """List all teams.

        Args:
            name: Optionally filter by name

        Returns:
            A list of all teams.
        """

    @abstractmethod
    def update_team(
        self, team_id: UUID, team_update: TeamUpdateModel
    ) -> TeamResponseModel:
        """Update an existing team.

        Args:
            team_id: The ID of the team to be updated.
            team_update: The update to be applied to the team.

        Returns:
            The updated team.

        Raises:
            KeyError: if the team does not exist.
        """

    @abstractmethod
    def delete_team(self, team_name_or_id: Union[str, UUID]) -> None:
        """Deletes a team.

        Args:
            team_name_or_id: Name or ID of the team to delete.

        Raises:
            KeyError: If no team with the given ID exists.
        """

    # -----
    # Roles
    # -----

    @abstractmethod
    def create_role(self, role: RoleRequestModel) -> RoleResponseModel:
        """Creates a new role.

        Args:
            role: The role model to create.

        Returns:
            The newly created role.

        Raises:
            EntityExistsError: If a role with the given name already exists.
        """

    @abstractmethod
    def get_role(self, role_name_or_id: Union[str, UUID]) -> RoleResponseModel:
        """Gets a specific role.

        Args:
            role_name_or_id: Name or ID of the role to get.

        Returns:
            The requested role.

        Raises:
            KeyError: If no role with the given name exists.
        """

    @abstractmethod
    def list_roles(self, name: Optional[str] = None) -> List[RoleResponseModel]:
        """List all roles.

        Args:
            name: Optionally filter by name

        Returns:
            A list of all roles.
        """

    @abstractmethod
    def update_role(
        self, role_id: UUID, role_update: RoleUpdateModel
    ) -> RoleResponseModel:
        """Update an existing role.

        Args:
            role_id: The ID of the role to be updated.
            role_update: The update to be applied to the role.

        Returns:
            The updated role.

        Raises:
            KeyError: if the role does not exist.
        """

    @abstractmethod
    def delete_role(self, role_name_or_id: Union[str, UUID]) -> None:
        """Deletes a role.

        Args:
            role_name_or_id: Name or ID of the role to delete.

        Raises:
            KeyError: If no role with the given ID exists.
        """

    # ----------------
    # Role assignments
    # ----------------
    @abstractmethod
    def create_role_assignment(
        self, role_assignment: RoleAssignmentRequestModel
    ) -> RoleAssignmentResponseModel:
        """"""

    @abstractmethod
    def get_role_assignment(
        self, role_assignment_id: UUID
    ) -> RoleAssignmentResponseModel:
        """"""

    @abstractmethod
    def delete_role_assignment(self, role_assignment_id: UUID) -> UUID:
        """Delete a specific role assignment

        Args:
            role_assignment_id: The Id of the specific role assignment
        """

    @abstractmethod
    def list_role_assignments(
        self,
        workspace_name_or_id: Optional[Union[str, UUID]] = None,
        role_name_or_id: Optional[Union[str, UUID]] = None,
        team_name_or_id: Optional[Union[str, UUID]] = None,
        user_name_or_id: Optional[Union[str, UUID]] = None,
    ) -> List[RoleAssignmentResponseModel]:
        """List all role assignments.

        Args:
            workspace_name_or_id: If provided, only list assignments for the given
                workspace
            role_name_or_id: If provided, only list assignments of the given
                role
            team_name_or_id: If provided, only list assignments for the given
                team
            user_name_or_id: If provided, only list assignments for the given
                user

        Returns:
            A list of all role assignments.
        """

    # --------
    # Workspaces
    # --------

    @abstractmethod
    def create_workspace(
        self, workspace: WorkspaceRequestModel
    ) -> WorkspaceResponseModel:
        """Creates a new workspace.

        Args:
            workspace: The workspace to create.

        Returns:
            The newly created workspace.

        Raises:
            EntityExistsError: If a workspace with the given name already exists.
        """

    @abstractmethod
    def get_workspace(
        self, workspace_name_or_id: Union[UUID, str]
    ) -> WorkspaceResponseModel:
        """Get an existing workspace by name or ID.

        Args:
            workspace_name_or_id: Name or ID of the workspace to get.

        Returns:
            The requested workspace.

        Raises:
            KeyError: If there is no such workspace.
        """

    @abstractmethod
    def list_workspaces(
        self, name: Optional[str] = None
    ) -> List[WorkspaceResponseModel]:
        """List all workspaces.

        Args:
            name: Optionally filter by name

        Returns:
            A list of all workspaces.
        """

    @abstractmethod
    def update_workspace(
        self, workspace_id: UUID, workspace_update: WorkspaceUpdateModel
    ) -> WorkspaceResponseModel:
        """Update an existing workspace.

        Args:
            workspace_id: The ID of the workspace to be updated.
            workspace_update: The update to be applied to the workspace.

        Returns:
            The updated workspace.

        Raises:
            KeyError: if the workspace does not exist.
        """

    @abstractmethod
    def delete_workspace(self, workspace_name_or_id: Union[str, UUID]) -> None:
        """Deletes a workspace.

        Args:
            workspace_name_or_id: Name or ID of the workspace to delete.

        Raises:
            KeyError: If no workspace with the given name exists.
        """

    # ---------
    # Pipelines
    # ---------
    @abstractmethod
    def create_pipeline(
        self,
        pipeline: PipelineRequestModel,
    ) -> PipelineResponseModel:
        """Creates a new pipeline in a workspace.

        Args:
            pipeline: The pipeline to create.

        Returns:
            The newly created pipeline.

        Raises:
            KeyError: if the workspace does not exist.
            EntityExistsError: If an identical pipeline already exists.
        """

    @abstractmethod
    def get_pipeline(self, pipeline_id: UUID) -> PipelineResponseModel:
        """Get a pipeline with a given ID.

        Args:
            pipeline_id: ID of the pipeline.

        Returns:
            The pipeline.

        Raises:
            KeyError: if the pipeline does not exist.
        """

    @abstractmethod
    def list_pipelines(
        self,
        workspace_name_or_id: Optional[Union[str, UUID]] = None,
        user_name_or_id: Optional[Union[str, UUID]] = None,
        name: Optional[str] = None,
    ) -> List[PipelineResponseModel]:
        """List all pipelines in the workspace.

        Args:
            workspace_name_or_id: If provided, only list pipelines in this
                workspace.
            user_name_or_id: If provided, only list pipelines from this user.
            name: If provided, only list pipelines with this name.

        Returns:
            A list of pipelines.

        Raises:
            KeyError: if the workspace does not exist.
        """

    @abstractmethod
    def update_pipeline(
        self,
        pipeline_id: UUID,
        pipeline_update: PipelineUpdateModel,
    ) -> PipelineResponseModel:
        """Updates a pipeline.

        Args:
            pipeline_id: The ID of the pipeline to be updated.
            pipeline_update: The update to be applied.

        Returns:
            The updated pipeline.

        Raises:
            KeyError: if the pipeline doesn't exist.
        """

    @abstractmethod
    def delete_pipeline(self, pipeline_id: UUID) -> None:
        """Deletes a pipeline.

        Args:
            pipeline_id: The ID of the pipeline to delete.

        Raises:
            KeyError: if the pipeline doesn't exist.
        """

    # --------------
    # Pipeline runs
    # --------------

    @abstractmethod
    def create_run(
        self, pipeline_run: PipelineRunRequestModel
    ) -> PipelineRunResponseModel:
        """Creates a pipeline run.

        Args:
            pipeline_run: The pipeline run to create.

        Returns:
            The created pipeline run.

        Raises:
            EntityExistsError: If an identical pipeline run already exists.
            KeyError: If the pipeline does not exist.
        """

    @abstractmethod
    def get_run(
        self, run_name_or_id: Union[str, UUID]
    ) -> PipelineRunResponseModel:
        """Gets a pipeline run.

        Args:
            run_name_or_id: The name or ID of the pipeline run to get.

        Returns:
            The pipeline run.

        Raises:
            KeyError: if the pipeline run doesn't exist.
        """

    @abstractmethod
    def get_or_create_run(
        self, pipeline_run: PipelineRunRequestModel
    ) -> PipelineRunResponseModel:
        """Gets or creates a pipeline run.

        If a run with the same ID or name already exists, it is returned.
        Otherwise, a new run is created.

        Args:
            pipeline_run: The pipeline run to get or create.

        Returns:
            The pipeline run.
        """

    @abstractmethod
    def list_runs(
        self,
        workspace_name_or_id: Optional[Union[str, UUID]] = None,
        stack_id: Optional[UUID] = None,
        component_id: Optional[UUID] = None,
        run_name: Optional[str] = None,
        user_name_or_id: Optional[Union[str, UUID]] = None,
        pipeline_id: Optional[UUID] = None,
        unlisted: bool = False,
    ) -> List[PipelineRunResponseModel]:
        """Gets all pipeline runs.

        Args:
            workspace_name_or_id: If provided, only return runs for this workspace.
            stack_id: If provided, only return runs for this stack.
            component_id: Optionally filter for runs that used the
                          component
            run_name: Run name if provided
            user_name_or_id: If provided, only return runs for this user.
            pipeline_id: If provided, only return runs for this pipeline.
            unlisted: If True, only return unlisted runs that are not
                associated with any pipeline (filter by `pipeline_id==None`).

        Returns:
            A list of all pipeline runs.
        """

    @abstractmethod
    def update_run(
        self, run_id: UUID, run_update: PipelineRunUpdateModel
    ) -> PipelineRunResponseModel:
        """Updates a pipeline run.

        Args:
            run_id: The ID of the pipeline run to update.
            run_update: The update to be applied to the pipeline run.

        Returns:
            The updated pipeline run.

        Raises:
            KeyError: if the pipeline run doesn't exist.
        """

    # ------------------
    # Pipeline run steps
    # ------------------

    @abstractmethod
    def create_run_step(
        self, step: StepRunRequestModel
    ) -> StepRunResponseModel:
        """Creates a step.

        Args:
            step: The step to create.

        Returns:
            The created step.

        Raises:
            EntityExistsError: if the step already exists.
            KeyError: if the pipeline run doesn't exist.
        """

    @abstractmethod
    def get_run_step(self, step_id: UUID) -> StepRunResponseModel:
        """Get a step by ID.

        Args:
            step_id: The ID of the step to get.

        Returns:
            The step.

        Raises:
            KeyError: if the step doesn't exist.
        """

    @abstractmethod
    def get_run_step_inputs(
        self, step_id: UUID
    ) -> Dict[str, ArtifactResponseModel]:
        """Get a list of inputs for a specific step.

        Args:
            step_id: The id of the step to get inputs for.

        Returns:
            A dict mapping artifact names to the input artifacts for the step.
        """

    @abstractmethod
    def list_run_steps(
        self, run_id: Optional[UUID] = None
    ) -> List[StepRunResponseModel]:
        """Gets all steps in a pipeline run.

        Args:
            run_id: The ID of the pipeline run for which to list runs.

        Returns:
            A list of all run steps.
        """

    @abstractmethod
    def update_run_step(
        self,
        step_id: UUID,
        step_update: StepRunUpdateModel,
    ) -> StepRunResponseModel:
        """Updates a step.

        Args:
            step_id: The ID of the step to update.
            step_update: The update to be applied to the step.

        Returns:
            The updated step.

        Raises:
            KeyError: if the step doesn't exist.
        """

    # ---------
    # Artifacts
    # ---------

    @abstractmethod
    def create_artifact(
        self, artifact: ArtifactRequestModel
    ) -> ArtifactResponseModel:
        """Creates an artifact.

        Args:
            artifact: The artifact to create.

        Returns:
            The created artifact.

        Raises:
            KeyError: if the parent step doesn't exist.
        """

    @abstractmethod
    def list_artifacts(
        self,
        artifact_uri: Optional[str] = None,
        parent_step_id: Optional[UUID] = None,
    ) -> List[ArtifactResponseModel]:
        """Lists all artifacts.

        Args:
            artifact_uri: If specified, only artifacts with the given URI will
                be returned.
            parent_step_id: If specified, only artifacts for the given step run
                will be returned.

        Returns:
            A list of all artifacts.
        """

    # ------------------------
    # Internal utility methods
    # ------------------------
    @abstractmethod
    def _sync_runs(self) -> None:
        """Syncs runs from MLMD."""
