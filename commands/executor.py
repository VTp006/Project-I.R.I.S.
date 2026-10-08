from typing import Any, Callable

from commands.registry import (
    Command,
    get_command,
)


class CommandResult:
    """Result returned after executing a command."""

    def __init__(
        self,
        success: bool,
        message: str = "",
        data: Any = None,
        error: str | None = None,
    ):
        self.success = success
        self.message = message
        self.data = data
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
        }

    def __repr__(self) -> str:
        return (
            f"CommandResult("
            f"success={self.success}, "
            f"message={self.message!r}, "
            f"error={self.error!r})"
        )


class CommandExecutor:
    """
    Central command execution system for IRIS.

    Responsibilities:
    - Validate commands
    - Validate parameters
    - Check confirmation requirements
    - Check dangerous commands
    - Dispatch commands to handlers
    - Return structured results
    """

    def __init__(self):
        self.handlers: dict[str, Callable[..., Any]] = {}

    # region HANDLER REGISTRATION

    def register_handler(
        self,
        command_name: str,
        handler: Callable[..., Any],
    ) -> None:
        """Register a function to execute a command."""

        if get_command(command_name) is None:
            raise ValueError(
                f"Cannot register handler: "
                f"unknown command '{command_name}'"
            )

        self.handlers[command_name] = handler

    def register_handlers(
        self,
        handlers: dict[str, Callable[..., Any]],
    ) -> None:
        """Register multiple command handlers."""

        for command_name, handler in handlers.items():
            self.register_handler(command_name, handler)

    # endregion

    # region VALIDATION

    def validate_command(
        self,
        command_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> CommandResult:
        """Validate whether a command can be executed."""

        command = get_command(command_name)

        if command is None:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command_name}",
            )

        parameters = parameters or {}

        missing_parameters = []

        for parameter in command.parameters:
            if parameter not in parameters:
                missing_parameters.append(parameter)

        if missing_parameters:
            return CommandResult(
                success=False,
                error=(
                    f"Missing parameters for {command_name}: "
                    f"{', '.join(missing_parameters)}"
                ),
            )

        return CommandResult(
            success=True,
            message=f"Command '{command_name}' is valid.",
        )

    # endregion

    # region CONFIRMATION

    def requires_confirmation(self, command_name: str) -> bool:
        """Check whether a command requires user confirmation."""

        command = get_command(command_name)

        if command is None:
            return False

        return command.requires_confirmation or command.dangerous

    # endregion

    # region EXECUTION

    def execute(
        self,
        command_name: str,
        parameters: dict[str, Any] | None = None,
        confirmed: bool = False,
    ) -> CommandResult:
        """
        Execute a registered command.

        Parameters:
            command_name:
                Name of the command from the registry.

            parameters:
                Parameters required by the command.

            confirmed:
                Whether the user has explicitly confirmed
                a command that requires confirmation.
        """

        parameters = parameters or {}

        # Validate command
        validation = self.validate_command(
            command_name,
            parameters,
        )

        if not validation.success:
            return validation

        command = get_command(command_name)

        if command is None:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command_name}",
            )

        # Check confirmation
        if self.requires_confirmation(command_name):
            if not confirmed:
                return CommandResult(
                    success=False,
                    message=(
                        f"Confirmation required for "
                        f"'{command_name}'."
                    ),
                    error="CONFIRMATION_REQUIRED",
                )

        # Check handler
        handler = self.handlers.get(command_name)

        if handler is None:
            return CommandResult(
                success=False,
                error=(
                    f"No handler registered for "
                    f"'{command_name}'."
                ),
            )

        # Execute handler
        try:
            result = handler(**parameters)

            # Handler returned CommandResult
            if isinstance(result, CommandResult):
                return result

            # Handler returned a normal value
            return CommandResult(
                success=True,
                message=(
                    f"Command '{command_name}' "
                    f"executed successfully."
                ),
                data=result,
            )

        except Exception as error:
            return CommandResult(
                success=False,
                error=str(error),
            )

    # endregion

    # region INFORMATION

    def has_handler(self, command_name: str) -> bool:
        """Check whether a handler exists."""

        return command_name in self.handlers

    def get_registered_handlers(self) -> list[str]:
        """Return all commands that have handlers."""

        return list(self.handlers.keys())

    def get_missing_handlers(self) -> list[str]:
        """Return registry commands that don't have handlers yet."""

        from commands.registry import ALL_COMMANDS

        return [
            command.name
            for command in ALL_COMMANDS
            if command.name not in self.handlers
        ]

    # endregion


# region GLOBAL EXECUTOR

executor = CommandExecutor()

# endregion