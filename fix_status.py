import re

# Read the file
with open('backend/app/agents/financial_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace status= with success= in AgentResult calls only
# Match AgentResult( followed by status=
content = re.sub(
    r'(AgentResult\([^)]*?)status="SUCCESS"',
    r'\1success=True',
    content
)
content = re.sub(
    r'(AgentResult\([^)]*?)status="FAILED"',
    r'\1success=False',
    content
)
content = re.sub(
    r'(AgentResult\([^)]*?)status="BLOCKED"',
    r'\1success=False',
    content
)
content = re.sub(
    r'(AgentResult\([^)]*?)status="PENDING"',
    r'\1success=False',
    content
)
content = re.sub(
    r'(AgentResult\([^)]*?)status="NEEDS_CONFIRMATION"',
    r'\1success=False',
    content
)

# Write it back
with open('backend/app/agents/financial_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all AgentResult status parameters!")
