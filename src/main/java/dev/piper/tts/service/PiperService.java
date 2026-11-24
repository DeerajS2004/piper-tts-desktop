package dev.piper.tts.service;

import dev.piper.tts.config.AppConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

/**
 * Calls the native piper binary via ProcessBuilder and returns raw WAV bytes.
 */
@Service
public class PiperService {

    private static final Logger log = LoggerFactory.getLogger(PiperService.class);

    private final AppConfig cfg;
    private final ExecutorService ioExecutor = Executors.newCachedThreadPool(r -> {
        Thread t = new Thread(r, "piper-io");
        t.setDaemon(true);
        return t;
    });

    public PiperService(AppConfig cfg) { this.cfg = cfg; }

    /**
     * Synthesize text and return WAV bytes.
     *
     * @param text     text to speak
     * @param onnxPath absolute path to the .onnx voice model
     * @param speed    playback speed multiplier (0.5 – 2.0)
     */
    public byte[] synthesize(String text, Path onnxPath, double speed) throws Exception {
        Path tmpWav = Files.createTempFile("piper_", ".wav");
        try {
            List<String> cmd = buildCmd(onnxPath, tmpWav, speed);
            log.debug("Running: {}", String.join(" ", cmd));

            Path piperDir = cfg.getPiperBin().getParent();
            ProcessBuilder pb = new ProcessBuilder(cmd)
                // Run from piper's own directory so it finds espeak-ng-data + .so files
                .directory(piperDir != null ? piperDir.toFile() : null);

            // Set LD_LIBRARY_PATH so native libs are found regardless of cwd
            if (piperDir != null) {
                pb.environment().merge("LD_LIBRARY_PATH",
                    piperDir.toAbsolutePath().toString(),
                    (existing, added) -> added + ":" + existing);
            }

            Process proc = pb.start();

            // Write text to piper's stdin in a background thread (avoid deadlock)
            Future<?> stdinWriter = ioExecutor.submit(() -> {
                try (OutputStream out = proc.getOutputStream()) {
                    out.write(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                } catch (IOException ignored) {}
            });

            // Drain stderr in background (piper logs progress there)
            Future<String> stderrReader = ioExecutor.submit(() -> {
                try { return new String(proc.getErrorStream().readAllBytes()); }
                catch (IOException e) { return ""; }
            });

            boolean finished = proc.waitFor(cfg.getTimeout(), TimeUnit.SECONDS);
            stdinWriter.get(5, TimeUnit.SECONDS);
            String stderr = stderrReader.get(5, TimeUnit.SECONDS);

            if (!finished) {
                proc.destroyForcibly();
                throw new RuntimeException("piper timed out after " + cfg.getTimeout() + "s");
            }
            if (proc.exitValue() != 0) {
                throw new RuntimeException("piper exited " + proc.exitValue() + ": " + stderr.trim());
            }

            return Files.readAllBytes(tmpWav);
        } finally {
            Files.deleteIfExists(tmpWav);
        }
    }

    /**
     * Extract duration (seconds) from a WAV byte array using javax.sound.
     */
    public double getWavDuration(byte[] wavBytes) {
        try (AudioInputStream ais = AudioSystem.getAudioInputStream(
                new BufferedInputStream(new ByteArrayInputStream(wavBytes)))) {
            long frames = ais.getFrameLength();
            float rate  = ais.getFormat().getFrameRate();
            if (frames > 0 && rate > 0) return (double) frames / rate;
        } catch (Exception e) {
            log.warn("Could not read WAV duration: {}", e.getMessage());
        }
        return 0.0;
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private List<String> buildCmd(Path onnxPath, Path outWav, double speed) {
        List<String> cmd = new ArrayList<>();
        cmd.add(cfg.getPiperBin().toAbsolutePath().toString());
        cmd.add("--model");        cmd.add(onnxPath.toAbsolutePath().toString());
        cmd.add("--output_file");  cmd.add(outWav.toAbsolutePath().toString());
        if (Math.abs(speed - 1.0) > 0.001) {
            cmd.add("--length_scale");
            cmd.add(String.format(Locale.US, "%.4f", 1.0 / speed));
        }
        return cmd;
    }
}
