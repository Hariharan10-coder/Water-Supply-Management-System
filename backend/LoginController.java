import com.sun.net.httpserver.*;
import java.io.*;
import java.sql.*;

public class LoginController {


public static void main(String args[])
throws Exception{


HttpServer server=
HttpServer.create(
new java.net.InetSocketAddress(8080),0);



server.createContext("/login",exchange->{


String response="Invalid";


if(exchange.getRequestMethod()
.equals("POST")){


String body=
new String(
exchange.getRequestBody()
.readAllBytes()
);



String[] data=body.split("&");


String username=data[0].split("=")[1];

String password=data[1].split("=")[1];


try(Connection con=
DBConnection.getConnection()){


PreparedStatement ps=
con.prepareStatement(
"SELECT username,role FROM users WHERE username=? AND password=?"
);


ps.setString(1,username);

ps.setString(2,
PasswordUtil.hashPassword(password)
);



ResultSet rs=
ps.executeQuery();



if(rs.next()){

response=
"{\"username\":\""+
rs.getString("username")+
"\",\"role\":\""+
rs.getString("role")+
"\"}";

}


}



}



exchange.sendResponseHeaders(
200,response.length()
);


exchange.getResponseBody()
.write(response.getBytes());


exchange.close();


});


server.start();


System.out.println(
"Server running http://localhost:8080"
);


}

}
