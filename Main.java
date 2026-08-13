import javax.swing.*;

public class Main {

    public static void main(String[] args) {

        UIManager.put("Button.arc", 20);
        UIManager.put("Component.arc", 20);

        SwingUtilities.invokeLater(() -> {
            new LoginForm().setVisible(true);
        });
    }
}