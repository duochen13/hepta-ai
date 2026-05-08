"""
LLM Client - Claude API integration for code generation

Generates datavint SDK code from natural language prompts using Anthropic Claude.
"""

from anthropic import Anthropic
import os
from typing import Dict, Any

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# System prompt with security constraints and examples
SYSTEM_PROMPT = """You are a data analysis code generator specialized in the DataVint SDK.

STRICT RULES:
1. Generate ONLY Python code using these imports: datavint, pandas, numpy
2. NO file operations (no open, read, write)
3. NO network calls (no requests, urllib)
4. NO system commands (no os, subprocess, sys)
5. Code must work with a DataFrame variable named 'df'
6. Always return results in a dict assigned to 'result' variable
7. Use vint.profile() for data quality analysis

ALLOWED PATTERNS:
- import datavint as vint
- import pandas as pd
- import numpy as np
- stats, issues = vint.profile(df)
- df.describe(), df.info(), df.isnull().sum()
- Basic pandas operations on 'df'

FORBIDDEN PATTERNS:
- import os, sys, subprocess, requests
- open(), read(), write(), eval(), exec()
- Any file system or network operations

EXAMPLE 1 - Basic profiling:
User: "analyze this dataset for data quality issues"
Response:
```python
import datavint as vint
stats, issues = vint.profile(df)
result = {'stats': stats, 'issues': issues}
```

EXAMPLE 2 - Missing values focus:
User: "check for missing values and show which columns have them"
Response:
```python
import datavint as vint
import pandas as pd

# Profile for data quality
stats, issues = vint.profile(df)

# Get missing value details
missing_counts = df.isnull().sum()
missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
columns_with_missing = missing_counts[missing_counts > 0]

result = {
    'stats': stats,
    'issues': issues,
    'missing_counts': missing_counts.to_dict(),
    'missing_percentages': missing_pct.to_dict(),
    'columns_with_missing': columns_with_missing.to_dict()
}
```

EXAMPLE 3 - Duplicates check:
User: "find duplicate rows"
Response:
```python
import datavint as vint
import pandas as pd

# Profile for comprehensive checks
stats, issues = vint.profile(df)

# Check for duplicates
duplicate_count = df.duplicated().sum()
duplicate_rows = df[df.duplicated(keep=False)]

result = {
    'stats': stats,
    'issues': issues,
    'duplicate_count': duplicate_count,
    'total_rows': len(df),
    'duplicate_percentage': round(duplicate_count / len(df) * 100, 2)
}
```

IMPORTANT: Return ONLY the Python code in a ```python code block. No explanations before or after.
"""


async def generate_datavint_code(prompt: str, dataframe_info: Dict[str, Any]) -> str:
    """
    Generate executable datavint code from natural language prompt.

    Calls Claude API with security-constrained system prompt to generate
    safe Python code using only the datavint SDK and pandas operations.

    Args:
        prompt: User's natural language request (e.g., "check for missing values")
        dataframe_info: DataFrame metadata dict with keys:
            - shape: tuple of (rows, columns)
            - columns: list of column names
            - dtypes: dict of column -> dtype mappings

    Returns:
        str: Generated Python code as string

    Raises:
        Exception: If Claude API call fails or times out

    Example:
        >>> info = {'shape': (100, 5), 'columns': ['a', 'b', 'c', 'd', 'e'], 'dtypes': {...}}
        >>> code = await generate_datavint_code("check for missing values", info)
        >>> print(code)
        import datavint as vint
        stats, issues = vint.profile(df)
        result = {'stats': stats, 'issues': issues}
    """
    # Build user message with context
    user_message = f"""Generate Python code for this analysis request: "{prompt}"

DataFrame information:
- Shape: {dataframe_info['shape'][0]} rows × {dataframe_info['shape'][1]} columns
- Columns: {', '.join(dataframe_info['columns'][:10])}{'...' if len(dataframe_info['columns']) > 10 else ''}

Requirements:
1. Use the DataFrame variable 'df' (already loaded)
2. Import datavint as vint for profiling
3. Store results in a 'result' dict
4. Include vint.profile(df) for comprehensive data quality checks

Return ONLY the Python code in a ```python code block."""

    # Call Claude API
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",  # Claude 3 Opus model
            max_tokens=1024,
            temperature=0,  # Deterministic for security
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            timeout=30.0  # 30 second timeout
        )

        # Extract code from response
        code = message.content[0].text

        # Handle markdown code blocks
        if "```python" in code:
            # Extract code between ```python and ```
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            # Extract code between ``` and ```
            code = code.split("```")[1].split("```")[0].strip()

        return code

    except Exception as e:
        # Log error and re-raise
        print(f"Claude API error: {str(e)}")
        raise Exception(f"Failed to generate code: {str(e)}")
