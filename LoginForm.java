import javax.swing.*;
import java.awt.*;
import java.sql.*;

public class LoginForm extends JFrame {

    JTextField username;
    JPasswordField password;

    public LoginForm(){

        setTitle("Water Supply Management System");
        setSize(450,350);
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        JPanel main = new JPanel();
        main.setBackground(new Color(20,120,180));
        main.setLayout(new GridBagLayout());


        JPanel card = new JPanel();
        card.setPreferredSize(new Dimension(320,240));
        card.setBackground(Color.WHITE);
        card.setLayout(null);


        JLabel title = new JLabel("💧 Water Supply");
        title.setFont(new Font("Arial",Font.BOLD,24));
        title.setBounds(70,20,250,40);


        username = new JTextField();
        username.setBounds(50,80,220,35);


        password = new JPasswordField();
        password.setBounds(50,125,220,35);


        JButton login = new JButton("LOGIN");
        login.setBounds(50,175,220,35);
        login.setBackground(new Color(20,120,180));
        login.setForeground(Color.WHITE);


        card.add(title);
        card.add(username);
        card.add(password);
        card.add(login);


        main.add(card);

        add(main);


        login.addActionListener(e -> authenticate());
    }



    void authenticate(){

        String user=username.getText();
        String pass=new String(password.getPassword());


        String sql=
        "SELECT user_id,username,role FROM users WHERE username=? AND password=?";


        try(Connection con=DBConnection.getConnection();
            PreparedStatement ps=con.prepareStatement(sql)){


            ps.setString(1,user);
            ps.setString(2,PasswordUtil.hashPassword(pass));


            ResultSet rs=ps.executeQuery();


            if(rs.next()){

                User u=new User(
                    rs.getInt("user_id"),
                    rs.getString("username"),
                    rs.getString("role")
                );


                new Dashboard(u).setVisible(true);
                dispose();

            }
            else{

                JOptionPane.showMessageDialog(
                    this,
                    "Invalid Login"
                );

            }


        }catch(Exception e){

            JOptionPane.showMessageDialog(
                this,
                e.getMessage()
            );

        }

    }
}