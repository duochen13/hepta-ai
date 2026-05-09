"""
Raw Data tab API routes
"""

import uuid
import pandas as pd
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional
import json

from ..models.response import DataPreviewResponse, StatisticsResponse
from ..services.analysis import dataset_cache

router = APIRouter()


def clean_dataframe_for_json(df: pd.DataFrame) -> list:
    """
    Convert DataFrame to list of dicts with proper JSON serialization.
    Handles NaN, inf, and -inf values by converting them to None.
    """
    # Replace inf and -inf with None
    df_clean = df.replace([np.inf, -np.inf], np.nan)

    # Convert to dict, NaN will become None automatically with orient='records'
    # But we need to use a custom JSON encoder
    records = df_clean.to_dict('records')

    # Clean each record
    cleaned_records = []
    for record in records:
        cleaned_record = {}
        for key, value in record.items():
            if pd.isna(value):
                cleaned_record[key] = None
            elif isinstance(value, (np.floating, float)):
                if np.isnan(value) or np.isinf(value):
                    cleaned_record[key] = None
                else:
                    cleaned_record[key] = float(value)
            elif isinstance(value, (np.integer, int)):
                cleaned_record[key] = int(value)
            elif isinstance(value, np.bool_):
                cleaned_record[key] = bool(value)
            else:
                cleaned_record[key] = value
        cleaned_records.append(cleaned_record)

    return cleaned_records


@router.post("/upload")
async def upload_data(
    file: UploadFile = File(...),
    label_col: Optional[str] = Form(None)
):
    """
    Upload CSV dataset for analysis

    Returns a dataset_id that can be used in subsequent requests.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(contents))

        # Generate unique dataset ID
        dataset_id = str(uuid.uuid4())

        # Store in cache
        dataset_cache.store(dataset_id, df, label_col)

        # Get preview (first 50 rows)
        preview_df = df.head(50)
        preview_rows = clean_dataframe_for_json(preview_df)

        return {
            "success": True,
            "dataset_id": dataset_id,
            "preview": {
                "rows": len(df),
                "columns": len(df.columns),
                "sample": preview_rows
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@router.get("/preview", response_model=DataPreviewResponse)
async def get_preview(
    dataset_id: str = Query(..., description="Dataset ID from upload"),
    limit: int = Query(50, description="Number of rows to return")
):
    """
    Get dataset preview (first N rows)
    """
    df, _ = dataset_cache.get(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    preview_df = df.head(limit)
    rows = clean_dataframe_for_json(preview_df)

    return DataPreviewResponse(
        dataset_id=dataset_id,
        total_rows=len(df),
        columns=df.columns.tolist(),
        rows=rows
    )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(dataset_id: str = Query(..., description="Dataset ID")):
    """
    Get dataset statistics
    """
    df, label_col = dataset_cache.get(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        from datavint.statistics import generate_statistics

        # Generate statistics
        stats = generate_statistics(df, label_col=label_col)

        # Convert to dict format with enriched metrics
        features_dict = {}
        for feature_name, feature_stats in stats.features.items():
            features_dict[feature_name] = {
                'name': feature_stats.name,
                'type': feature_stats.type,
                'count': feature_stats.count,
                'null_count': feature_stats.null_count,
                'null_rate': feature_stats.null_rate,
                # Enriched metrics (available for all features)
                'completeness': feature_stats.completeness,
                'distinct_count': feature_stats.distinct_count,
                'distinctness': feature_stats.distinctness,
                'uniqueness': feature_stats.uniqueness,
                'unique_value_ratio': feature_stats.unique_value_ratio,
                'entropy': feature_stats.entropy,
            }

            # Numeric-specific fields
            if feature_stats.type == 'numeric':
                features_dict[feature_name].update({
                    'mean': feature_stats.mean,
                    'std': feature_stats.std,
                    'min': feature_stats.min,
                    'max': feature_stats.max,
                    'median': feature_stats.median,
                    'p25': feature_stats.p25,
                    'p75': feature_stats.p75,
                    'p99': feature_stats.p99,
                    'sum': feature_stats.sum,
                    'q10': feature_stats.q10,
                    'q90': feature_stats.q90,
                })

            # Categorical-specific fields
            if feature_stats.type == 'categorical':
                features_dict[feature_name].update({
                    'unique_count': feature_stats.unique_count,
                    'top_values': feature_stats.top_values,
                })

        return StatisticsResponse(
            dataset_id=dataset_id,
            statistics={
                'n_rows': stats.n_rows,
                'n_cols': stats.n_cols,
                'label_col': stats.label_col,
                'label_rate': stats.label_rate,
                'label_entropy': stats.label_entropy,
                'duplicate_count': stats.duplicate_count,
                'duplicate_rate': stats.duplicate_rate,
                'features': features_dict
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate statistics: {str(e)}")
