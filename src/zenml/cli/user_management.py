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
"""Functionality to administer users of the ZenML CLI and server."""

from typing import List, Optional, Tuple

import click

from zenml.cli import utils as cli_utils
from zenml.cli.cli import TagGroup, cli
from zenml.client import Client
from zenml.enums import CliCategories, PermissionType, StoreType
from zenml.exceptions import EntityExistsError, IllegalOperationError
from zenml.utils.uuid_utils import parse_name_or_uuid


@cli.group(cls=TagGroup, tag=CliCategories.IDENTITY_AND_SECURITY)
def user() -> None:
    """Commands for user management."""


@user.command("get")
def get_user() -> None:
    """Get the active user."""
    cli_utils.print_active_config()
    cli_utils.declare(f"Active user: '{Client().zen_store.active_user_name}'")


@user.command("list")
def list_users() -> None:
    """List all users."""
    cli_utils.print_active_config()
    users = Client().zen_store.users
    if not users:
        cli_utils.declare("No users registered.")
        return

    cli_utils.print_pydantic_models(
        users,
        exclude_columns=[
            "created",
            "updated",
            "email",
            "email_opted_in",
            "activation_token",
        ],
        is_active=lambda u: u.name == Client().zen_store.active_user_name,
    )


@user.command(
    "create",
    help="Create a new user. If an empty password is configured, an activation "
    "token is generated and a link to the dashboard is provided where the "
    "user can activate the account.",
)
@click.argument("user_name", type=str, required=True)
@click.option(
    "--password",
    help=(
        "The user password. If omitted, a prompt will be shown to enter the "
        "password. If an empty password is entered, an activation token is "
        "generated and a link to the dashboard is provided where the user can "
        "activate the account."
    ),
    required=False,
    type=str,
)
@click.option(
    "--role",
    "-r",
    "initial_role",
    help=("Give the user an initial role."),
    required=False,
    type=str,
    default="admin",
)
def create_user(
    user_name: str,
    initial_role: str = "admin",
    password: Optional[str] = None,
) -> None:
    """Create a new user.

    Args:
        user_name: The name of the user to create.
        password: The password of the user to create.
        initial_role: Give the user an initial role
    """
    client = Client()
    if not password:
        if client.zen_store.type != StoreType.REST:

            password = click.prompt(
                f"Password for user {user_name}",
                hide_input=True,
            )
        else:
            password = click.prompt(
                f"Password for user {user_name}. Leave empty to generate an "
                f"activation token",
                default="",
                hide_input=True,
            )

    cli_utils.print_active_config()

    try:
        new_user = client.create_user(name=user_name, password=password)

        cli_utils.declare(f"Created user '{new_user.name}'.")
    except EntityExistsError as err:
        cli_utils.error(str(err))
    else:
        try:
            client.create_user_role_assignment(
                role_name_or_id=initial_role,
                user_name_or_id=str(new_user.id),
                project_name_or_id=None,
            )
        except KeyError as err:
            cli_utils.error(str(err))

    if not new_user.active and new_user.activation_token is not None:
        cli_utils.declare(
            f"The created user account is currently inactive. You can activate "
            f"it by visiting the dashboard at the following URL:\n"
            f"{client.zen_store.url}/signup?user={str(new_user.id)}&username={new_user.name}&token={new_user.activation_token.get_secret_value()}\n"
        )


@user.command(
    "update",
    help="Update user information through the cli. All attributes "
    "except for password can be updated through the cli.",
)
@click.argument("user_name_or_id", type=str, required=True)
@click.option(
    "--name",
    "-n",
    "updated_name",
    type=str,
    required=False,
    help="New user name.",
)
@click.option(
    "--full_name",
    "-f",
    "updated_full_name",
    type=str,
    required=False,
    help="New full name. If this contains an empty space make sure to surround "
    "the name with quotes '<Full Name>'.",
)
@click.option(
    "--email",
    "-e",
    "updated_email",
    type=str,
    required=False,
    help="New user email.",
)
def update_user(
    user_name_or_id: str,
    updated_name: Optional[str] = None,
    updated_full_name: Optional[str] = None,
    updated_email: Optional[str] = None,
) -> None:
    """Create a new user.

    Args:
        user_name_or_id: The name of the user to create.
        updated_name: The name of the user to create.
        updated_full_name: The name of the user to create.
        updated_email: The name of the user to create.
    """
    try:
        Client().update_user(
            user_name_or_id=user_name_or_id,
            updated_name=updated_name,
            updated_full_name=updated_full_name,
            updated_email=updated_email,
        )
    except (KeyError, IllegalOperationError) as err:
        cli_utils.error(str(err))


@user.command("delete")
@click.argument("user_name_or_id", type=str, required=True)
def delete_user(user_name_or_id: str) -> None:
    """Delete a user.

    Args:
        user_name_or_id: The name or ID of the user to delete.
    """
    cli_utils.print_active_config()
    try:
        Client().delete_user(user_name_or_id)
    except (KeyError, IllegalOperationError) as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Deleted user '{user_name_or_id}'.")


@cli.group(cls=TagGroup, tag=CliCategories.IDENTITY_AND_SECURITY)
def team() -> None:
    """Commands for team management."""


@team.command("list")
def list_teams() -> None:
    """List all teams."""
    cli_utils.print_active_config()
    teams = Client().zen_store.teams
    if not teams:
        cli_utils.declare("No teams registered.")
        return

    cli_utils.print_pydantic_models(
        teams,
        exclude_columns=["id", "created", "updated"],
    )


@team.command("describe", help="List all users in a team.")
@click.argument("team_name_or_id", type=str, required=True)
def describe_team(team_name_or_id: str) -> None:
    """List all users in a team.

    Args:
        team_name_or_id: The name or ID of the team to describe.
    """
    cli_utils.print_active_config()
    try:
        users = Client().zen_store.get_users_for_team(
            team_name_or_id=parse_name_or_uuid(team_name_or_id)
        )
    except KeyError as err:
        cli_utils.error(str(err))
    if not users:
        cli_utils.declare(f"Team '{team_name_or_id}' has no users.")
        return
    user_names = set([user.name for user in users])
    cli_utils.declare(
        f"Team '{team_name_or_id}' has the following users: {user_names}"
    )


@team.command("create", help="Create a new team.")
@click.argument("team_name", type=str, required=True)
def create_team(team_name: str) -> None:
    """Create a new team.

    Args:
        team_name: Name of the team to create.
    """
    cli_utils.print_active_config()
    try:
        from zenml.models import TeamModel

        Client().zen_store.create_team(TeamModel(name=team_name))
    except EntityExistsError as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Created team '{team_name}'.")


@team.command("update", help="Update an existing team.")
@click.argument("team_name", type=str, required=True)
@click.option("--name", "-n", type=str, required=False, help="New team name.")
def update_team(
    team_name: str,
    name: Optional[str] = None,
) -> None:
    """Update an existing team.

    Args:
        team_name: The name of the team.
        name: The new name of the team.
    """
    cli_utils.print_active_config()
    try:
        team = Client().zen_store.get_team(team_name)
        team.name = name or team.name
        Client().zen_store.update_team(team)
    except (EntityExistsError, KeyError) as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Updated team '{team_name}'.")


@team.command("delete", help="Delete a team.")
@click.argument("team_name_or_id", type=str, required=True)
def delete_team(team_name_or_id: str) -> None:
    """Delete a team.

    Args:
        team_name_or_id: The name or ID of the team to delete.
    """
    cli_utils.print_active_config()
    try:
        Client().zen_store.delete_team(parse_name_or_uuid(team_name_or_id))
    except KeyError as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Deleted team '{team_name_or_id}'.")


@team.command("add", help="Add users to a team.")
@click.argument("team_name_or_id", type=str, required=True)
@click.option(
    "--user", "user_names_or_ids", type=str, required=True, multiple=True
)
def add_users(team_name_or_id: str, user_names_or_ids: Tuple[str]) -> None:
    """Add users to a team.

    Args:
        team_name_or_id: Name or ID of the team.
        user_names_or_ids: The names or IDs of the users to add to the team.
    """
    cli_utils.print_active_config()

    try:
        for user_name_or_id in user_names_or_ids:
            Client().zen_store.add_user_to_team(
                user_name_or_id=parse_name_or_uuid(user_name_or_id),
                team_name_or_id=parse_name_or_uuid(team_name_or_id),
            )
            cli_utils.declare(
                f"Added user '{user_name_or_id}' to team '{team_name_or_id}'."
            )
    except (KeyError, EntityExistsError) as err:
        cli_utils.error(str(err))


@team.command("remove", help="Remove users from a team.")
@click.argument("team_name_or_id", type=str, required=True)
@click.option(
    "--user", "user_names_or_ids", type=str, required=True, multiple=True
)
def remove_users(team_name_or_id: str, user_names_or_ids: Tuple[str]) -> None:
    """Remove users from a team.

    Args:
        team_name_or_id: Name or ID of the team.
        user_names_or_ids: Names or IDS of the users.
    """
    cli_utils.print_active_config()

    try:
        for user_name_or_id in user_names_or_ids:
            Client().zen_store.remove_user_from_team(
                user_name_or_id=parse_name_or_uuid(user_name_or_id),
                team_name_or_id=parse_name_or_uuid(team_name_or_id),
            )
            cli_utils.declare(
                f"Removed user '{user_name_or_id}' from team '{team_name_or_id}'."
            )
    except KeyError as err:
        cli_utils.error(str(err))


def warn_unsupported_non_default_project() -> None:
    """Warning for unsupported non-default project."""
    cli_utils.warning(
        "Currently the concept of `project` is not supported "
        "within the Dashboard. The Project functionality will be "
        "completed in the coming weeks. For the time being it "
        "is recommended to stay within the `default` project."
    )


@cli.group(cls=TagGroup, tag=CliCategories.MANAGEMENT_TOOLS)
def project() -> None:
    """Commands for project management."""


@project.command("list", hidden=True)
def list_projects() -> None:
    """List all projects."""
    warn_unsupported_non_default_project()
    cli_utils.print_active_config()
    projects = Client().zen_store.list_projects()

    if projects:
        active_project = Client().active_project
        active_project_id = active_project.id if active_project else None
        cli_utils.print_pydantic_models(
            projects,
            exclude_columns=["id", "created", "updated"],
            is_active=(lambda p: p.id == active_project_id),
        )
    else:
        cli_utils.declare("No projects registered.")


@project.command("create", help="Create a new project.", hidden=True)
@click.argument("project_name", type=str, required=True)
@click.option("--description", "-d", type=str, required=False, default="")
def create_project(project_name: str, description: str) -> None:
    """Create a new project.

    Args:
        project_name: The name of the project.
        description: A description of the project.
    """
    warn_unsupported_non_default_project()
    cli_utils.print_active_config()
    try:
        from zenml.models import ProjectModel

        Client().zen_store.create_project(
            ProjectModel(name=project_name, description=description)
        )
    except EntityExistsError as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Created project '{project_name}'.")


@project.command("update", help="Update an existing project.", hidden=True)
@click.argument("project_name", type=str, required=True)
@click.option(
    "--name", "-n", type=str, required=False, help="New project name."
)
@click.option(
    "--description",
    "-d",
    type=str,
    required=False,
    help="New project description.",
)
def update_project(
    project_name: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """Update an existing project.

    Args:
        project_name: The name of the project.
        name: The new name of the project.
        description: The new description of the project.
    """
    warn_unsupported_non_default_project()
    cli_utils.print_active_config()
    try:
        project = Client().zen_store.get_project(project_name)
        project.name = name or project.name
        project.description = description or project.description
        Client().zen_store.update_project(project)
    except (EntityExistsError, KeyError, IllegalOperationError) as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Updated project '{project_name}'.")


@project.command("get", hidden=True)
def get_project() -> None:
    """Get the currently active project."""
    warn_unsupported_non_default_project()
    active_project = Client().active_project
    description = (
        "\nDescription: " + active_project.description
        if active_project.description
        else ""
    )
    cli_utils.declare(f"ACTIVE PROJECT: {active_project.name}{description}")


@project.command("set", help="Set the active project.", hidden=True)
@click.argument("project_name_or_id", type=str, required=True)
def set_project(project_name_or_id: str) -> None:
    """Set the active project.

    Args:
        project_name_or_id: The name or ID of the project to set as active.
    """
    warn_unsupported_non_default_project()
    cli_utils.print_active_config()
    try:
        Client().set_active_project(project_name_or_id=project_name_or_id)
    except KeyError as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Set active project '{project_name_or_id}'.")


@project.command("delete", help="Delete a project.", hidden=True)
@click.argument("project_name_or_id", type=str, required=True)
def delete_project(project_name_or_id: str) -> None:
    """Delete a project.

    Args:
        project_name_or_id: Name or ID of project to delete.
    """
    warn_unsupported_non_default_project()
    cli_utils.print_active_config()
    confirmation = cli_utils.confirmation(
        f"Are you sure you want to delete project `{project_name_or_id}`? "
        "This will permanently delete all associated stacks, stack components, "
        "pipelines, runs, artifacts and metadata."
    )
    if not confirmation:
        cli_utils.declare("Project deletion canceled.")
        return
    try:
        Client().delete_project(project_name_or_id)
    except (KeyError, IllegalOperationError) as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Deleted project '{project_name_or_id}'.")


@cli.group(cls=TagGroup, tag=CliCategories.IDENTITY_AND_SECURITY)
def role() -> None:
    """Commands for role management."""


@role.command("list")
def list_roles() -> None:
    """List all roles."""
    cli_utils.print_active_config()
    roles = Client().zen_store.roles
    if not roles:
        cli_utils.declare("No roles registered.")
        return
    cli_utils.print_pydantic_models(
        roles,
        exclude_columns=["created", "updated"],
    )


@role.command("create", help="Create a new role.")
@click.argument("role_name", type=str, required=True)
@click.option(
    "--permissions",
    "-p",
    "permissions",
    type=click.Choice(choices=PermissionType.values()),
    multiple=True,
    help="Name of permission to attach to this role.",
)
def create_role(role_name: str, permissions: List[str]) -> None:
    """Create a new role.

    Args:
        role_name: Name of the role to create.
        permissions: Permissions to assign
    """
    cli_utils.print_active_config()

    from zenml.models import RoleModel

    Client().create_role(name=role_name, permissions_list=permissions)
    cli_utils.declare(f"Created role '{role_name}'.")


@role.command("update", help="Update an existing role.")
@click.argument("role_name", type=str, required=True)
@click.option("--name", "-n", "new_name", type=str, required=False, help="New role name.")
@click.option(
    "--remove-permission",
    "-r",
    type=click.Choice(choices=PermissionType.values()),
    multiple=True,
    help="Name of permission to remove.",
)
@click.option(
    "--add-permission",
    "-a",
    type=click.Choice(choices=PermissionType.values()),
    multiple=True,
    help="Name of permission to add.",
)
def update_role(
    role_name: str,
    new_name: Optional[str] = None,
    remove_permission: Optional[List[str]] = None,
    add_permission: Optional[List[str]] = None,
) -> None:
    """Update an existing role.

    Args:
        role_name: The name of the role.
        new_name: The new name of the role.
        remove_permission: Name of permission to remove from role
        add_permission: Name of permission to add to role
    """
    cli_utils.print_active_config()

    union_add_rm = set(remove_permission) & set(add_permission)
    if union_add_rm:
        cli_utils.error(f"The `--remove-permission` and `--add-permission` "
                        f"options both contain the same value: "
                        f"`{union_add_rm}`. Please rerun command and make sure "
                        f"that the same role does not show up for "
                        f"`--remove-permission` and `--add-permission`.")

    try:
        Client().update_role(
            name_id_or_prefix=role_name,
            new_name=new_name,
            remove_permission=remove_permission,
            add_permission=add_permission,
        )
    except (EntityExistsError, KeyError, IllegalOperationError) as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Updated role '{role_name}'.")


@role.command("delete", help="Delete a role.")
@click.argument("role_name_or_id", type=str, required=True)
def delete_role(role_name_or_id: str) -> None:
    """Delete a role.

    Args:
        role_name_or_id: Name or ID of the role to delete.
    """
    cli_utils.print_active_config()
    try:
        Client().zen_store.delete_role(
            role_name_or_id=parse_name_or_uuid(role_name_or_id)
        )
    except (KeyError, IllegalOperationError) as err:
        cli_utils.error(str(err))
    cli_utils.declare(f"Deleted role '{role_name_or_id}'.")


@role.command("assign", help="Assign a role.")
@click.argument("role_name_or_id", type=str, required=True)
@click.option("--project", "project_name_or_id", type=str, required=False)
@click.option(
    "--user", "user_names_or_ids", type=str, required=False, multiple=True
)
@click.option(
    "--team", "team_names_or_ids", type=str, required=False, multiple=True
)
def assign_role(
    role_name_or_id: str,
    user_names_or_ids: Tuple[str],
    team_names_or_ids: Tuple[str],
    project_name_or_id: Optional[str] = None,
) -> None:
    """Assign a role.

    Args:
        role_name_or_id: Name or IDs of the role to assign.
        user_names_or_ids : Names or IDs of users to assign the role to.
        team_names_or_ids: Names or IDs of teams to assign the role to.
        project_name_or_id: Name or IDs of a project in which to assign the
            role. If this is not provided, the role will be assigned globally.
    """
    cli_utils.print_active_config()

    # Assign the role to users
    for user_name_or_id in user_names_or_ids:
        try:
            Client().zen_store.assign_role(
                role_name_or_id=role_name_or_id,
                user_or_team_name_or_id=user_name_or_id,
                is_user=True,
                project_name_or_id=project_name_or_id,
            )
        except KeyError as err:
            cli_utils.error(str(err))
        except EntityExistsError as err:
            cli_utils.warning(str(err))
        else:
            cli_utils.declare(
                f"Assigned role '{role_name_or_id}' to user '{user_name_or_id}'."
            )

    # Assign the role to teams
    for team_name_or_id in team_names_or_ids:
        try:
            Client().zen_store.assign_role(
                role_name_or_id=role_name_or_id,
                user_or_team_name_or_id=team_name_or_id,
                is_user=False,
                project_name_or_id=project_name_or_id,
            )
        except KeyError as err:
            cli_utils.error(str(err))
        except EntityExistsError as err:
            cli_utils.warning(str(err))
        else:
            cli_utils.declare(
                f"Assigned role '{role_name_or_id}' to team '{team_name_or_id}'."
            )


@role.command("revoke", help="Revoke a role.")
@click.argument("role_name_or_id", type=str, required=True)
@click.option("--project", "project_name_or_id", type=str, required=False)
@click.option(
    "--user", "user_names_or_ids", type=str, required=False, multiple=True
)
@click.option(
    "--team", "team_names_or_ids", type=str, required=False, multiple=True
)
def revoke_role(
    role_name_or_id: str,
    user_names_or_ids: Tuple[str],
    team_names_or_ids: Tuple[str],
    project_name_or_id: Optional[str] = None,
) -> None:
    """Revoke a role.

    Args:
        role_name_or_id: Name or IDs of the role to revoke.
        user_names_or_ids: Names or IDs of users from which to revoke the role.
        team_names_or_ids: Names or IDs of teams from which to revoke the role.
        project_name_or_id: Name or IDs of a project in which to revoke the
            role. If this is not provided, the role will be revoked globally.
    """
    cli_utils.print_active_config()

    # Revoke the role from users
    for user_name_or_id in user_names_or_ids:
        try:
            Client().zen_store.revoke_role(
                role_name_or_id=role_name_or_id,
                user_or_team_name_or_id=user_name_or_id,
                is_user=True,
                project_name_or_id=project_name_or_id,
            )
        except KeyError as err:
            cli_utils.warning(str(err))
        else:
            cli_utils.declare(
                f"Revoked role '{role_name_or_id}' from user "
                f"'{user_name_or_id}'."
            )

    # Revoke the role from teams
    for team_name_or_id in team_names_or_ids:
        try:
            Client().zen_store.revoke_role(
                role_name_or_id=role_name_or_id,
                user_or_team_name_or_id=team_name_or_id,
                is_user=False,
                project_name_or_id=project_name_or_id,
            )
        except KeyError as err:
            cli_utils.warning(str(err))
        else:
            cli_utils.declare(
                f"Revoked role '{role_name_or_id}' from team "
                f"'{team_name_or_id}'."
            )


@role.group()
def assignment() -> None:
    """Commands for role management."""


@assignment.command("list")
@click.option("--role", "role_name_or_id", type=str, required=False)
@click.option("--project", "project_name_or_id", type=str, required=False)
@click.option(
    "--user",
    "user_name_or_id",
    type=str,
    required=False,
)
@click.option(
    "--team",
    "team_name_or_id",
    type=str,
    required=False,
)
def list_role_assignments(
    role_name_or_id: Optional[str] = None,
    user_name_or_id: Optional[str] = None,
    team_name_or_id: Optional[str] = None,
    project_name_or_id: Optional[str] = None,
) -> None:
    """List all role assignments.

    Args:
        role_name_or_id: Name or ID of a role to list role assignments for.
        user_name_or_id: Name or ID of a user to list role assignments for.
        team_name_or_id: Name or ID of a team to list role assignments for.
        project_name_or_id: Name or ID of a project to list role assignments
            for.
    """
    cli_utils.print_active_config()
    # Hacky workaround while role assignments are scoped to the user endpoint
    role_assignments = []
    for user in Client().zen_store.users:
        role_assignments.extend(
            Client().zen_store.list_role_assignments(
                user_name_or_id=user.id,
                role_name_or_id=role_name_or_id,
                team_name_or_id=team_name_or_id,
                project_name_or_id=project_name_or_id,
            )
        )
    if not role_assignments:
        cli_utils.declare("No roles assigned.")
        return
    cli_utils.print_pydantic_models(role_assignments)


@cli.group(cls=TagGroup, tag=CliCategories.IDENTITY_AND_SECURITY)
def permission() -> None:
    """Commands for role management."""


@permission.command("list")
def list_permissions() -> None:
    """List all role assignments."""
    cli_utils.print_active_config()
    permissions = [i.value for i in PermissionType]
    cli_utils.declare(
        f"The following permissions are currently supported: " f"{permissions}"
    )
