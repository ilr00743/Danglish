# DanGlish Context

DanGlish lets a learner search Danish transcript data and play the matching YouTube moment with surrounding caption context.

## Language

**Search Match**:
A caption row that contains the searched Danish word and can be selected for playback.
_Avoid_: Result item, hit

**PlaybackSession**:
The active viewing state for one selected Search Match, including seek target, player time, loaded captions, and current caption.
_Avoid_: Player state, caption state

**SearchLanguage**:
The Danish word matching rules used to find and highlight Search Matches.
_Avoid_: Regex helper, query utility

**TranscriptRepository**:
The local transcript storage module that searches captions, lists video captions, and replaces stored video transcripts.
_Avoid_: Database helper, SQL wrapper

**IngestionPipeline**:
The process that turns YouTube channel videos into stored manual Danish transcript data.
_Avoid_: Scraper, import script

**Current Caption**:
The caption row whose time range contains the YouTube player's current playback time.
_Avoid_: Active subtitle, live text
