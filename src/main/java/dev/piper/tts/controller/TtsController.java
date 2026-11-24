package dev.piper.tts.controller;

import dev.piper.tts.config.AppConfig;
import dev.piper.tts.model.*;
import dev.piper.tts.service.PiperService;
import dev.piper.tts.service.TimingEstimator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

import java.nio.file.*;
import java.util.*;

@RestController
@RequestMapping("/api")
public class TtsController {

    private static final Logger log = LoggerFactory.getLogger(TtsController.class);

    private final AppConfig       cfg;
    private final PiperService    piper;
    private final TimingEstimator timing;

    public TtsController(AppConfig cfg, PiperService piper, TimingEstimator timing) {
        this.cfg    = cfg;
        this.piper  = piper;
        this.timing = timing;
    }

    // ── POST /api/synthesize ──────────────────────────────────────────────────

    @PostMapping("/synthesize")
    public ResponseEntity<?> synthesize(@RequestBody SynthesizeRequest req) {
        String text = req.text() == null ? "" : req.text().strip();
        if (text.isEmpty()) {
            return error("No text provided", HttpStatus.BAD_REQUEST);
        }
        if (req.voice() == null || req.voice().isBlank()) {
            return error("No voice selected", HttpStatus.BAD_REQUEST);
        }

        Path onnx = cfg.getVoicesDir().resolve(req.voice() + ".onnx");
        if (!Files.exists(onnx)) {
            return error("Voice not found: " + req.voice(), HttpStatus.NOT_FOUND);
        }

        // Slice from start_char if requested
        int startChar = Math.max(0, req.startChar());
        String speakText = startChar < text.length() ? text.substring(startChar) : text;
        if (speakText.isBlank()) {
            return error("Nothing to speak from that position", HttpStatus.BAD_REQUEST);
        }

        try {
            byte[] wav     = piper.synthesize(speakText, onnx, req.speed());
            double dur     = piper.getWavDuration(wav);
            int    cpm     = dur > 0 ? (int) Math.round(speakText.length() / (dur / 60.0)) : 0;
            var    timings = timing.estimate(speakText, dur, req.speed(),
                                             req.lang(), startChar);
            String audio   = Base64.getEncoder().encodeToString(wav);

            return ResponseEntity.ok(new SynthesizeResponse(audio, round3(dur), timings, cpm));

        } catch (Exception e) {
            log.error("Synthesis failed: {}", e.getMessage());
            return error(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // ── POST /api/export ─────────────────────────────────────────────────────

    @PostMapping("/export")
    public ResponseEntity<?> export(@RequestBody ExportRequest req) {
        String text = req.text() == null ? "" : req.text().strip();
        if (text.isEmpty()) {
            return error("No text provided", HttpStatus.BAD_REQUEST);
        }

        Path onnx = cfg.getVoicesDir().resolve(req.voice() + ".onnx");
        if (!Files.exists(onnx)) {
            return error("Voice not found: " + req.voice(), HttpStatus.NOT_FOUND);
        }

        try {
            byte[] wav = piper.synthesize(text, onnx, req.speed());
            return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType("audio/wav"))
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"piper-tts.wav\"")
                .body(wav);

        } catch (Exception e) {
            log.error("Export failed: {}", e.getMessage());
            return error(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static ResponseEntity<Map<String, String>> error(String msg, HttpStatus status) {
        return ResponseEntity.status(status).body(Map.of("error", msg));
    }

    private static double round3(double v) {
        return Math.round(v * 1000.0) / 1000.0;
    }
}
