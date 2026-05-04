# Useful Commands & Tips

## Session Management

- Save progress: `/context-save [optional-title]`
- Restore session: `/context-restore`
- List saved contexts: `/context-save list`
- List all branches: `/context-save list --all`

## Gstack Skills

- QA testing: `/qa`
- Investigation: `/investigate`
- Code review: `/review`
- Ship changes: `/ship`

## Learnings

- Record learning: `/learn` skill
- Learnings auto-load at session start

## Tested Public Problematic Datasets

### Titanic (Kaggle) ✅ TESTED
- **Size**: 891 passengers (59KB)
- **Quality Issues**: Missing Age (19%), duplicates (10%)
- **DataVint Results**: 
  - Detected 10.1% duplicates
  - AUC improved 0.842 → 0.845 (+0.4%)
  - Precision improved +2.8%
  - Removed 72 duplicate rows

### Amazon Electronics ✅ TESTED  
- **Size**: 1.4GB (100K reviews tested)
- **Finding**: Too clean in sample, has data leakage (rating → label)
- **Recommendation**: Use for scale testing, not quality detection

### Recommended Next Tests
1. UCI Dirty Datasets (various sizes)
2. OpenML tagged quality issues
3. MovieLens Anomalous (injected issues)
