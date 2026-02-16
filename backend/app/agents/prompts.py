CLASSIFY_PROMPT = """Classify the user message as one of: financial, auth, risk, audit, unknown.
Only output the category name in lowercase.

Message: {message}
Category:"""