import asyncio
import re
from groq import Groq
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client, StdioServerParameters
import json
import os

SYSTEM_PROMT = """You are a ModSecurity firewall rule generator.

IMPORTANT INSTRUCTIONS:
1. ALWAYS call read_rule_file FIRST to read existing rules
2. Parse all existing rule IDs (format: id:XXXX)
3. Find the highest ID number in existing rules
4. Generate NEW rules starting from (highest_id + 1)
5. Use rewrite_rule_file to write ALL rules (existing + new) together
6. NEVER use write_to_file (append mode) - always rewrite the entire file
7. Maintain sequential, unique IDs for all rules

Rule Format:
- Phase: 2
- Action: deny,status:403,log
- Each rule must have unique ID
- Keep existing rules intact, only add new ones at the end

Example:
Existing rules: id:1002, id:1003, id:1004
New attack detected → Generate: id:1005, id:1006
Output ALL rules: 1002, 1003, 1004, 1005, 1006 (via rewrite_rule_file)"""

class MCPClient:
    def __init__(self):
        self.session: ClientSession = None
        self.exit_stack = AsyncExitStack()
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY", "default-secret-key"))

    async def connect_to_server(self, script_path: str):
        server = StdioServerParameters(
            command="python3",
            args=[script_path],
            env=None
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        tools = await self.session.list_tools()
        print("Connected to MCP server. Tools:", [t.name for t in tools.tools])
    
    async def call_llm(self, prompt: str) -> str:
        new_rules_written = False
        res = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema 
            }
        } for tool in res.tools]

        messages = [
            {"role": "system", "content": SYSTEM_PROMT},
            {"role": "user", "content": prompt}
        ]

        while not new_rules_written:

            completion_args = {
                "model": "qwen/qwen3-32b",
                "messages": messages,
                "temperature": 0.8,
                "top_p": 0.8,
                "max_tokens": 4096,
            }
            
            if available_tools:
                completion_args["tools"] = available_tools

            res = self.groq.chat.completions.create(**completion_args)
            tools_call = res.choices[0].message.tool_calls
            if tools_call:
                for tool in tools_call:
                    print(f"Calling tool: {tool.function.name}")
                    parsed_arguments = json.loads(tool.function.arguments)
                    
                    if tool.function.name == "read_rule_file":
                        result = await self.session.call_tool("read_rule_file")
                        existing_rules = result.content[0].text
                        messages.append({
                            "role": "assistant",
                            "content": f"I read the existing rules:\n{existing_rules if existing_rules else '(empty file)'}"
                        })
                        messages.append({
                            "role": "user",
                            "content": "Now generate new rules with unique IDs and use rewrite_rule_file to write ALL rules (existing + new)"
                        })
                        
                    elif tool.function.name == "rewrite_rule_file":
                        result = await self.session.call_tool(
                            "rewrite_rule_file",
                            {"content": parsed_arguments["content"]}
                        )
                        print(f"✅ Rules rewritten successfully")
                        new_rules_written = True
                        break
                        
                    elif tool.function.name == "write_to_file":
                        print("⚠️  write_to_file called, redirecting to rewrite_rule_file instead")
                        result = await self.session.call_tool(
                            "rewrite_rule_file",
                            {"content": parsed_arguments["content"]}
                        )
                        new_rules_written = True
                        break
                    else:
                        pass
                print("Tool call result:", result)
    
    async def close(self):
        await self.exit_stack.aclose()

def run_mcp_client(payloads: list, script_path: str = "app/services/mcp_server.py"):
    async def runner():
        client = MCPClient()
        try:
            await client.connect_to_server(script_path)
            json_string = json.dumps({"payloads": payloads})
            prompt = f"""Analyze this payload: {json_string}

If this payload is MALICIOUS:
1. Call read_rule_file to get existing rules
2. Parse existing IDs and find the highest ID
3. Generate NEW ModSecurity rules for this attack (starting from highest_id + 1)
4. Call rewrite_rule_file with ALL rules (existing rules + new rules)
5. Ensure all IDs are unique and sequential

If payload is safe, do nothing.

Only output ModSecurity SecRule directives, no explanations."""
            await client.call_llm(prompt)
        finally:
            await client.close()
    
    asyncio.run(runner())