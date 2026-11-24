package dev.piper.tts;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.awt.Desktop;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.URI;

@SpringBootApplication
public class PiperTtsApplication {

    private static final Logger log = LoggerFactory.getLogger(PiperTtsApplication.class);

    public static void main(String[] args) {
        int port = findFreePort(5000);

        SpringApplication app = new SpringApplication(PiperTtsApplication.class);
        app.setDefaultProperties(java.util.Map.of("server.port", String.valueOf(port)));
        app.run(args);

        log.info("🎤 Piper TTS running at http://localhost:{}", port);
        openBrowser(port);
    }

    /**
     * Find the first free TCP port starting from {@code preferred}.
     * Tries preferred, preferred+1, … up to preferred+99.
     */
    static int findFreePort(int preferred) {
        for (int p = preferred; p < preferred + 100; p++) {
            try (ServerSocket s = new ServerSocket(p)) {
                s.setReuseAddress(true);
                return p;
            } catch (IOException ignored) {}
        }
        // Last resort: let OS assign any free port
        try (ServerSocket s = new ServerSocket(0)) {
            return s.getLocalPort();
        } catch (IOException e) {
            throw new RuntimeException("No free port found", e);
        }
    }

    private static void openBrowser(int port) {
        new Thread(() -> {
            try {
                Thread.sleep(900);
                String url = "http://localhost:" + port;
                if (Desktop.isDesktopSupported()
                        && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
                    Desktop.getDesktop().browse(new URI(url));
                } else {
                    new ProcessBuilder("xdg-open", url).start();
                }
            } catch (Exception ignored) {}
        }, "browser-opener").start();
    }
}
