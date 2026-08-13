import com.sun.net.httpserver.*;

import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.sql.*;



public class Server {


public static void main(String[] args)throws Exception{


HttpServer server =
HttpServer.create(
new InetSocketAddress(8080),
0);



server.createContext("/",exchange->{


sendFile(
exchange,
"index.html",
"text/html"
);


});




server.createContext("/dashboard.html",exchange->{


sendFile(
exchange,
"dashboard.html",
"text/html"
);


});




server.createContext("/style.css",exchange->{


sendFile(
exchange,
"style.css",
"text/css"
);


});





server.createContext("/login",exchange->{


BufferedReader br =
new BufferedReader(
new InputStreamReader(
exchange.getRequestBody()
)
);



String data =
br.readLine();



String username =
data.split("&")[0]
.split("=")[1];


String password =
data.split("&")[1]
.split("=")[1];



boolean result =
authenticate(
username,
password
);



String response;



if(result)

response =
"{\"status\":\"success\"}";


else

response =
"{\"status\":\"failed\"}";




exchange.getResponseHeaders()
.set(
"Content-Type",
"application/json"
);



exchange.sendResponseHeaders(
200,
response.length()
);



exchange.getResponseBody()
.write(
response.getBytes()
);



exchange.close();



});




server.start();



System.out.println(
"http://localhost:8080"
);


}





static void sendFile(
HttpExchange exchange,
String file,
String type)
throws IOException{


byte[] data =
Files.readAllBytes(
Paths.get(file)
);



exchange.getResponseHeaders()
.set(
"Content-Type",
type
);



exchange.sendResponseHeaders(
200,
data.length
);



exchange.getResponseBody()
.write(data);



exchange.close();


}





static boolean authenticate(
String username,
String password){


String sql=
"SELECT * FROM users WHERE username=? AND password=?";



try(
Connection con =
DBConnection.getConnection();


PreparedStatement ps =
con.prepareStatement(sql)

){


ps.setString(
1,
username
);



ps.setString(
2,
PasswordUtil.hashPassword(password)
);



ResultSet rs =
ps.executeQuery();



return rs.next();



}

catch(Exception e){

e.printStackTrace();

}


return false;


}


}