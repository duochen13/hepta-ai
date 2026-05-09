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

EXAMPLE 4 - Class imbalance check:
User: "what's the imbalance rate of dataset?"
Response:
```python
import datavint as vint
import pandas as pd

# Auto-detect label column (common names: label, target, y, class, etc.)
label_col = None
common_label_names = ['label', 'target', 'y', 'class', 'is_fraud', 'churn', 'clicked', 'converted']
for col in df.columns:
    if col.lower() in common_label_names or col.lower().startswith(('is_', 'has_')):
        label_col = col
        break

# Profile dataset with label column (runs all 11 detectors)
stats, issues = vint.profile(df, label_col=label_col)

# Extract imbalance issues
imbalance_issues = [issue for issue in issues if issue['type'] == 'class_imbalance']

# Calculate class distribution if label exists
if label_col:
    class_dist = df[label_col].value_counts(normalize=True).to_dict()
else:
    class_dist = None

result = {
    'stats': stats,
    'issues': issues,
    'imbalance_issues': imbalance_issues,
    'class_distribution': class_dist,
    'label_column': label_col
}
```

EXAMPLE 5 - Completeness check (NEW detector):
User: "check completeness of features"
Response:
```python
import datavint as vint
import pandas as pd

# Profile dataset (includes completeness detector)
stats, issues = vint.profile(df)

# Extract completeness issues
completeness_issues = [issue for issue in issues if issue['type'] == 'low_completeness']

# Get completeness metrics per feature
completeness_metrics = {}
for feat_name, feat_stats in stats.features.items():
    if hasattr(feat_stats, 'completeness') and feat_stats.completeness is not None:
        completeness_metrics[feat_name] = {
            'completeness': round(feat_stats.completeness * 100, 2),
            'missing_rate': round((1 - feat_stats.completeness) * 100, 2)
        }

result = {
    'stats': stats,
    'issues': issues,
    'completeness_issues': completeness_issues,
    'completeness_metrics': completeness_metrics
}
```

EXAMPLE 6 - Entropy and cardinality check (NEW detectors):
User: "check for high cardinality or low information features"
Response:
```python
import datavint as vint
import pandas as pd

# Profile dataset (includes entropy and cardinality detectors)
stats, issues = vint.profile(df)

# Extract relevant issues
entropy_issues = [issue for issue in issues if 'entropy' in issue['type']]
cardinality_issues = [issue for issue in issues if issue['type'] == 'high_cardinality']

# Get enriched metrics per feature
enriched_metrics = {}
for feat_name, feat_stats in stats.features.items():
    enriched_metrics[feat_name] = {
        'type': feat_stats.type,
        'distinct_count': feat_stats.distinct_count,
        'distinctness': round(feat_stats.distinctness * 100, 2) if feat_stats.distinctness else None,
        'uniqueness': round(feat_stats.uniqueness * 100, 2) if feat_stats.uniqueness else None,
        'entropy': round(feat_stats.entropy, 3) if feat_stats.entropy else None,
        'completeness': round(feat_stats.completeness * 100, 2) if feat_stats.completeness else None
    }

result = {
    'stats': stats,
    'issues': issues,
    'entropy_issues': entropy_issues,
    'cardinality_issues': cardinality_issues,
    'enriched_metrics': enriched_metrics
}
```

DataVint SDK Info - 11 Detectors:
1. MissingValuesDetector - High null rates
2. DuplicatesDetector - Exact duplicate rows
3. SchemaViolationDetector - Type mismatches
4. NumericRangeDetector - Out-of-range values
5. TrainTestSkewDetector - Distribution shifts
6. ClassImbalanceDetector - Extreme class ratios
7. CompletenessDetector - Low completeness (NEW)
8. DistinctnessDetector - Few distinct values (NEW)
9. UniquenessDetector - Many duplicates (NEW)
10. EntropyDetector - Low/high information content (NEW)
11. CardinalityDetector - High cardinality categorical (NEW)

All detectors run automatically with vint.profile(df).

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
            model="claude-sonnet-4-6",  # Claude Sonnet 4.6 (Feb 2026)
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
