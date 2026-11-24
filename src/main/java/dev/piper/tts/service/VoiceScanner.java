package dev.piper.tts.service;

import dev.piper.tts.config.AppConfig;
import dev.piper.tts.model.VoiceInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;

/**
 * Scans the voices directory and builds the list of available VoiceInfo objects.
 */
@Service
public class VoiceScanner {

    private static final Logger log = LoggerFactory.getLogger(VoiceScanner.class);

    // Known locale → (display name, ISO lang code, flag emoji)
    private static final Map<String, String[]> LOCALE_MAP = Map.of(
        "en_US", new String[]{"English (US)", "en", "🇺🇸"},
        "en_GB", new String[]{"English (UK)", "en", "🇬🇧"},
        "ja_JP", new String[]{"Japanese",     "ja", "🇯🇵"}
    );

    // Baseline CPM at 1× speed (from benchmarks)
    private static final Map<String, Integer> LANG_CPM = Map.of("en", 1160, "ja", 303);

    private final AppConfig cfg;

    public VoiceScanner(AppConfig cfg) { this.cfg = cfg; }

    public List<VoiceInfo> scanVoices() {
        Path dir = cfg.getVoicesDir();
        if (!Files.isDirectory(dir)) {
            log.warn("Voices directory not found: {}", dir);
            return List.of();
        }

        List<VoiceInfo> voices = new ArrayList<>();
        try (DirectoryStream<Path> ds = Files.newDirectoryStream(dir, "*.onnx")) {
            List<Path> files = new ArrayList<>();
            ds.forEach(files::add);
            files.sort(Comparator.comparing(p -> p.getFileName().toString()));

            for (Path f : files) {
                String name   = stripSuffix(f.getFileName().toString(), ".onnx");
                String[] parts = name.split("-");
                String locale  = parts[0];
                String[] info  = LOCALE_MAP.getOrDefault(locale,
                                     new String[]{locale, "en", ""});
                String dispName = info[0];
                String lang     = info[1];
                String flag     = info[2];

                String speaker = parts.length > 1
                    ? capitalize(String.join(" ", Arrays.copyOfRange(parts, 1, parts.length)))
                    : "";
                String label = (flag + " " + dispName + (speaker.isEmpty() ? "" : " — " + speaker)).strip();

                voices.add(new VoiceInfo(
                    name,
                    f.toAbsolutePath().toString(),
                    lang,
                    label,
                    LANG_CPM.getOrDefault(lang, 1160)
                ));
            }
        } catch (IOException e) {
            log.error("Error scanning voices dir: {}", e.getMessage());
        }
        return voices;
    }

    private static String stripSuffix(String s, String suffix) {
        return s.endsWith(suffix) ? s.substring(0, s.length() - suffix.length()) : s;
    }

    private static String capitalize(String s) {
        if (s == null || s.isEmpty()) return s;
        return Character.toUpperCase(s.charAt(0)) + s.substring(1);
    }
}
