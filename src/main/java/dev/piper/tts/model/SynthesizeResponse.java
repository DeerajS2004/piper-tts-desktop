package dev.piper.tts.model;

import java.util.List;

/**
 * POST /api/synthesize response body.
 * audio = base64-encoded WAV bytes.
 */
public record SynthesizeResponse(
    String          audio,
    double          duration,
    List<TimingEntry> timings,
    int             cpm
) {}
