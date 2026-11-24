package dev.piper.tts.controller;

import dev.piper.tts.model.VoiceInfo;
import dev.piper.tts.service.VoiceScanner;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
public class VoiceController {

    private final VoiceScanner scanner;

    public VoiceController(VoiceScanner scanner) { this.scanner = scanner; }

    /** GET /api/voices — returns list of installed voices. */
    @GetMapping("/voices")
    public List<VoiceInfo> voices() {
        return scanner.scanVoices();
    }
}
