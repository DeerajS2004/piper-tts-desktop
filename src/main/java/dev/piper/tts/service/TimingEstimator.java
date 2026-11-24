package dev.piper.tts.service;

import dev.piper.tts.model.TimingEntry;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.*;

/**
 * Estimates per-word / per-character timing from total audio duration,
 * using benchmark pause data for English and Japanese punctuation.
 *
 * Pause values (seconds at 1× speed) measured from actual piper output:
 *   EN: .=+0.50  ,=+0.27  ;=+0.78  :=+0.42  !=+0.33  ?=+0.46  \n=+0.35  …=-0.16
 *   JA: 。=+0.72 ！=+0.65 ？=+0.91 、=0.00  \n=+0.70  …=-0.08
 */
@Service
public class TimingEstimator {

    // EN pause data (character → pause seconds at 1× speed)
    private static final Map<Character, Double> EN_PAUSES = Map.of(
        '.', 0.50, ',', 0.27, ';', 0.78, ':',  0.42,
        '!', 0.33, '?', 0.46, '\n', 0.35, '…', -0.16
    );

    // JA pause data
    private static final Map<Character, Double> JA_PAUSES = Map.of(
        '。', 0.72, '！', 0.65, '？', 0.91, '、', 0.00,
        '\n', 0.70, '…', -0.08
    );

    // Pattern to strip non-word characters from English words (for speech char count)
    private static final Pattern EN_SPEECH_CHARS = Pattern.compile("[^\\w']");

    /**
     * Estimate timing for each word/character token.
     *
     * @param text          the text that was synthesized (may start at offset)
     * @param totalDuration total audio duration in seconds
     * @param speed         playback speed multiplier
     * @param lang          "en" or "ja"
     * @param offset        character offset of text within the full document
     * @return list of TimingEntry, one per word (EN) or character (JA)
     */
    public List<TimingEntry> estimate(String text, double totalDuration,
                                     double speed, String lang, int offset) {
        boolean isJa = "ja".equals(lang);
        Map<Character, Double> pauses = isJa ? JA_PAUSES : EN_PAUSES;
        List<Token> tokens = tokenize(text, isJa, pauses, offset);
        if (tokens.isEmpty()) return List.of();

        double totalChars = tokens.stream().mapToInt(t -> t.chars).sum();
        // Pauses scale inversely with speed; negative pauses (…) don't subtract from total
        double totalPause = tokens.stream()
            .mapToDouble(t -> Math.max(0.0, t.pause) / speed)
            .sum();
        double speechTime = Math.max(0.01, totalDuration - totalPause);
        double tpc = speechTime / Math.max(totalChars, 1); // time-per-speech-char

        List<TimingEntry> result = new ArrayList<>(tokens.size());
        double cur = 0.0;
        for (int i = 0; i < tokens.size(); i++) {
            Token tok = tokens.get(i);
            double dur = Math.max(0.0, tok.chars * tpc + tok.pause / speed);
            result.add(new TimingEntry(
                i,
                tok.text,
                tok.startChar,
                tok.endChar,
                round4(cur),
                round4(cur + dur)
            ));
            cur += dur;
        }
        return result;
    }

    // ── Tokenization ──────────────────────────────────────────────────────────

    private List<Token> tokenize(String text, boolean isJa,
                                 Map<Character, Double> pauses, int offset) {
        if (isJa) return tokenizeJa(text, pauses, offset);
        else       return tokenizeEn(text, pauses, offset);
    }

    /** Japanese: each non-whitespace character is its own token. */
    private List<Token> tokenizeJa(String text, Map<Character, Double> pauses, int offset) {
        List<Token> toks = new ArrayList<>();
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (ch == ' ' || ch == '\t' || ch == '\r') continue;
            boolean isPunct = pauses.containsKey(ch);
            toks.add(new Token(
                String.valueOf(ch),
                offset + i,
                offset + i + 1,
                isPunct ? 0 : 1,          // punct chars have 0 speech chars, just pause
                pauses.getOrDefault(ch, 0.0)
            ));
        }
        return toks;
    }

    /** English: each whitespace-delimited word is a token. */
    private List<Token> tokenizeEn(String text, Map<Character, Double> pauses, int offset) {
        List<Token> toks = new ArrayList<>();
        Matcher m = Pattern.compile("\\S+").matcher(text);
        while (m.find()) {
            String word = m.group();
            int sc = offset + m.start();
            int ec = offset + m.end();

            // Speech chars = letters/digits/apostrophes only
            int speechChars = Math.max(
                EN_SPEECH_CHARS.matcher(word).replaceAll("").length(), 1);

            // Sum pauses from any punctuation chars inside the word
            double pause = 0.0;
            for (char c : word.toCharArray()) {
                pause += pauses.getOrDefault(c, 0.0);
            }
            // Extra pause if immediately followed by a newline
            int end = m.end();
            if (end < text.length() && text.charAt(end) == '\n') {
                pause += pauses.getOrDefault('\n', 0.0);
            }

            toks.add(new Token(word, sc, ec, speechChars, pause));
        }
        return toks;
    }

    private static double round4(double v) {
        return Math.round(v * 10000.0) / 10000.0;
    }

    // ── Internal token ────────────────────────────────────────────────────────

    private record Token(String text, int startChar, int endChar, int chars, double pause) {}
}
