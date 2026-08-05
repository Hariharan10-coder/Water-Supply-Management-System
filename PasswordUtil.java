import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;

/**
 * Simple SHA-256 password hashing so passwords are never stored in
 * plain text, per the SRS "Encrypted Password Storage" requirement.
 */
public class PasswordUtil {

    public static String hashPassword(String plainPassword) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashBytes = digest.digest(plainPassword.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : hashBytes) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) sb.append('0');
                sb.append(hex);
            }
            return sb.toString();
        } catch (Exception e) {
            throw new RuntimeException("Error while hashing password", e);
        }
    }

    /**
     * Run this class directly to generate a hash for a password you want
     * to insert into the database (e.g. for creating the first admin user).
     * Usage: java PasswordUtil admin123
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java PasswordUtil <password>");
            return;
        }
        System.out.println("Hashed password: " + hashPassword(args[0]));
    }
}
