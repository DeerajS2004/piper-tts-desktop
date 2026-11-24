package dev.piper.tts.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Timing for a single word/character token.
 * start_char / end_char are absolute offsets in the FULL text.
 */
public record TimingEntry(
    int idx,
    String text,
    @JsonProperty("start_char")  int    startChar,
    @JsonProperty("end_char")    int    endChar,
    @JsonProperty("start_time")  double startTime,
    @JsonProperty("end_time")    double endTime
) {}
