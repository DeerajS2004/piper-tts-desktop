package dev.piper.tts.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

import jakarta.annotation.PostConstruct;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

/**
 * Resolves piper binary and voices directory at startup.
 * Priority: env var → application.properties → known install locations.
 */
@Configuration
public class AppConfig {

    private static final Logger log = LoggerFactory.getLogger(AppConfig.class);

    @Value("${piper.bin:}")
    private String piperBinProp;

    @Value("${piper.voices.dir:}")
    private String voicesDirProp;

    @Value("${piper.timeout:120}")
    private int timeoutSeconds;

    private Path resolvedPiperBin;
    private Path resolvedVoicesDir;

    @PostConstruct
    public void resolve() {
        resolvedPiperBin  = resolvePiperBin();
        resolvedVoicesDir = resolveVoicesDir();

        log.info("Piper binary  : {}", resolvedPiperBin);
        log.info("Voices dir    : {}", resolvedVoicesDir);

        if (!Files.isExecutable(resolvedPiperBin)) {
            log.warn("⚠️  piper binary not executable: {}", resolvedPiperBin);
        }
        if (!Files.isDirectory(resolvedVoicesDir)) {
            log.warn("⚠️  voices directory not found: {}", resolvedVoicesDir);
        }
    }

    // ── Piper binary ──────────────────────────────────────────────────────────

    private Path resolvePiperBin() {
        String home = System.getProperty("user.home");

        List<String> candidates = List.of(
            envOr("PIPER_BIN", ""),
            piperBinProp,
            // Native C++ binary (downloaded by install.sh)
            home + "/.local/share/piper-tts/bin/piper/piper",
            // Python-based piper-tts CLI (legacy)
            home + "/.local/share/piper-tts/venv/bin/piper",
            // System .deb install
            "/usr/share/piper-tts/venv/bin/piper",
            // Generic PATH lookup
            "piper"
        );

        for (String c : candidates) {
            if (c == null || c.isBlank()) continue;
            Path p = Paths.get(c).toAbsolutePath();
            if (Files.exists(p)) return p;
        }
        return Paths.get("piper"); // last resort — rely on PATH
    }

    // ── Voices directory ──────────────────────────────────────────────────────

    private Path resolveVoicesDir() {
        String home = System.getProperty("user.home");

        List<String> candidates = List.of(
            envOr("PIPER_VOICES_DIR", ""),
            voicesDirProp,
            home + "/.local/share/piper-tts/voices",
            "/usr/share/piper-tts/voices"
        );

        for (String c : candidates) {
            if (c == null || c.isBlank()) continue;
            Path p = Paths.get(c).toAbsolutePath();
            if (Files.isDirectory(p)) return p;
        }
        return Paths.get(home, ".local/share/piper-tts/voices");
    }

    // ── Accessors ─────────────────────────────────────────────────────────────

    public Path getPiperBin()     { return resolvedPiperBin; }
    public Path getVoicesDir()    { return resolvedVoicesDir; }
    public int  getTimeout()      { return timeoutSeconds; }

    private static String envOr(String key, String def) {
        String v = System.getenv(key);
        return (v != null && !v.isBlank()) ? v : def;
    }
}
