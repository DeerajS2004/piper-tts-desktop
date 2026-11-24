package dev.piper.tts.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * POST /api/synthesize request body.
 * start_char: offset in `text` to begin speaking from (0 = beginning).
 */
public record SynthesizeRequest(
    String text,
    String voice,
    double speed,
    @JsonProperty("start_char") int    startChar,
    String lang
) {
    /** Apply defaults for null / missing fields */
    public SynthesizeRequest {
        if (speed  <= 0) speed      = 1.0;
        if (lang   == null) lang    = "en";
        if (startChar < 0)  startChar = 0;
    }
}
