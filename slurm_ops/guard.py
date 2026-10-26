"""Provide command guidance for login nodes across agent applications.

The command classifier parses known forms without executing them. It provides
advice for unrecognized shell structure.
"""

import posixpath
import re
import shlex


_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*=")
_PYTHON = re.compile(r"^(?:python(?:[23](?:\.\d+)?)?|pypy[23]?)$")
_RUNNERS = {"pytest", "py.test", "torchrun", "deepspeed", "mpiexec", "mpirun"}
_MODULE_RUNNERS = {"pytest", "unittest", "torch.distributed.run", "torch.distributed.launch"}
_HELP = {"-h", "--help", "--version", "-V"}
_UV_VALUES = {
    "--project", "--directory", "--package", "--python", "-p", "--with",
    "--with-editable", "--with-requirements", "--env-file", "--config-file",
    "--cache-dir", "--index", "--default-index", "--index-url",
    "--extra-index-url", "--find-links", "--prerelease", "--resolution",
    "--python-platform", "--link-mode", "--from", "--color", "--keyring-provider",
    "--extra", "--no-extra", "--group", "--no-group", "--only-group",
    "--index-strategy", "--upgrade-package", "-P", "--reinstall-package",
    "--no-build-package", "--no-binary-package", "--allow-insecure-host",
    "--python-preference", "--python-downloads",
}
_UV_FLAGS = {
    "--isolated", "--no-project", "--active", "--locked", "--frozen", "--offline",
    "--no-sync", "--all-packages", "--all-extras", "--no-default-groups",
    "--no-dev", "--dev", "--no-managed-python", "--managed-python", "--no-cache",
    "--refresh", "--no-config", "--no-env-file", "--no-progress", "--quiet", "-q",
    "--verbose", "-v", "--native-tls", "--exact", "--all-groups", "--only-dev",
    "--no-sources", "--no-build", "--no-binary", "--reinstall", "--upgrade", "-U",
}
_SCHED_VALUES = {
    "--account", "-A", "--partition", "-p", "--qos", "-q", "--time", "-t",
    "--nodes", "-N", "--ntasks", "-n", "--cpus-per-task", "-c", "--mem",
    "--mem-per-cpu", "--mem-per-gpu", "--gres", "--gpus", "-G", "--gpus-per-node",
    "--gpus-per-task", "--ntasks-per-node", "--ntasks-per-gpu", "--constraint", "-C",
    "--job-name", "-J", "--chdir", "-D", "--jobid", "--job-id", "--output", "-o",
    "--error", "-e", "--export", "--reservation", "--licenses", "-L", "--hint",
    "--distribution", "-m", "--cpu-bind", "--gpu-bind", "--mpi", "--signal",
    "--begin", "--dependency", "-d", "--exclude", "-x", "--nodelist", "-w",
    "--threads-per-core", "--sockets-per-node", "--cores-per-socket", "--nice",
    "--kill-on-bad-exit", "--wait", "-W", "--switches", "--comment",
}
_SCHED_FLAGS = {
    "--exclusive", "--overlap", "--exact", "--pty", "--unbuffered", "-u",
    "--immediate", "-I", "--no-shell", "--test-only", "--verbose", "-v", "--quiet",
    "-Q", "--label", "-l", "--no-kill", "--contiguous", "--oversubscribe", "-s",
}


def _result(decision, reason):
    return {"decision": decision, "reason": reason}


def _complex_shell(command):
    """Detect active shell syntax with quote and escape handling."""
    quote = None
    escaped = False
    for index, char in enumerate(command):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote != "'":
            escaped = True
            continue
        if quote == "'":
            if char == "'":
                quote = None
            continue
        if char == "'" and quote is None:
            quote = "'"
            continue
        if char == '"':
            quote = None if quote == '"' else '"'
            continue
        if char == "`" or (char == "$" and index + 1 < len(command)
                           and command[index + 1] in "({"):
            return True
        if quote is None and (char in ";&|<>()\n\r" or char == "$" or char in "*?["):
            return True
    return quote is not None or escaped


def _options(argv, value_options, flag_options):
    """Return the command after known prefix options, or None if uncertain."""
    index = 0
    short_values = {option for option in value_options if len(option) == 2}
    while index < len(argv):
        arg = argv[index]
        if arg == "--":
            return argv[index + 1:]
        if not arg.startswith("-") or arg == "-":
            return argv[index:]
        if arg in _HELP:
            return []
        option, equals, _ = arg.partition("=")
        if option in value_options:
            if equals:
                index += 1
            else:
                if index + 1 >= len(argv):
                    return None
                index += 2
        elif option in flag_options:
            index += 1
        elif len(arg) > 2 and arg[:2] in short_values and not arg.startswith("--"):
            index += 1
        else:
            return None
    return []


def _unwrap(argv):
    """Remove supported environment and Python command prefixes without execution."""
    for _ in range(8):
        while argv and _ASSIGNMENT.match(argv[0]):
            argv = argv[1:]
        if not argv:
            return []
        name = posixpath.basename(argv[0])
        if name == "env":
            argv = _options(argv[1:], {"-u", "--unset", "-C", "--chdir"},
                            {"-i", "--ignore-environment", "-0", "--null"})
            if argv is None:
                return None
        elif name == "uv":
            tail = _options(argv[1:], {"--directory", "--project", "--config-file", "--color"},
                            {"--offline", "--no-config", "--quiet", "-q", "--verbose", "-v"})
            if tail is None:
                return None
            if not tail or tail[0] != "run":
                return argv  # Return other uv commands unchanged for classification.
            argv = _options(tail[1:], _UV_VALUES, _UV_FLAGS)
            if argv is None:
                return None
        elif name == "uvx":
            argv = _options(argv[1:], _UV_VALUES, _UV_FLAGS)
            if argv is None:
                return None
            if argv:
                argv = [re.split(r"[@=]", argv[0], maxsplit=1)[0]] + argv[1:]
        else:
            return argv
    return None


def _workload(argv):
    """Recognize standard workload commands; leave project scripts unclassified."""
    name = posixpath.basename(argv[0])
    if any(arg in _HELP for arg in argv[1:]):
        return False
    if name in _RUNNERS:
        return True
    if name == "accelerate" and len(argv) > 1 and argv[1] == "launch":
        return True
    if _PYTHON.match(name):
        index = 1
        while index < len(argv):
            arg = argv[index]
            if arg == "-m":
                if index + 1 == len(argv):
                    return False
                return argv[index + 1] in _MODULE_RUNNERS
            if arg == "-c":
                return False  # Never interpret arbitrary Python source.
            if arg in {"-W", "-X"}:
                index += 2
            elif arg.startswith("-"):
                index += 1
            else:
                return False  # Leave project scripts unclassified.
    return False


def classify_command(command, context):
    """Inspect command text and return allow, deny, or advisory.

    Denials apply only to confirmed execution on login nodes. Validate resources
    before submission. Submit jobs covered by the user request or prior authorization.
    """
    login = isinstance(context, dict) and context.get("role") == "login"
    if not isinstance(command, str) or not command.strip():
        return _result("allow", "No shell command to classify.")
    if len(command) > 65536 or _complex_shell(command):
        return _result("advisory" if login else "allow",
                       "Complex shell syntax requires manual review. "
                       "Keep compute workloads inside an allocation.")
    try:
        argv = _unwrap(shlex.split(command, comments=True, posix=True))
    except ValueError:
        argv = None
    if argv is None:
        return _result("advisory" if login else "allow",
                       "Unrecognized command prefix; verify that compute executes inside an allocation.")
    if not argv:
        return _result("allow", "No workload execution recognized.")
    if not login:
        return _result("allow", "Login-node denials require a confirmed login role.")
    name = posixpath.basename(argv[0])
    if name in {"sbatch", "srun"}:
        return _result("allow", "Scheduler submission or execution through srun recognized.")
    if name == "salloc":
        tail = _options(argv[1:], _SCHED_VALUES, _SCHED_FLAGS)
        if tail is None:
            return _result("advisory", "Unrecognized salloc options. Use srun to start compute "
                           "execution on allocated nodes.")
        if not tail:
            return _result("allow", "Allocation request recognized; its shell remains on the login "
                           "node until a compute step is started.")
        nested = _unwrap(tail)
        if nested is None:
            return _result("advisory", "Unrecognized salloc command; use srun for compute execution.")
        if nested and posixpath.basename(nested[0]) == "srun":
            return _result("allow", "salloc starts an srun compute step.")
        argv = nested or []
    if argv and _workload(argv):
        return _result("deny", "Recognized compute or test workload would execute on a confirmed "
                       "login node. Use an appropriate single-node srun/sbatch allocation. "
                       "For salloc allocations, use srun to execute the workload on allocated nodes.")
    if argv and posixpath.basename(argv[0]) in {"bash", "sh", "zsh", "fish", "timeout", "nice", "nohup", "exec", "command", "time", "stdbuf"}:
        return _result("advisory", "Review this shell or command prefix manually. "
                       "Verify that compute executes inside an allocation.")
    return _result("allow", "No recognized direct compute workload.")
