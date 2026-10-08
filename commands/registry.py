from dataclasses import dataclass
from enum import Enum
from typing import Any


# region COMMAND DOMAINS

class CommandDomain(Enum):
    FILES = "files"
    APPLICATIONS = "applications"
    BROWSER = "browser"
    WINDOWS = "windows"
    SYSTEM = "system"
    AUDIO_MEDIA = "audio_media"
    SCREEN_INPUT = "screen_input"
    PRODUCTIVITY = "productivity"
    CLIPBOARD = "clipboard"
    SEARCH_INFORMATION = "search_information"
    NETWORK = "network"
    HARDWARE = "hardware"
    SECURITY = "security"
    PROCESSES = "processes"
    SOFTWARE = "software"
    IRIS = "iris"
    AI = "ai"
    AUTOMATION = "automation"


# endregion


# region COMMAND MODEL

@dataclass(frozen=True)
class Command:
    name: str
    domain: CommandDomain
    description: str
    parameters: list[str]
    requires_confirmation: bool = False
    dangerous: bool = False


# endregion


# region FILES & FOLDERS

FILES_COMMANDS = [
    Command("OPEN_FILE", CommandDomain.FILES, "Open a file.", ["path"]),
    Command("CLOSE_FILE", CommandDomain.FILES, "Close an open file.", ["path"]),
    Command("CREATE_FILE", CommandDomain.FILES, "Create a new file.", ["path", "type"]),
    Command(
        "DELETE_FILE",
        CommandDomain.FILES,
        "Delete a file.",
        ["path"],
        requires_confirmation=True,
        dangerous=True,
    ),
    Command("EDIT_FILE", CommandDomain.FILES, "Edit a file.", ["path", "content"]),
    Command("READ_FILE", CommandDomain.FILES, "Read file contents.", ["path"]),
    Command("OPEN_FOLDER", CommandDomain.FILES, "Open a folder.", ["path"]),
    Command("CLOSE_FOLDER", CommandDomain.FILES, "Close a folder.", ["path"]),
    Command("CREATE_FOLDER", CommandDomain.FILES, "Create a folder.", ["path"]),
    Command(
        "DELETE_FOLDER",
        CommandDomain.FILES,
        "Delete a folder.",
        ["path"],
        requires_confirmation=True,
        dangerous=True,
    ),
    Command(
        "CONFIRM_DELETION",
        CommandDomain.FILES,
        "Confirm a pending deletion.",
        [],
    ),
    Command(
        "CANCEL_DELETION",
        CommandDomain.FILES,
        "Cancel a pending deletion.",
        [],
    ),
    Command("RENAME_FILE", CommandDomain.FILES, "Rename a file.", ["path", "new_name"]),
    Command(
        "RENAME_FOLDER",
        CommandDomain.FILES,
        "Rename a folder.",
        ["path", "new_name"],
    ),
    Command("COPY_FILE", CommandDomain.FILES, "Copy a file.", ["source", "destination"]),
    Command(
        "COPY_FOLDER",
        CommandDomain.FILES,
        "Copy a folder.",
        ["source", "destination"],
    ),
    Command("MOVE_FILE", CommandDomain.FILES, "Move a file.", ["source", "destination"]),
    Command(
        "MOVE_FOLDER",
        CommandDomain.FILES,
        "Move a folder.",
        ["source", "destination"],
    ),
    Command("SEARCH_FILE", CommandDomain.FILES, "Search for a file.", ["query"]),
    Command("SEARCH_FOLDER", CommandDomain.FILES, "Search for a folder.", ["query"]),
    Command("LIST_FOLDER", CommandDomain.FILES, "List folder contents.", ["path"]),
    Command("GET_FILE_INFO", CommandDomain.FILES, "Get file information.", ["path"]),
    Command("GET_FOLDER_INFO", CommandDomain.FILES, "Get folder information.", ["path"]),
    Command("COMPRESS_FILE", CommandDomain.FILES, "Compress a file or folder.", ["path"]),
    Command(
        "EXTRACT_FILE",
        CommandDomain.FILES,
        "Extract an archive.",
        ["path", "destination"],
    ),
    Command(
        "EMPTY_RECYCLE_BIN",
        CommandDomain.FILES,
        "Empty the recycle bin.",
        [],
        requires_confirmation=True,
        dangerous=True,
    ),
]

# endregion


# region APPLICATIONS

APPLICATION_COMMANDS = [
    Command("OPEN_APP", CommandDomain.APPLICATIONS, "Open an application.", ["app"]),
    Command("CLOSE_APP", CommandDomain.APPLICATIONS, "Close an application.", ["app"]),
    Command("RESTART_APP", CommandDomain.APPLICATIONS, "Restart an application.", ["app"]),
    Command("MINIMIZE_APP", CommandDomain.APPLICATIONS, "Minimize an application.", ["app"]),
    Command("MAXIMIZE_APP", CommandDomain.APPLICATIONS, "Maximize an application.", ["app"]),
    Command("FOCUS_APP", CommandDomain.APPLICATIONS, "Focus an application.", ["app"]),
    Command("SWITCH_APP", CommandDomain.APPLICATIONS, "Switch to an application.", ["app"]),
    Command(
        "INSTALL_APP",
        CommandDomain.APPLICATIONS,
        "Install an application.",
        ["app"],
        requires_confirmation=True,
    ),
    Command(
        "UNINSTALL_APP",
        CommandDomain.APPLICATIONS,
        "Uninstall an application.",
        ["app"],
        requires_confirmation=True,
        dangerous=True,
    ),
    Command(
        "CHECK_APP_STATUS",
        CommandDomain.APPLICATIONS,
        "Check application status.",
        ["app"],
    ),
]

# endregion


# region BROWSER

BROWSER_COMMANDS = [
    Command("OPEN_WEBSITE", CommandDomain.BROWSER, "Open a website.", ["url"]),
    Command("CLOSE_WEBSITE", CommandDomain.BROWSER, "Close a website.", ["url"]),
    Command("CHANGE_TAB", CommandDomain.BROWSER, "Change browser tab.", ["tab"]),
    Command("GOOGLE_SEARCH", CommandDomain.BROWSER, "Search Google.", ["query"]),
    Command("NEW_TAB", CommandDomain.BROWSER, "Open a new browser tab.", []),
    Command("CLOSE_TAB", CommandDomain.BROWSER, "Close the current tab.", []),
    Command("REOPEN_TAB", CommandDomain.BROWSER, "Reopen the last closed tab.", []),
    Command("SWITCH_TAB", CommandDomain.BROWSER, "Switch browser tab.", ["tab"]),
    Command("BACK", CommandDomain.BROWSER, "Go back one page.", []),
    Command("FORWARD", CommandDomain.BROWSER, "Go forward one page.", []),
    Command("REFRESH_PAGE", CommandDomain.BROWSER, "Refresh the current page.", []),
    Command("GO_TO_URL", CommandDomain.BROWSER, "Navigate to a URL.", ["url"]),
    Command("DOWNLOAD_FILE", CommandDomain.BROWSER, "Download a file.", ["url"]),
    Command("STOP_DOWNLOAD", CommandDomain.BROWSER, "Stop a download.", []),
    Command("SEARCH_WEBSITE", CommandDomain.BROWSER, "Search the current website.", ["query"]),
    Command("BOOKMARK_PAGE", CommandDomain.BROWSER, "Bookmark the current page.", []),
    Command("OPEN_BOOKMARK", CommandDomain.BROWSER, "Open a bookmark.", ["bookmark"]),
    Command(
        "CLEAR_BROWSER_DATA",
        CommandDomain.BROWSER,
        "Clear browser data.",
        [],
        requires_confirmation=True,
    ),
]

# endregion


# region WINDOWS & DESKTOP CONTROL

WINDOW_COMMANDS = [
    Command("MINIMIZE_WINDOW", CommandDomain.WINDOWS, "Minimize a window.", ["window"]),
    Command("MAXIMIZE_WINDOW", CommandDomain.WINDOWS, "Maximize a window.", ["window"]),
    Command("RESTORE_WINDOW", CommandDomain.WINDOWS, "Restore a window.", ["window"]),
    Command("MOVE_WINDOW", CommandDomain.WINDOWS, "Move a window.", ["window", "x", "y"]),
    Command(
        "RESIZE_WINDOW",
        CommandDomain.WINDOWS,
        "Resize a window.",
        ["window", "width", "height"],
    ),
    Command("FOCUS_WINDOW", CommandDomain.WINDOWS, "Focus a window.", ["window"]),
    Command("SWITCH_WINDOW", CommandDomain.WINDOWS, "Switch to a window.", ["window"]),
    Command(
        "CLOSE_WINDOW",
        CommandDomain.WINDOWS,
        "Close a window.",
        ["window"],
        requires_confirmation=True,
    ),
    Command("SNAP_WINDOW", CommandDomain.WINDOWS, "Snap a window.", ["window", "position"]),
    Command("SHOW_DESKTOP", CommandDomain.WINDOWS, "Show the desktop.", []),
    Command("LOCK_SCREEN", CommandDomain.WINDOWS, "Lock the screen.", []),
]

# endregion


# region SYSTEM CONTROL

SYSTEM_COMMANDS = [
    Command("EXIT", CommandDomain.SYSTEM, "Exit IRIS.", []),
    Command(
        "SHUTDOWN",
        CommandDomain.SYSTEM,
        "Shut down the computer.",
        [],
        requires_confirmation=True,
        dangerous=True,
    ),
    Command(
        "RESTART",
        CommandDomain.SYSTEM,
        "Restart the computer.",
        [],
        requires_confirmation=True,
    ),
    Command("SLEEP", CommandDomain.SYSTEM, "Put the computer to sleep.", []),
    Command("HIBERNATE", CommandDomain.SYSTEM, "Hibernate the computer.", []),
    Command("LOCK_PC", CommandDomain.SYSTEM, "Lock the computer.", []),
    Command(
        "LOG_OUT",
        CommandDomain.SYSTEM,
        "Log out the current user.",
        [],
        requires_confirmation=True,
    ),
    Command(
        "CANCEL_SHUTDOWN",
        CommandDomain.SYSTEM,
        "Cancel a pending shutdown.",
        [],
    ),
    Command("SYSTEM_INFO", CommandDomain.SYSTEM, "Get system information.", []),
    Command("CPU_USAGE", CommandDomain.SYSTEM, "Get current CPU usage.", []),
    Command("GPU_USAGE", CommandDomain.SYSTEM, "Get current GPU usage.", []),
    Command("RAM_USAGE", CommandDomain.SYSTEM, "Get current RAM usage.", []),
    Command("DISK_USAGE", CommandDomain.SYSTEM, "Get current disk usage.", []),
    Command("BATTERY_STATUS", CommandDomain.SYSTEM, "Get battery status.", []),
    Command("NETWORK_STATUS", CommandDomain.SYSTEM, "Get network status.", []),
    Command("OS_INFO", CommandDomain.SYSTEM, "Get operating system information.", []),
]

# endregion


# region AUDIO & MEDIA

AUDIO_MEDIA_COMMANDS = [
    Command("PLAY_MUSIC", CommandDomain.AUDIO_MEDIA, "Play music.", ["source"]),
    Command("PAUSE_MEDIA", CommandDomain.AUDIO_MEDIA, "Pause media.", []),
    Command("RESUME_MEDIA", CommandDomain.AUDIO_MEDIA, "Resume media.", []),
    Command("STOP_MEDIA", CommandDomain.AUDIO_MEDIA, "Stop media.", []),
    Command("NEXT_TRACK", CommandDomain.AUDIO_MEDIA, "Play the next track.", []),
    Command("PREVIOUS_TRACK", CommandDomain.AUDIO_MEDIA, "Play the previous track.", []),
    Command("VOLUME_UP", CommandDomain.AUDIO_MEDIA, "Increase volume.", []),
    Command("VOLUME_DOWN", CommandDomain.AUDIO_MEDIA, "Decrease volume.", []),
    Command("SET_VOLUME", CommandDomain.AUDIO_MEDIA, "Set system volume.", ["level"]),
    Command("MUTE", CommandDomain.AUDIO_MEDIA, "Mute audio.", []),
    Command("UNMUTE", CommandDomain.AUDIO_MEDIA, "Unmute audio.", []),
    Command("PLAY_VIDEO", CommandDomain.AUDIO_MEDIA, "Play a video.", ["source"]),
    Command("STOP_VIDEO", CommandDomain.AUDIO_MEDIA, "Stop video playback.", []),
]

# endregion


# region SCREEN & INPUT

SCREEN_INPUT_COMMANDS = [
    Command("SCREENSHOT", CommandDomain.SCREEN_INPUT, "Take a screenshot.", []),
    Command("SCREENSHOT_FULL", CommandDomain.SCREEN_INPUT, "Take a full-screen screenshot.", []),
    Command("SCREENSHOT_WINDOW", CommandDomain.SCREEN_INPUT, "Screenshot a window.", ["window"]),
    Command("SCREENSHOT_REGION", CommandDomain.SCREEN_INPUT, "Screenshot a screen region.", ["region"]),
    Command("SCREEN_RECORD", CommandDomain.SCREEN_INPUT, "Start screen recording.", []),
    Command("STOP_SCREEN_RECORD", CommandDomain.SCREEN_INPUT, "Stop screen recording.", []),
    Command("TYPE_TEXT", CommandDomain.SCREEN_INPUT, "Type text.", ["text"]),
    Command("PRESS_KEY", CommandDomain.SCREEN_INPUT, "Press a keyboard key.", ["key"]),
    Command("PRESS_KEYS", CommandDomain.SCREEN_INPUT, "Press multiple keys.", ["keys"]),
    Command("MOUSE_CLICK", CommandDomain.SCREEN_INPUT, "Click the mouse.", ["button"]),
    Command("MOUSE_MOVE", CommandDomain.SCREEN_INPUT, "Move the mouse.", ["x", "y"]),
    Command("SCROLL", CommandDomain.SCREEN_INPUT, "Scroll the mouse wheel.", ["amount"]),
    Command("DRAG", CommandDomain.SCREEN_INPUT, "Drag the mouse.", ["start", "end"]),
]

# endregion


# region PRODUCTIVITY

PRODUCTIVITY_COMMANDS = [
    Command("CREATE_NOTE", CommandDomain.PRODUCTIVITY, "Create a note.", ["content"]),
    Command("READ_NOTE", CommandDomain.PRODUCTIVITY, "Read a note.", ["name"]),
    Command("EDIT_NOTE", CommandDomain.PRODUCTIVITY, "Edit a note.", ["name", "content"]),
    Command(
        "DELETE_NOTE",
        CommandDomain.PRODUCTIVITY,
        "Delete a note.",
        ["name"],
        requires_confirmation=True,
    ),
    Command("OPEN_DOCUMENT", CommandDomain.PRODUCTIVITY, "Open a document.", ["path"]),
    Command(
        "CREATE_DOCUMENT",
        CommandDomain.PRODUCTIVITY,
        "Create a document.",
        ["path", "type"],
    ),
    Command("OPEN_CALENDAR", CommandDomain.PRODUCTIVITY, "Open the calendar.", []),
    Command(
        "CREATE_REMINDER",
        CommandDomain.PRODUCTIVITY,
        "Create a reminder.",
        ["text", "time"],
    ),
    Command("SET_TIMER", CommandDomain.PRODUCTIVITY, "Set a timer.", ["duration"]),
    Command("CANCEL_TIMER", CommandDomain.PRODUCTIVITY, "Cancel a timer.", []),
]

# endregion


# region CLIPBOARD

CLIPBOARD_COMMANDS = [
    Command("COPY", CommandDomain.CLIPBOARD, "Copy selected content.", []),
    Command("PASTE", CommandDomain.CLIPBOARD, "Paste clipboard content.", []),
    Command("READ_CLIPBOARD", CommandDomain.CLIPBOARD, "Read clipboard contents.", []),
    Command("WRITE_CLIPBOARD", CommandDomain.CLIPBOARD, "Write text to clipboard.", ["text"]),
    Command("CLEAR_CLIPBOARD", CommandDomain.CLIPBOARD, "Clear the clipboard.", []),
    Command("CLIPBOARD_HISTORY", CommandDomain.CLIPBOARD, "View clipboard history.", []),
]

# endregion


# region SEARCH & INFORMATION

SEARCH_INFORMATION_COMMANDS = [
    Command("WEB_SEARCH", CommandDomain.SEARCH_INFORMATION, "Search the web.", ["query"]),
    Command("SEARCH_PC", CommandDomain.SEARCH_INFORMATION, "Search the computer.", ["query"]),
    Command("SEARCH_FILES", CommandDomain.SEARCH_INFORMATION, "Search files on the computer.", ["query"]),
    Command("CALCULATE", CommandDomain.SEARCH_INFORMATION, "Perform a calculation.", ["expression"]),
    Command("GET_DATE", CommandDomain.SEARCH_INFORMATION, "Get the current date.", []),
    Command("GET_TIME", CommandDomain.SEARCH_INFORMATION, "Get the current time.", []),
    Command("WEATHER", CommandDomain.SEARCH_INFORMATION, "Get weather information.", ["location"]),
    Command("NEWS", CommandDomain.SEARCH_INFORMATION, "Get current news.", ["topic"]),
]

# endregion


# region NETWORK

NETWORK_COMMANDS = [
    Command("WIFI_ON", CommandDomain.NETWORK, "Turn Wi-Fi on.", []),
    Command("WIFI_OFF", CommandDomain.NETWORK, "Turn Wi-Fi off.", []),
    Command("WIFI_STATUS", CommandDomain.NETWORK, "Get Wi-Fi status.", []),
    Command("CONNECT_WIFI", CommandDomain.NETWORK, "Connect to a Wi-Fi network.", ["network"]),
    Command("DISCONNECT_WIFI", CommandDomain.NETWORK, "Disconnect from Wi-Fi.", []),
    Command("BLUETOOTH_ON", CommandDomain.NETWORK, "Turn Bluetooth on.", []),
    Command("BLUETOOTH_OFF", CommandDomain.NETWORK, "Turn Bluetooth off.", []),
    Command("BLUETOOTH_STATUS", CommandDomain.NETWORK, "Get Bluetooth status.", []),
    Command("NETWORK_INFO", CommandDomain.NETWORK, "Get network information.", []),
    Command("PING_HOST", CommandDomain.NETWORK, "Ping a host.", ["host"]),
]

# endregion


# region HARDWARE

HARDWARE_COMMANDS = [
    Command("BATTERY_HEALTH", CommandDomain.HARDWARE, "Get battery health.", []),
    Command("CPU_STATUS", CommandDomain.HARDWARE, "Get CPU status and information.", []),
    Command("GPU_STATUS", CommandDomain.HARDWARE, "Get GPU status and information.", []),
    Command("RAM_STATUS", CommandDomain.HARDWARE, "Get RAM status and information.", []),
    Command("DISK_STATUS", CommandDomain.HARDWARE, "Get disk status and information.", []),
    Command("TEMPERATURE_STATUS", CommandDomain.HARDWARE, "Get hardware temperatures.", []),
    Command("DISPLAY_INFO", CommandDomain.HARDWARE, "Get display information.", []),
    Command("AUDIO_DEVICE_INFO", CommandDomain.HARDWARE, "Get audio device information.", []),
    Command("MICROPHONE_STATUS", CommandDomain.HARDWARE, "Get microphone status.", []),
]

# endregion


# region SECURITY

SECURITY_COMMANDS = [
    Command(
        "CHANGE_PASSWORD",
        CommandDomain.SECURITY,
        "Change the user password.",
        [],
        requires_confirmation=True,
    ),
    Command(
        "ENABLE_FIREWALL",
        CommandDomain.SECURITY,
        "Enable the firewall.",
        [],
        requires_confirmation=True,
    ),
    Command(
        "DISABLE_FIREWALL",
        CommandDomain.SECURITY,
        "Disable the firewall.",
        [],
        requires_confirmation=True,
        dangerous=True,
    ),
    Command(
        "CHECK_SECURITY_STATUS",
        CommandDomain.SECURITY,
        "Check security status.",
        [],
    ),
    Command(
        "CHECK_RUNNING_PROCESSES",
        CommandDomain.SECURITY,
        "Check running processes.",
        [],
    ),
]

# endregion


# region PROCESS MANAGEMENT

PROCESS_COMMANDS = [
    Command("LIST_PROCESSES", CommandDomain.PROCESSES, "List running processes.", []),
    Command("FIND_PROCESS", CommandDomain.PROCESSES, "Find a process.", ["query"]),
    Command("PROCESS_INFO", CommandDomain.PROCESSES, "Get process information.", ["process"]),
    Command("START_PROCESS", CommandDomain.PROCESSES, "Start a process.", ["process"]),
    Command("STOP_PROCESS", CommandDomain.PROCESSES, "Stop a process.", ["process"]),
    Command(
        "KILL_PROCESS",
        CommandDomain.PROCESSES,
        "Forcefully terminate a process.",
        ["process"],
        requires_confirmation=True,
        dangerous=True,
    ),
    Command(
        "CHECK_PROCESS_STATUS",
        CommandDomain.PROCESSES,
        "Check process status.",
        ["process"],
    ),
]

# endregion


# region PACKAGE / SOFTWARE MANAGEMENT

SOFTWARE_COMMANDS = [
    Command(
        "INSTALL_SOFTWARE",
        CommandDomain.SOFTWARE,
        "Install software.",
        ["software"],
        requires_confirmation=True,
    ),
    Command(
        "UNINSTALL_SOFTWARE",
        CommandDomain.SOFTWARE,
        "Uninstall software.",
        ["software"],
        requires_confirmation=True,
        dangerous=True,
    ),
    Command(
        "UPDATE_SOFTWARE",
        CommandDomain.SOFTWARE,
        "Update software.",
        ["software"],
        requires_confirmation=True,
    ),
    Command("CHECK_UPDATES", CommandDomain.SOFTWARE, "Check for software updates.", []),
    Command(
        "LIST_INSTALLED_SOFTWARE",
        CommandDomain.SOFTWARE,
        "List installed software.",
        [],
    ),
    Command("LAUNCH_SOFTWARE", CommandDomain.SOFTWARE, "Launch software.", ["software"]),
]

# endregion


# region IRIS CONTROLS

IRIS_COMMANDS = [
    Command("WAKE_WORD", CommandDomain.IRIS, "Get the current wake word.", []),
    Command("ENABLE_WAKE_WORD", CommandDomain.IRIS, "Enable wake word detection.", []),
    Command("DISABLE_WAKE_WORD", CommandDomain.IRIS, "Disable wake word detection.", []),
    Command("CHANGE_WAKE_WORD", CommandDomain.IRIS, "Change the wake word.", ["wake_word"]),
    Command("VOICE_MODE", CommandDomain.IRIS, "Enable voice mode.", []),
    Command("TEXT_MODE", CommandDomain.IRIS, "Enable text mode.", []),
    Command("SLEEP_MODE", CommandDomain.IRIS, "Put IRIS into sleep mode.", []),
    Command("WAKE_IRIS", CommandDomain.IRIS, "Wake IRIS.", []),
    Command("STOP_IRIS", CommandDomain.IRIS, "Stop IRIS.", []),
    Command("RESTART_IRIS", CommandDomain.IRIS, "Restart IRIS.", []),
    Command("IRIS_STATUS", CommandDomain.IRIS, "Get IRIS status.", []),
]

# endregion


# region AI / CONVERSATION

AI_COMMANDS = [
    Command("AI_FALLBACK", CommandDomain.AI, "Use AI fallback processing.", ["prompt"]),
    Command("ASK_AI", CommandDomain.AI, "Ask the AI a question.", ["prompt"]),
    Command("SUMMARIZE", CommandDomain.AI, "Summarize text.", ["text"]),
    Command("EXPLAIN", CommandDomain.AI, "Explain something.", ["text"]),
    Command("TRANSLATE", CommandDomain.AI, "Translate text.", ["text", "language"]),
    Command("REWRITE", CommandDomain.AI, "Rewrite text.", ["text", "style"]),
    Command("GENERATE_TEXT", CommandDomain.AI, "Generate text.", ["prompt"]),
    Command("ANALYZE_TEXT", CommandDomain.AI, "Analyze text.", ["text"]),
    Command("ANALYZE_FILE", CommandDomain.AI, "Analyze a file.", ["path"]),
]

# endregion


# region MULTI-ACTION / AUTOMATION

AUTOMATION_COMMANDS = [
    Command(
        "EXECUTE_TASK",
        CommandDomain.AUTOMATION,
        "Execute a multi-step task.",
        ["task"],
    ),
    Command(
        "RUN_SEQUENCE",
        CommandDomain.AUTOMATION,
        "Run a sequence of commands.",
        ["commands"],
    ),
    Command(
        "CREATE_AUTOMATION",
        CommandDomain.AUTOMATION,
        "Create an automation.",
        ["name", "commands"],
    ),
    Command(
        "RUN_AUTOMATION",
        CommandDomain.AUTOMATION,
        "Run an automation.",
        ["name"],
    ),
    Command(
        "STOP_AUTOMATION",
        CommandDomain.AUTOMATION,
        "Stop an automation.",
        ["name"],
    ),
    Command(
        "LIST_AUTOMATIONS",
        CommandDomain.AUTOMATION,
        "List available automations.",
        [],
    ),
]

# endregion


# region COMMAND REGISTRY

ALL_COMMANDS = (
    FILES_COMMANDS
    + APPLICATION_COMMANDS
    + BROWSER_COMMANDS
    + WINDOW_COMMANDS
    + SYSTEM_COMMANDS
    + AUDIO_MEDIA_COMMANDS
    + SCREEN_INPUT_COMMANDS
    + PRODUCTIVITY_COMMANDS
    + CLIPBOARD_COMMANDS
    + SEARCH_INFORMATION_COMMANDS
    + NETWORK_COMMANDS
    + HARDWARE_COMMANDS
    + SECURITY_COMMANDS
    + PROCESS_COMMANDS
    + SOFTWARE_COMMANDS
    + IRIS_COMMANDS
    + AI_COMMANDS
    + AUTOMATION_COMMANDS
)


# Every command name must be globally unique.
COMMAND_REGISTRY = {
    command.name: command
    for command in ALL_COMMANDS
}


# endregion


# region HELPER FUNCTIONS

def get_command(name: str) -> Command | None:
    """Return a command by name."""
    return COMMAND_REGISTRY.get(name.upper())


def get_commands_by_domain(domain: CommandDomain) -> list[Command]:
    """Return all commands belonging to a domain."""
    return [
        command
        for command in ALL_COMMANDS
        if command.domain == domain
    ]


def get_dangerous_commands() -> list[Command]:
    """Return all commands marked as dangerous."""
    return [
        command
        for command in ALL_COMMANDS
        if command.dangerous
    ]


def get_confirmation_commands() -> list[Command]:
    """Return all commands requiring confirmation."""
    return [
        command
        for command in ALL_COMMANDS
        if command.requires_confirmation
    ]


def command_exists(name: str) -> bool:
    """Check whether a command exists."""
    return name.upper() in COMMAND_REGISTRY


def command_to_dict(command: Command) -> dict[str, Any]:
    """Convert a command into a dictionary."""
    return {
        "name": command.name,
        "domain": command.domain.value,
        "description": command.description,
        "parameters": command.parameters,
        "requires_confirmation": command.requires_confirmation,
        "dangerous": command.dangerous,
    }


def get_command_schema() -> list[dict[str, Any]]:
    """Return all commands as dictionaries."""
    return [
        command_to_dict(command)
        for command in ALL_COMMANDS
    ]


# endregion
