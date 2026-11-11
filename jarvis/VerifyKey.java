import java.net.URI;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import javax.tools.SimpleJavaFileObject;
import javax.tools.JavaFileObject;
import javax.tools.ToolProvider;

/** Run the actual validator decompiled from the resulting DEX, with a Base64 stub. */
public class VerifyKey {
    static JavaFileObject source(String name, String contents) {
        return new SimpleJavaFileObject(URI.create("string:///" + name.replace('.', '/') + ".java"), JavaFileObject.Kind.SOURCE) {
            public CharSequence getCharContent(boolean ignored) { return contents; }
        };
    }

    public static void main(String[] args) throws Exception {
        String actual = Files.readString(Path.of(args[0]));
        // DEX does not require a Java checked-exception declaration. Restore only
        // that declaration for javac; both method bodies remain unchanged.
        actual = actual.replace("public static String c(int i) {",
                                "public static String c(int i) throws GeneralSecurityException {");
        Path output = Files.createTempDirectory("jarvis-key-check-");
        String stub = "package android.util; public class Base64 { public static byte[] decode(String s,int flags) { return java.util.Base64.getMimeDecoder().decode(s); } }";
        var compiler = ToolProvider.getSystemJavaCompiler();
        boolean compiled = compiler.getTask(null, null, null, List.of("-d", output.toString()), null,
            List.of(source("com.x.icon_crack_.io.q.b", actual), source("android.util.Base64", stub))).call();
        if (!compiled) throw new AssertionError("Actual decompiled validator did not compile");
        try (var loader = new URLClassLoader(new java.net.URL[]{output.toUri().toURL()})) {
            var type = loader.loadClass("com.x.icon_crack_.io.q.b");
            var validate = type.getMethod("a", String.class);
            var text = type.getMethod("c", int.class);
            String[] inputs = {"@Icon_Crack", "@faustgenius", " @Icon_Crack ", "@icon_crack", "", "random", null};
            for (int i = 0; i < inputs.length; i++) {
                boolean expected = i == 0;
                boolean result = (boolean) validate.invoke(null, (Object) inputs[i]);
                if (result != expected) throw new AssertionError("Local validator case " + i);
                boolean regexGate = inputs[i] != null && inputs[i].matches((String) text.invoke(null, 0));
                if (regexGate != expected) throw new AssertionError("Login format gate case " + i);
            }
            if (!"t.me/Icon_Crack".equals(text.invoke(null, 1))) throw new AssertionError("Telegram caption");
            if (!"Ключ: @Icon_Crack".equals(text.invoke(null, 3))) throw new AssertionError("Key caption");
            for (int i = 0; i < 8; i++) {
                String value = (String) text.invoke(null, i);
                if (value.toLowerCase().contains("faust")) throw new AssertionError("Old attribution at " + i);
            }
            System.out.println("PASS: 7 actual validator cases, 7 login-format cases, 8 decoded strings");
        }
    }
}
