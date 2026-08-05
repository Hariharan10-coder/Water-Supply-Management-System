# Water Supply Management System — Login, Dashboard, Authentication

Java Swing desktop app (matches your SRS: Java + MySQL + JDBC) implementing:
- **FR1 User Login** — username/password authentication against MySQL
- **Role-based Dashboard** — different menu items for Admin / Officer / Maintenance / Customer
- **Logout** — returns to the login screen
- **Encrypted password storage** — SHA-256 hashing (NFR: Security)

## Files
- `DBConnection.java` — MySQL JDBC connection
- `PasswordUtil.java` — SHA-256 password hashing (also runnable to generate hashes)
- `User.java` — simple user session model
- `LoginForm.java` — login screen + authentication logic
- `Dashboard.java` — post-login dashboard with role-based menu + logout
- `database.sql` — creates the database, `users` table, and supporting tables from SRS section 6

## 1. Prerequisites
- Java JDK 17 (as specified in your SRS)
- MySQL Server, running locally
- MySQL Connector/J (JDBC driver) — download the `.jar` from
  https://dev.mysql.com/downloads/connector/j/

## 2. Set up the database
```bash
mysql -u root -p < database.sql
```
Then generate real password hashes and update the `users` table:
```bash
javac PasswordUtil.java
java PasswordUtil admin123
```
Copy the printed hash and run, for example:
```sql
UPDATE users SET password = '<hash>' WHERE username = 'admin';
```
Repeat for `officer`, `staff`, `customer` (or add your own users).

## 3. Configure the connection
Open `DBConnection.java` and set your MySQL password:
```java
private static final String DB_PASSWORD = "your_mysql_password";
```

## 4. Compile and run
Place `mysql-connector-j-<version>.jar` in the same folder, then:

**Windows:**
```bash
javac *.java
java -cp ".;mysql-connector-j-9.0.0.jar" LoginForm
```

**macOS/Linux:**
```bash
javac *.java
java -cp ".:mysql-connector-j-9.0.0.jar" LoginForm
```

The login window opens first. Log in with one of the seeded usernames
(`admin`, `officer`, `staff`, `customer`) and the password you hashed in
step 2 — you'll land on the role-appropriate dashboard, and Logout returns
you to the login screen.

## Next steps (to complete the rest of your SRS)
Each dashboard button currently opens a placeholder dialog. Wire them up to
real screens as you build out FR2–FR8: Customer Management, Billing,
Maintenance Requests, Leakage Reporting, Complaints, and Reports — using the
`customer`, `water_usage`, `billing`, `maintenance`, and `complaint` tables
already created in `database.sql`.
