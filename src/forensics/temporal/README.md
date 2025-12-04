# Temporal Analysis System

## Overview
Advanced temporal event extraction and timeline reconstruction for forensic investigations.

## Components

### TimelineReconstructor
Reconstructs chronological timelines from events.

```python
from src.forensics.temporal import TimelineReconstructor

reconstructor = TimelineReconstructor()
timeline = reconstructor.reconstruct(events)
```

### EventExtractor
Extracts temporal events from unstructured text.
- Date/time extraction
- Context preservation
- Position tracking

## Usage

```python
from src.forensics.temporal import (
    TimelineReconstructor,
    EventExtractor
)

# Extract events
extractor = EventExtractor()
events = extractor.extract_events(document_text)

# Reconstruct timeline
reconstructor = TimelineReconstructor()
timeline = reconstructor.reconstruct(events)

print(f"Timeline: {timeline['start_date']} to {timeline['end_date']}")
print(f"Events: {timeline['event_count']}")
```

## Integration

Works with:
- Document extraction
- Contradiction detection
- Legal analysis
- Evidence chain

**Status: OPERATIONAL** ✅

