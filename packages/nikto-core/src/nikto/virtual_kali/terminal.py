"""Kali Terminal — Full shell emulator with NICTO integration.

Provides a realistic bash-like shell with:
- Kali green-on-black prompt (┌──(nikto)─(/root)└──$ )
- Command history, tab-completion, pipes
- Built-in commands (cd, ls, cat, pwd, echo, etc.)
- Tool execution via ToolDatabase
- Script execution (.sh files)
- Environment variables
"""

from __future__ import annotations
import os
import time
import random
import shlex
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable
from enum import Enum

from .filesystem import VirtualFileSystem
from .tools import ToolDatabase, KaliTool, ToolCategory


class CommandResult:
    def __init__(self, output: str = "", success: bool = True,
                 exit_code: int = 0, error: str = ""):
        self.output = output
        self.success = success
        self.exit_code = exit_code
        self.error = error


@dataclass
class CommandHistory:
    commands: List[str] = field(default_factory=list)
    max_size: int = 1000
    index: int = -1

    def add(self, cmd: str):
        if cmd and (not self.commands or self.commands[-1] != cmd):
            self.commands.append(cmd)
            if len(self.commands) > self.max_size:
                self.commands.pop(0)
        self.index = len(self.commands)

    def up(self) -> Optional[str]:
        if self.commands and self.index > 0:
            self.index -= 1
            return self.commands[self.index]
        return None

    def down(self) -> Optional[str]:
        if self.commands and self.index < len(self.commands) - 1:
            self.index += 1
            return self.commands[self.index]
        self.index = len(self.commands)
        return ""


class KaliTerminal:
    """Kali Linux terminal emulator with full shell simulation."""

    def __init__(self, fs: VirtualFileSystem, tools: ToolDatabase):
        self.fs = fs
        self.tools = tools
        self.history = CommandHistory()
        self.env: Dict[str, str] = {
            "USER": "root",
            "HOME": "/root",
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/share/nmap:/opt/nikto/scripts",
            "LANG": "en_US.UTF-8",
            "PWD": "/root",
            "HOSTNAME": "nikto-kali",
            "KALI_VERSION": "2024.1",
            "NIKTO_VERSION": "8.2.0",
        }
        self._builtins: Dict[str, Callable] = self._register_builtins()
        self._tool_aliases: Dict[str, str] = self._register_aliases()
        self.output_callback: Optional[Callable] = None
        self._running = True

    def _register_builtins(self) -> Dict[str, Callable]:
        return {
            "cd": self._cmd_cd,
            "ls": self._cmd_ls,
            "cat": self._cmd_cat,
            "pwd": self._cmd_pwd,
            "echo": self._cmd_echo,
            "clear": self._cmd_clear,
            "touch": self._cmd_touch,
            "mkdir": self._cmd_mkdir,
            "rm": self._cmd_rm,
            "cp": self._cmd_cp,
            "mv": self._cmd_mv,
            "chmod": self._cmd_chmod,
            "find": self._cmd_find,
            "grep": self._cmd_grep,
            "head": self._cmd_head,
            "tail": self._cmd_tail,
            "whoami": self._cmd_whoami,
            "hostname": self._cmd_hostname,
            "env": self._cmd_env,
            "export": self._cmd_export,
            "history": self._cmd_history,
            "exit": self._cmd_exit,
            "help": self._cmd_help,
            "man": self._cmd_man,
            "which": self._cmd_which,
            "wget": self._cmd_wget,
            "curl": self._cmd_curl,
            "uname": self._cmd_uname,
            "id": self._cmd_id,
            "date": self._cmd_date,
            "df": self._cmd_df,
            "du": self._cmd_du,
            "ps": self._cmd_ps,
            "kill": self._cmd_kill,
            "sort": self._cmd_sort,
            "wc": self._cmd_wc,
            "sleep": self._cmd_sleep,
            "true": lambda a: CommandResult(),
            "false": lambda a: CommandResult(success=False, exit_code=1),
            "nikto-help": self._cmd_nikto_help,
            "nikto-status": self._cmd_nikto_status,
            "nikto-exploit": self._cmd_nikto_exploit,
            "nikto-scan": self._cmd_nikto_scan,
        }

    def _register_aliases(self) -> Dict[str, str]:
        return {
            "ll": "ls -la",
            "la": "ls -A",
            "vim": "vi",
            "vi": "nano",
            "py": "python3",
            "cls": "clear",
            "grep": "grep --color=auto",
            "..": "cd ..",
        }

    def execute(self, command: str) -> CommandResult:
        if not command or not command.strip():
            return CommandResult()
        command = command.strip()
        self.history.add(command)
        alias = self._tool_aliases.get(command.split()[0])
        if alias:
            command = alias + command[len(command.split()[0]):]
        try:
            parts = shlex.split(command)
        except ValueError:
            return CommandResult(error=f"Syntax error: {command}", success=False, exit_code=2)
        if not parts:
            return CommandResult()
        cmd_name = parts[0]
        args = parts[1:]
        if cmd_name in self._builtins:
            result = self._builtins[cmd_name](args)
        elif cmd_name in self.tools.tools:
            result = self._execute_tool(cmd_name, args)
        else:
            result = self._handle_unknown(cmd_name, args)
        if result.output and self.output_callback:
            self.output_callback(result.output)
        return result

    def execute_script(self, script_path: str) -> CommandResult:
        content = self.fs.read(script_path)
        if content is None:
            return CommandResult(error=f"script: {script_path}: No such file", success=False, exit_code=1)
        lines = content.split("\n")
        combined = CommandResult()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                result = self.execute(line)
                if result.output:
                    combined.output += result.output + "\n"
                if not result.success and result.exit_code != 0:
                    return result
        return combined

    def _execute_tool(self, name: str, args: List[str]) -> CommandResult:
        tool = self.tools.get(name)
        if not tool:
            return CommandResult(error=f"Command not found: {name}", success=False, exit_code=127)
        arg_str = " ".join(args)
        if tool.nicto_integrated:
            return CommandResult(
                output=f"[NICTO-INTEGRATED] {name} {arg_str}\n"
                       f"Running {name} via NICTO engine...\n"
                       f"Target: {arg_str if arg_str else 'default'}\n"
                       f"Tool version: {tool.version}\n"
                       f"Category: {tool.category.value}\n"
                       f"[+] {name} execution complete.\n"
            )
        return CommandResult(
            output=f"[{tool.category.value}] {name} v{tool.version}\n"
                   f"{tool.description}\n"
                   f"Arguments: {arg_str if arg_str else '(none)'}\n"
                   f"[+] Tool completed successfully.\n"
        )

    def _handle_unknown(self, cmd: str, args: List[str]) -> CommandResult:
        return CommandResult(
            error=f"bash: {cmd}: command not found",
            success=False, exit_code=127
        )

    def get_prompt(self) -> str:
        pwd = self.fs.pwd()
        user = self.env.get("USER", "root")
        host = self.env.get("HOSTNAME", "nikto-kali")
        short_pwd = pwd.replace("/root", "~") if pwd.startswith("/root") else pwd
        return f"\033[01;31m┌──(\033[01;32m{user}㉿{host}\033[01;31m)─[\033[01;34m{short_pwd}\033[01;31m]\n\033[01;31m└──\033[00m\033[01;32m$\033[00m "

    # ----- Built-in commands -----
    def _cmd_cd(self, args: List[str]) -> CommandResult:
        path = args[0] if args else "/root"
        ok, msg = self.fs.cd(path)
        self.env["PWD"] = self.fs.pwd()
        if ok:
            return CommandResult()
        return CommandResult(error=msg, success=False, exit_code=1)

    def _cmd_ls(self, args: List[str]) -> CommandResult:
        show_all = False
        long = False
        target = None
        i = 0
        while i < len(args):
            if args[i] == "-la" or args[i] == "-al":
                show_all = True; long = True
            elif args[i] == "-l":
                long = True
            elif args[i] == "-a":
                show_all = True
            elif args[i].startswith("-"):
                for c in args[i][1:]:
                    if c == 'a': show_all = True
                    elif c == 'l': long = True
            else:
                target = args[i]
            i += 1
        lines = self.fs.ls(target, show_all=show_all, long=long)
        return CommandResult(output="\n".join(lines))

    def _cmd_cat(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(error="cat: missing operand", success=False, exit_code=1)
        output = ""
        for path in args:
            abs_path = self.fs.get_absolute_path(path)
            ok, content = self.fs.cat(abs_path)
            if ok:
                output += content
            else:
                output += f"cat: {path}: No such file\n"
        return CommandResult(output=output.rstrip("\n"))

    def _cmd_pwd(self, args: List[str]) -> CommandResult:
        return CommandResult(output=self.fs.pwd())

    def _cmd_echo(self, args: List[str]) -> CommandResult:
        text = " ".join(args)
        text = os.path.expandvars(text)
        return CommandResult(output=text)

    def _cmd_clear(self, args: List[str]) -> CommandResult:
        return CommandResult(output="\033[2J\033[H")

    def _cmd_touch(self, args: List[str]) -> CommandResult:
        for path in args:
            abs_path = self.fs.get_absolute_path(path)
            self.fs.touch(abs_path)
        return CommandResult()

    def _cmd_mkdir(self, args: List[str]) -> CommandResult:
        for path in args:
            abs_path = self.fs.get_absolute_path(path)
            ok, msg = self.fs.mkdir(abs_path)
            if not ok:
                return CommandResult(error=msg, success=False, exit_code=1)
        return CommandResult()

    def _cmd_rm(self, args: List[str]) -> CommandResult:
        recursive = False
        targets = []
        for a in args:
            if a == "-r" or a == "-rf" or a == "-fr":
                recursive = True
            elif a.startswith("-") and "r" in a:
                recursive = True
            else:
                targets.append(a)
        for path in targets:
            abs_path = self.fs.get_absolute_path(path)
            ok, msg = self.fs.rm(abs_path, recursive=recursive)
            if not ok:
                return CommandResult(error=msg, success=False, exit_code=1)
        return CommandResult()

    def _cmd_cp(self, args: List[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(error="cp: missing operand", success=False, exit_code=1)
        src = self.fs.get_absolute_path(args[-2])
        dst = self.fs.get_absolute_path(args[-1])
        ok, msg = self.fs.cp(src, dst)
        if not ok:
            return CommandResult(error=msg, success=False, exit_code=1)
        return CommandResult()

    def _cmd_mv(self, args: List[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(error="mv: missing operand", success=False, exit_code=1)
        src = self.fs.get_absolute_path(args[-2])
        dst = self.fs.get_absolute_path(args[-1])
        ok, msg = self.fs.mv(src, dst)
        if not ok:
            return CommandResult(error=msg, success=False, exit_code=1)
        return CommandResult()

    def _cmd_chmod(self, args: List[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(error="chmod: missing operand", success=False, exit_code=1)
        mode = args[0]
        path = self.fs.get_absolute_path(args[1])
        ok, msg = self.fs.chmod(path, mode)
        if not ok:
            return CommandResult(error=msg, success=False, exit_code=1)
        return CommandResult()

    def _cmd_find(self, args: List[str]) -> CommandResult:
        pattern = args[-1] if args else ""
        start = self.fs.get_absolute_path(args[0]) if len(args) > 1 and not args[0].startswith("-") else "/"
        results = self.fs.find(pattern, start)
        return CommandResult(output="\n".join(results) if results else f"find: nothing matched '{pattern}'")

    def _cmd_grep(self, args: List[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(error="grep: missing pattern", success=False, exit_code=2)
        pattern = args[0]
        path = self.fs.get_absolute_path(args[1])
        matches = self.fs.grep(pattern, path)
        return CommandResult(output="\n".join(matches) if matches else "")

    def _cmd_head(self, args: List[str]) -> CommandResult:
        n = 10
        target = ""
        for i, a in enumerate(args):
            if a.startswith("-n") and i + 1 < len(args):
                n = int(args[i + 1])
            elif not a.startswith("-"):
                target = a
        if not target:
            return CommandResult(error="head: missing operand", success=False, exit_code=1)
        path = self.fs.get_absolute_path(target)
        ok, content = self.fs.cat(path)
        if ok:
            lines = content.split("\n")[:n]
            return CommandResult(output="\n".join(lines))
        return CommandResult(error=f"head: {target}: No such file", success=False, exit_code=1)

    def _cmd_tail(self, args: List[str]) -> CommandResult:
        n = 10
        target = ""
        for i, a in enumerate(args):
            if a.startswith("-n") and i + 1 < len(args):
                n = int(args[i + 1])
            elif not a.startswith("-"):
                target = a
        if not target:
            return CommandResult(error="tail: missing operand", success=False, exit_code=1)
        path = self.fs.get_absolute_path(target)
        ok, content = self.fs.cat(path)
        if ok:
            lines = content.split("\n")
            return CommandResult(output="\n".join(lines[-n:]))
        return CommandResult(error=f"tail: {target}: No such file", success=False, exit_code=1)

    def _cmd_whoami(self, args: List[str]) -> CommandResult:
        return CommandResult(output=self.env.get("USER", "root"))

    def _cmd_hostname(self, args: List[str]) -> CommandResult:
        if args:
            self.env["HOSTNAME"] = args[0]
        return CommandResult(output=self.env.get("HOSTNAME", "nikto-kali"))

    def _cmd_env(self, args: List[str]) -> CommandResult:
        return CommandResult(output="\n".join(f"{k}={v}" for k, v in sorted(self.env.items())))

    def _cmd_export(self, args: List[str]) -> CommandResult:
        for arg in args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                self.env[k] = v
        return CommandResult()

    def _cmd_history(self, args: List[str]) -> CommandResult:
        lines = []
        for i, cmd in enumerate(self.history.commands, 1):
            lines.append(f"  {i:4d}  {cmd}")
        return CommandResult(output="\n".join(lines))

    def _cmd_exit(self, args: List[str]) -> CommandResult:
        self._running = False
        return CommandResult(output="logout")

    def _cmd_help(self, args: List[str]) -> CommandResult:
        help_text = """GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu)
These shell commands are defined internally.

NICTO-specific commands:
  nikto-help    - Show NICTO Virtual Kali help
  nikto-status  - Show NICTO engine status
  nikto-exploit - Search/launch exploits via NICTO
  nikto-scan    - Run NICTO scanner

File commands: cd, ls, cat, pwd, touch, mkdir, rm, cp, mv, chmod, find, grep
Text commands: echo, head, tail, sort, wc
System: whoami, hostname, env, export, history, clear, ps, kill, uname, id, date, df, du
Network: wget, curl, nmap, ping, netcat

Type 'nikto-help' for detailed NICTO commands.
"""
        return CommandResult(output=help_text)

    def _cmd_man(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(error="What manual page do you want?", success=False, exit_code=1)
        cmd = args[0]
        if cmd in self.tools.tools:
            t = self.tools.get(cmd)
            return CommandResult(
                output=f"{t.name}(1)\n\nNAME\n    {t.name} - {t.description}\n\n"
                       f"CATEGORY\n    {t.category.value}\n\nVERSION\n    {t.version}\n"
                       f"\nNICTO INTEGRATION\n    {'Yes' if t.nicto_integrated else 'No'}\n"
            )
        if cmd in self._builtins:
            return CommandResult(output=f"{cmd} - shell built-in command\n")
        return CommandResult(error=f"No manual entry for {cmd}", success=False, exit_code=16)

    def _cmd_which(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(error="which: missing operand", success=False, exit_code=1)
        cmd = args[0]
        if cmd in self._builtins:
            return CommandResult(output=f"{cmd}: shell built-in command")
        if cmd in self.tools.tools:
            paths = self.env.get("PATH", "/usr/bin").split(":")
            for p in paths:
                if os.path.exists(os.path.join(p, cmd)):
                    return CommandResult(output=f"{p}/{cmd}")
            return CommandResult(output=f"/usr/bin/{cmd}")
        return CommandResult(error=f"{cmd} not found", success=False, exit_code=1)

    def _cmd_wget(self, args: List[str]) -> CommandResult:
        url = args[-1] if args else ""
        if not url:
            return CommandResult(error="wget: missing URL", success=False, exit_code=1)
        filename = url.split("/")[-1] or "index.html"
        return CommandResult(
            output=f"--2024-01-01 12:00:00--  {url}\n"
                   f"Resolving {url.split('/')[2]}... 192.168.1.1\n"
                   f"Connecting to {url.split('/')[2]}:443... connected.\n"
                   f"HTTP request sent, awaiting response... 200 OK\n"
                   f"Length: 12345 [text/html]\n"
                   f"Saving to: '{filename}'\n\n"
                   f"12345  --.-K/s  in 0.1s\n\n"
                   f"'{filename}' saved\n"
        )

    def _cmd_curl(self, args: List[str]) -> CommandResult:
        url = args[-1] if args else ""
        if not url:
            return CommandResult(error="curl: try 'curl --help'", success=False, exit_code=1)
        return CommandResult(
            output=f"<!DOCTYPE html>\n<html>\n<head><title>Response</title></head>\n"
                   f"<body><h1>NICTO Virtual Kali</h1><p>Simulated response from {url}</p></body>\n</html>\n"
        )

    def _cmd_uname(self, args: List[str]) -> CommandResult:
        if "-a" in args:
            return CommandResult(output="Linux nikto-kali 6.6.9-amd64 #1 SMP PREEMPT_DYNAMIC Kali 6.6.9-1kali1 (2024-01-15) x86_64 GNU/Linux")
        if "-r" in args:
            return CommandResult(output="6.6.9-amd64")
        return CommandResult(output="Linux")

    def _cmd_id(self, args: List[str]) -> CommandResult:
        return CommandResult(output="uid=0(root) gid=0(root) groups=0(root)")

    def _cmd_date(self, args: List[str]) -> CommandResult:
        return CommandResult(output=time.strftime("%a %b %d %H:%M:%S %Z %Y"))

    def _cmd_df(self, args: List[str]) -> CommandResult:
        return CommandResult(
            output="Filesystem     1K-blocks    Used Available Use% Mounted on\n"
                   "/dev/sda1       48826368 8345678  40480690  18% /\n"
                   "tmpfs            2012340     456   2011884   1% /tmp\n"
        )

    def _cmd_du(self, args: List[str]) -> CommandResult:
        path = self.fs.get_absolute_path(args[0]) if args else self.fs.pwd()
        size = self.fs.get_size(path)
        return CommandResult(output=f"{size // 1024}\t{path}")

    def _cmd_ps(self, args: List[str]) -> CommandResult:
        processes = [
            "  PID TTY          TIME CMD",
            "    1 ?        00:00:02 init",
            "   42 ?        00:00:01 systemd-journal",
            "  128 ?        00:00:00 sshd",
            "  256 tty1     00:00:00 bash",
            "  312 tty1     00:00:00 nikto-kali",
            "  789 ?        00:00:01 apache2",
            "  812 ?        00:00:00 nmap",
        ]
        return CommandResult(output="\n".join(processes))

    def _cmd_kill(self, args: List[str]) -> CommandResult:
        return CommandResult(output="")

    def _cmd_sort(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(error="sort: missing operand", success=False, exit_code=1)
        path = self.fs.get_absolute_path(args[-1])
        ok, content = self.fs.cat(path)
        if ok:
            lines = sorted(content.split("\n"))
            return CommandResult(output="\n".join(lines))
        return CommandResult(error="", success=True)

    def _cmd_wc(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(error="wc: missing operand", success=False, exit_code=1)
        path = self.fs.get_absolute_path(args[-1])
        ok, content = self.fs.cat(path)
        if ok:
            lines = content.count("\n")
            words = len(content.split())
            chars = len(content)
            return CommandResult(output=f"  {lines}  {words}  {chars} {args[-1]}")
        return CommandResult(output="")

    def _cmd_sleep(self, args: List[str]) -> CommandResult:
        return CommandResult()

    # ----- NICTO-specific commands -----
    def _cmd_nikto_help(self, args: List[str]) -> CommandResult:
        help_text = """╔══════════════════════════════════════════════════════════╗
║        NICTO VIRTUAL KALI — Exclusive Operations         ║
╠══════════════════════════════════════════════════════════╣
║ Commands:                                                ║
║  nikto-help      - This help screen                      ║
║  nikto-status    - NICTO engine & tool status            ║
║  nikto-exploit   - Search exploits (nikto-exploit <q>)   ║
║  nikto-scan      - Run target scan (nikto-scan <target>) ║
║                                                          ║
║ Tools: 500+ Kali tools pre-installed                     ║
║ Integration: NICTO exploit_db, scanner, threat_intel     ║
║ Environment: Virtual Kali Linux Rolling                  ║
╚══════════════════════════════════════════════════════════╝"""
        return CommandResult(output=help_text)

    def _cmd_nikto_status(self, args: List[str]) -> CommandResult:
        stats = self.tools.get_stats()
        output = (f"NICTO Virtual Kali Status\n"
                  f"{'='*35}\n"
                  f"Total tools: {stats['total_tools']}\n"
                  f"NICTO-integrated: {stats['integrated']}\n"
                  f"Categories: {stats['categories']}\n"
                  f"PWD: {self.fs.pwd()}\n"
                  f"User: {self.env.get('USER')}@{self.env.get('HOSTNAME')}\n")
        return CommandResult(output=output)

    def _cmd_nikto_exploit(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(error="Usage: nikto-exploit <search_term>", success=False, exit_code=1)
        query = " ".join(args)
        results = self.tools.search(query)
        if not results:
            return CommandResult(output=f"No exploits found for '{query}'")
        output = f"NICTO Exploit Search: '{query}'\n{'='*40}\n"
        for t in results[:20]:
            tag = " [NICTO]" if t.nicto_integrated else ""
            output += f"  {t.name:<20} {t.category.value:<25} {t.description[:50]}{tag}\n"
        return CommandResult(output=output)

    def _cmd_nikto_scan(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(error="Usage: nikto-scan <target>", success=False, exit_code=1)
        target = args[0]
        output = (f"NICTO Scan: {target}\n"
                  f"{'='*40}\n"
                  f"[*] Target resolved: {target}\n"
                  f"[*] Port scanning initiated...\n"
                  f"  [+] 22/tcp   open  ssh     OpenSSH 8.9p1\n"
                  f"  [+] 80/tcp   open  http    Apache 2.4.57\n"
                  f"  [+] 443/tcp  open  https   Apache 2.4.57\n"
                  f"  [+] 3306/tcp open  mysql   MySQL 8.0.35\n"
                  f"[*] 4 ports identified\n"
                  f"[*] Service detection complete\n"
                  f"[*] Vulnerability scan queued\n"
                  f"[+] Scan complete — results saved to /root/reports/{target}.txt\n")
        return CommandResult(output=output)
