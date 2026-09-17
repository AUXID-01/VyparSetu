def parse_mock_token(token: str) -> str:
    if token.startswith("mock_tok_"):
        return token.replace("mock_tok_", "")
    return token
