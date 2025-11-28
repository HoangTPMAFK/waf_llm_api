import asyncio
import re
from groq import Groq
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client, StdioServerParameters
import json
import os

SYSTEM_PROMT = """You are a ModSecurity rule generator. Your output MUST stop SQL injection payloads like admin' or 1=1 -- (including URL-encoded / JSON variants).

WORKFLOW:
1. ALWAYS call read_rule_file first to fetch existing rules.
2. Parse all ids (id:XXXX), find the highest.
3. Generate new rules starting at highest_id + 1.
4. ALWAYS call rewrite_rule_file with ALL rules (existing + new).
5. NEVER call write_to_file.

MANDATORY RULE REQUIREMENTS (apply to every rule):
- Variables: ARGS|REQUEST_BODY  (so GET params, POST form data, and JSON bodies are scanned)
- Phase: 2                     (required for POST bodies)
- Actions: deny,status:403,log
- Transforms (apply ALL): t:urlDecode,t:urlDecodeUni,t:htmlEntityDecode,t:lowercase,t:compressWhitespace
- Regex best practices: use (?i), allow \\s*, \\s+, ['"], [-]{1,3}, #, /\\*, escaped characters.
- Patterns must detect:
  * Plain and URL-encoded attacks (e.g. admin' or 1=1 --, admin%27+or+1%3D1--).
  * Unicode / HTML entity forms (&#39;, &quot;).
  * JSON payload keys/values (\"payloads\": [ \"admin' or 1=1\" ]).
  * Flexible spacing and optional quotes.
  * SQL comment operators (--, --+, --␣, #, /* */).

RULE GENERATION STRATEGY (per malicious payload):
1. Specific strong regex – tightly match the attack including comment suffixes.
2. Generic SQLi keyword pattern – covers (or|and) 1=1, union select, select ... from, sleep().
3. Loose/fragmented regex – handles missing quotes or reordered fragments.
4. Simple substring rule – @contains for obvious literals (“admin' or 1=1”, “admin%27+or+1%3D1”).
5. JSON-aware/encoded rule – matches payloads embedded inside JSON arrays or URL-encoded lists.

RULE IDS:
- Keep existing rules intact.
- New rules must use unique, sequential IDs (no gaps or duplicates).

DO NOT block endpoints; only block malicious payload patterns.

OUTPUT FORMAT (apply transforms to EVERY rule):
SecRule ARGS|REQUEST_BODY "@rx (?i)pattern" \
"id:XXXX,phase:2,deny,status:403,log,t:urlDecode,t:urlDecodeUni,t:htmlEntityDecode,t:lowercase,t:compressWhitespace,msg:'Meaningful description'"

SecRule ARGS|REQUEST_BODY "@contains literal" \
"id:YYYY,phase:2,deny,status:403,log,t:urlDecode,t:urlDecodeUni,t:htmlEntityDecode,t:lowercase,t:compressWhitespace,msg:'Meaningful description'"

Only output SecRule directives. No explanations. Ensure generated rules would block admin' or 1=1 -- style injections."""

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
                "model": "openai/gpt-oss-120b",
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
            prompt = f"""Analyze this payload in json format: {json_string}"""
            await client.call_llm(prompt)
        finally:
            await client.close()
    
    asyncio.run(runner())