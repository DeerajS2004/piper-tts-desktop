package dev.piper.tts;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.awt.Desktop;
import java.net.URI;

@SpringBootApplication
public class PiperTtsApplication {

    public static void main(String[] args) {
        SpringApplication.run(PiperTtsApplication.class, args);
        openBrowser();
    }

    private static void openBrowser() {
        // Open the browser after a short delay so the server is ready
        new Thread(() -> {
            try {
                Thread.sleep(900);
                String url = "http://localhost:5000";
                if (Desktop.isDesktopSupported() && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
                    Desktop.getDesktop().browse(new URI(url));
                } else {
                    // Fallback for Linux systems where Desktop may not be supported
                    new ProcessBuilder("xdg-open", url).start();
                }
            } catch (Exception ignored) {}
        }, "browser-opener").start();
    }
}
