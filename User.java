/**
 * Simple model representing an authenticated user session.
 */
public class User {
    private final int userId;
    private final String username;
    private final String role; // Admin, Officer, Maintenance, Customer

    public User(int userId, String username, String role) {
        this.userId = userId;
        this.username = username;
        this.role = role;
    }

    public int getUserId() { return userId; }
    public String getUsername() { return username; }
    public String getRole() { return role; }
}
