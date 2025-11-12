from typing import Any
from mcp.server.fastmcp import FastMCP
import threading

mcp = FastMCP("rule_writer")

@mcp.tool(name="write_to_file", description="Write provided ModSecurity rules into rules.txt (append). Argument: content: str")
def write_to_file(content: str) -> str:
    with open("rules.txt", "a") as file:
        file.write(content)
    return "Content written to rules.txt"

@mcp.tool(name="rewrite_rule_file", description="Rewrite the rules.txt with provided content. Argument: content: str")
def rewrite_rule_file(content: str) -> str:
    with open("rules.txt", "w") as file:
        file.write(content)
    return "Rewritten rules.txt"

@mcp.tool(name="read_rule_file", description="Read the current rules.txt. Returns empty string if file not found or file empty.")
def read_rule_file() -> str:
    try:
        with open("rules.txt", "r") as file:
            return file.read()
    except FileNotFoundError:
        return ""

def _run():
    mcp.run(transport="stdio")

def start_mcp_server():
    t = threading.Thread(target=_run, daemon=True)
    t.start()