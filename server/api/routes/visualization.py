"""
Visualization Board tab API routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models.response import IssuesResponse, ManifestResponse, IssueItem
from ..services.analysis import dataset_cache

router = APIRouter()


@router.get("/issues", response_model=IssuesResponse)
async def get_issues(dataset_id: str = Query(..., description="Dataset ID")):
    """
    Get detected issues for visualization
    """
    df, label_col = dataset_cache.get(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        from datavint.statistics import generate_statistics
        from datavint.issues import detect_issues

        # Generate statistics and detect issues
        stats = generate_statistics(df, label_col=label_col)
        issues = detect_issues(stats)

        # Convert issues to response format
        issue_items = []
        severity_count = {'high': 0, 'medium': 0, 'low': 0}

        for issue in issues:
            issue_item = IssueItem(
                type=issue.type.value,
                feature=issue.feature,
                severity=issue.severity.value,
                metric_value=issue.metric_value,
                threshold=issue.threshold,
                description=issue.description,
                impact={
                    'ne_direction': issue.ne_direction,
                    'auc_direction': issue.auc_direction
                }
            )
            issue_items.append(issue_item)
            severity_count[issue.severity.value] += 1

        return IssuesResponse(
            dataset_id=dataset_id,
            issues=issue_items,
            summary={
                'total': len(issues),
                'high': severity_count['high'],
                'medium': severity_count['medium'],
                'low': severity_count['low']
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect issues: {str(e)}")


@router.post("/manifest", response_model=ManifestResponse)
async def generate_manifest_endpoint(
    dataset_id: str = Query(..., description="Dataset ID"),
    apply_corrections: bool = Query(True, description="Whether to apply corrections")
):
    """
    Generate manifest from detected issues
    """
    df, label_col = dataset_cache.get(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        from datavint.statistics import generate_statistics
        from datavint.issues import detect_issues
        from datavint.profiling import generate_manifest

        # Generate statistics
        stats = generate_statistics(df, label_col=label_col)

        # Detect issues before
        issues_before = detect_issues(stats)

        # Generate manifest
        manifest = generate_manifest(stats)

        # Apply manifest if requested
        if apply_corrections:
            corrected_df = manifest.apply(df, inplace=False)

            # Re-detect issues after correction
            corrected_stats = generate_statistics(corrected_df, label_col=label_col)
            issues_after = detect_issues(corrected_stats)

            return ManifestResponse(
                manifest={
                    'rows_filtered': len(df) - len(corrected_df),
                    'rows_kept': len(corrected_df),
                    'sample_weights': {
                        'min': float(manifest.sample_weights.min()),
                        'max': float(manifest.sample_weights.max()),
                        'mean': float(manifest.sample_weights.mean())
                    },
                    'feature_fixes': manifest.feature_fixes
                },
                improvements={
                    'issues_before': len(issues_before),
                    'issues_after': len(issues_after),
                    'quality_score': 10.0 - len(issues_after)  # Simple scoring
                }
            )
        else:
            return ManifestResponse(
                manifest={
                    'rows_filtered': 0,
                    'rows_kept': len(df),
                    'sample_weights': {
                        'min': float(manifest.sample_weights.min()),
                        'max': float(manifest.sample_weights.max()),
                        'mean': float(manifest.sample_weights.mean())
                    },
                    'feature_fixes': manifest.feature_fixes
                },
                improvements={
                    'issues_before': len(issues_before),
                    'issues_after': 0,
                    'quality_score': 0.0
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate manifest: {str(e)}")
