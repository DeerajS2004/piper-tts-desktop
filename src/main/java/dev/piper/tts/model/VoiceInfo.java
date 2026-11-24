package dev.piper.tts.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Describes an available .onnx voice.
 * cpm1x = baseline characters-per-minute at 1× speed (from benchmarks).
 */
public record VoiceInfo(
    String id,
    String onnx,
    String lang,
    String label,
    @JsonProperty("cpm_1x") int cpm1x
) {}
