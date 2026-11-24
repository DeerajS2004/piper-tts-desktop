package dev.piper.tts.model;

/** POST /api/export request body. */
public record ExportRequest(
    String text,
    String voice,
    double speed
) {
    public ExportRequest {
        if (speed <= 0) speed = 1.0;
    }
}
