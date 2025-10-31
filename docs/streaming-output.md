# Streaming CSV Output for Fuzzy Matching

## Overview

The streaming output feature allows you to see fuzzy matching results in real-time as they're generated, rather than waiting for all items to complete.

## Usage

### Batch Mode (Original)
```bash
python run_fuzzy_matching.py
```
- Waits for all 319 items to complete
- Writes CSV at the end
- Total time: ~37 minutes

### Streaming Mode (New)
```bash
python run_fuzzy_matching_streaming.py
```
- Writes each result to CSV immediately
- Shows real-time progress with ETA
- Can view results while processing continues
- Same total time, but results available immediately

## Monitoring Real-Time Output

While the streaming script is running, you can watch results appear in another terminal:

```bash
# Watch file grow
watch -n 1 wc -l out-match-streaming.csv

# Tail the file to see new results
tail -f out-match-streaming.csv

# Count successful matches so far
grep -c "match_1_bibkey.*:" out-match-streaming.csv
```

## Progress Indicator

The streaming script shows real-time progress:

```
[10/319] Avg: 7.2s/item | ETA: 37.1min | Matches: 8 (5 good)
```

- **Processed**: How many items matched so far
- **Avg**: Average time per item
- **ETA**: Estimated time to completion
- **Matches**: Items with at least one match (score >= 50)
- **(good)**: Items with strong match (score >= 100)

## Implementation

### Key Components

1. **`stage_bibitems_streaming()` (fuzzy_matcher.py)**
   - Generator function that yields results one at a time
   - Same logic as batch version, just streaming

2. **CSV Flushing (run_fuzzy_matching_streaming.py)**
   - Opens CSV before matching starts
   - Writes header immediately
   - Flushes after each row (`f.flush()`)
   - Ensures results are visible in real-time

3. **Progress Tracking**
   - Updates console every item
   - Shows statistics as they accumulate
   - Calculates ETA based on average time

## Benefits

### Real-Time Visibility
- See results as soon as they're ready
- Monitor progress and performance
- Identify issues early

### Interruption Safe
- Ctrl+C preserves partial results
- Already-matched items are in the CSV
- Can resume or analyze partial data

### Better UX
- No more waiting blindly for 37 minutes
- Know exactly how much longer to wait
- Can start reviewing early results

## Performance

Streaming adds minimal overhead:
- **Flush cost**: ~0.1-1ms per row
- **Total impact**: ~0.3-3 seconds for 319 items
- **Negligible** compared to 7s matching time per item

## Technical Details

### Generator Pipeline

```python
# Stream results as they're generated
for staged_item in stage_bibitems_streaming(staging_items, index):
    # Each iteration yields one matched item
    row = extract_bibitem_fields(staged_item.bibitem)
    writer.writerow(row)
    f.flush()  # Ensure immediate visibility
```

### Backward Compatibility

Both versions coexist:
- `stage_bibitems_batch()` - Returns tuple (original)
- `stage_bibitems_streaming()` - Returns generator (new)
- `run_fuzzy_matching.py` - Batch script (unchanged)
- `run_fuzzy_matching_streaming.py` - Streaming script (new)

## Future Enhancements

### Possible Optimizations

1. **Buffered Flushing**
   ```python
   if idx % 10 == 0:  # Flush every 10 rows
       f.flush()
   ```
   Trade-off: Less real-time but faster

2. **Progress Bar (tqdm)**
   ```python
   from tqdm import tqdm
   for item in tqdm(stage_bibitems_streaming(...)):
       # Nice progress bar with ETA
   ```

3. **Parallel Matching**
   - Use multiprocessing to match multiple items simultaneously
   - Would require thread-safe CSV writing
   - Could reduce total time significantly

## Example Output

```
================================================================================
FUZZY MATCHING: STAGING ITEMS AGAINST FULL BIBLIOGRAPHY (STREAMING)
================================================================================

[1/5] Loading bibliography from ODS...
      ✓ Loaded 209,622 items in 16.10s

[2/5] Loading staging items from CSV...
      ✓ Loaded 319 staging items in 0.01s

[3/5] Building fuzzy matching index...
      ✓ Built index in 41.26s
        - DOI index: 12,768 entries
        - Title trigrams: 26,889 unique
        - Author surnames: 35,664 unique

[4/5] Running fuzzy matching on 319 items (STREAMING)...
      Results are being written to CSV in real-time!

      [142/319] Avg: 7.1s/item | ETA: 21.0min | Matches: 115 (87 good)

💡 TIP: You can tail the output file to see results as they're generated:
   tail -f out-match-streaming.csv
================================================================================
```

## Comparison

| Feature | Batch Mode | Streaming Mode |
|---------|------------|----------------|
| Output visibility | At end only | Real-time |
| Progress tracking | None | Detailed |
| Interruption safe | No | Yes |
| Partial results | No | Yes |
| Performance | Same | Same |
| Memory usage | Slightly higher | Slightly lower |

## When to Use Which

**Use Batch Mode when:**
- Running automated/scheduled jobs
- Don't need to monitor progress
- Want to minimize I/O operations

**Use Streaming Mode when:**
- Running interactively
- Want to see results immediately
- Processing large batches
- Need progress visibility
- Want partial results if interrupted

## Conclusion

The streaming implementation provides the same results as batch mode but with much better user experience during long-running operations. It's especially valuable for the 319-item dataset which takes ~37 minutes to complete.
